"""
server.py - FastAPI server backend for TeXCleaner.

Exposes REST endpoints for cleaning operations and WebSocket for real-time
log streaming. The SwiftUI frontend communicates with this server.
"""

import asyncio
import threading
import os
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from version import __version__
from .job_store import Job, JobStore, JobStatus
from .wrapper import (
    clean_trackchanges,
    clean_changes,
    clean_arxiv,
    detect_cleaning_module,
    generate_output_filename,
)

app = FastAPI(
    title="TeXCleaner API",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

job_store = JobStore()

active_subscribers: dict[str, list[WebSocket]] = {}


class TrackChangesRequest(BaseModel):
    input_path: str
    keep_version: str = "new"
    remove_annotations: bool = True
    output_suffix: str = "-cleaned"
    overwrite: bool = False


class ArxivRequest(BaseModel):
    folder_path: str
    resize_images: bool = True
    image_size: int = 500
    compress_pdf: bool = False
    pdf_resolution: int = 500
    keep_bib: bool = False
    verbose: bool = False
    output_suffix: str = "-cleaned"
    overwrite: bool = False


class JobResponse(BaseModel):
    job_id: str
    status: str


class JobDetail(BaseModel):
    job_id: str
    status: str
    logs: list[str]
    result: str | None = None
    output_path: str | None = None
    created_at: str | None = None
    finished_at: str | None = None


@app.get("/")
def root():
    return {"name": "TeXCleaner API", "version": __version__}


@app.get("/detect")
def detect_module(input_path: str = Query(...)):
    detected = detect_cleaning_module(input_path)
    return {"input_path": input_path, "detected": detected}


@app.get("/jobs/{job_id}")
def get_job_detail(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobDetail(
        job_id=job.job_id,
        status=job.status.value,
        logs=job.logs,
        result=job.result,
        output_path=job.output_path,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


def _run_job(job, target_func, *args, **kwargs):
    job.status = JobStatus.RUNNING
    job.append_log(f"Job {job.job_id} started.\n")

    def callback(message: str):
        job.append_log(message)

    try:
        success, message = target_func(callback=callback, *args, **kwargs)
        job.finished_at = datetime.now(timezone.utc).isoformat()

        if success:
            job.status = JobStatus.SUCCESS
            job.result = message
            job.append_log(f"SUCCESS: {message}\n")
        else:
            job.status = JobStatus.ERROR
            job.result = message
            job.append_log(f"FAILED: {message}\n")

    except Exception as e:
        job.finished_at = datetime.now(timezone.utc).isoformat()
        job.status = JobStatus.ERROR
        error_msg = f"Unexpected error: {e}"
        job.result = error_msg
        job.append_log(f"ERROR: {error_msg}\n")


@app.post("/clean/trackchanges")
def start_trackchanges(request: TrackChangesRequest):
    job = job_store.create_job()
    input_path = request.input_path

    if not os.path.isfile(input_path):
        job.status = JobStatus.ERROR
        job.result = f"Input file not found: {input_path}"
        job.append_log(job.result + "\n")
        return JobResponse(job_id=job.job_id, status=job.status.value)

    if request.keep_version not in {"new", "old"}:
        raise HTTPException(status_code=422, detail="keep_version must be 'new' or 'old'")
    if not _valid_output_suffix(request.output_suffix):
        raise HTTPException(status_code=422, detail="Invalid output suffix")

    output_path = generate_output_filename(input_path, request.output_suffix)
    job.output_path = output_path

    thread = threading.Thread(
        target=_run_job,
        args=(job, clean_trackchanges, input_path, output_path),
        kwargs={
            "accept_changes": request.keep_version == "new",
            "remove_annotations": request.remove_annotations,
            "overwrite": request.overwrite,
        },
        daemon=True,
    )
    thread.start()
    return JobResponse(job_id=job.job_id, status=job.status.value)


@app.post("/clean/changes")
def start_changes(request: TrackChangesRequest):
    job = job_store.create_job()
    input_path = request.input_path

    if not os.path.isfile(input_path):
        job.status = JobStatus.ERROR
        job.result = f"Input file not found: {input_path}"
        job.append_log(job.result + "\n")
        return JobResponse(job_id=job.job_id, status=job.status.value)

    if request.keep_version not in {"new", "old"}:
        raise HTTPException(status_code=422, detail="keep_version must be 'new' or 'old'")
    if not _valid_output_suffix(request.output_suffix):
        raise HTTPException(status_code=422, detail="Invalid output suffix")

    output_path = generate_output_filename(input_path, request.output_suffix)
    job.output_path = output_path

    thread = threading.Thread(
        target=_run_job,
        args=(job, clean_changes, input_path, output_path),
        kwargs={
            "accept_changes": request.keep_version == "new",
            "remove_annotations": request.remove_annotations,
            "overwrite": request.overwrite,
        },
        daemon=True,
    )
    thread.start()
    return JobResponse(job_id=job.job_id, status=job.status.value)


@app.post("/clean/arxiv")
def start_arxiv(request: ArxivRequest):
    job = job_store.create_job()
    folder_path = request.folder_path

    if not os.path.isdir(folder_path):
        job.status = JobStatus.ERROR
        job.result = f"Folder not found: {folder_path}"
        job.append_log(job.result + "\n")
        return JobResponse(job_id=job.job_id, status=job.status.value)

    if not 1 <= request.image_size <= 10000:
        raise HTTPException(status_code=422, detail="image_size must be between 1 and 10000")
    if not 1 <= request.pdf_resolution <= 2400:
        raise HTTPException(status_code=422, detail="pdf_resolution must be between 1 and 2400")
    if not _valid_output_suffix(request.output_suffix):
        raise HTTPException(status_code=422, detail="Invalid output suffix")

    normalized_folder_path = os.path.normpath(folder_path)
    job.output_path = os.path.join(
        os.path.dirname(normalized_folder_path),
        os.path.basename(normalized_folder_path) + request.output_suffix,
    )

    thread = threading.Thread(
        target=_run_job,
        args=(job, clean_arxiv, folder_path),
        kwargs={
            "resize_images": request.resize_images,
            "im_size": request.image_size,
            "compress_pdf": request.compress_pdf,
            "pdf_resolution": request.pdf_resolution,
            "keep_bib": request.keep_bib,
            "verbose": request.verbose,
            "output_suffix": request.output_suffix,
            "overwrite": request.overwrite,
        },
        daemon=True,
    )
    thread.start()
    return JobResponse(job_id=job.job_id, status=job.status.value)


@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    await websocket.accept()
    if job_id not in active_subscribers:
        active_subscribers[job_id] = []
    active_subscribers[job_id].append(websocket)

    try:
        while True:
            await asyncio.sleep(0.2)
            job = job_store.get_job(job_id)
            if job is None:
                continue

            msg = {"logs_updated": len(job.logs)}

            if job.status in (JobStatus.SUCCESS, JobStatus.ERROR):
                msg["status"] = job.status.value
                msg["result"] = job.result
                msg["output_path"] = job.output_path
                msg["logs"] = job.logs
                await websocket.send_json(msg)
                break

            await websocket.send_json(msg)

    except Exception:
        pass
    finally:
        if websocket in active_subscribers.get(job_id, []):
            active_subscribers[job_id].remove(websocket)


def run_server(
    port: int = 8765,
    host: str = "127.0.0.1",
    log_level: str = "info",
):
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
    )


def _valid_output_suffix(suffix: str) -> bool:
    return bool(suffix) and "/" not in suffix and "\\" not in suffix and "\0" not in suffix
