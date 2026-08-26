"""Authenticated FastAPI backend for TeXCleaner cleaning jobs."""

import asyncio
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket
from pydantic import BaseModel, Field

from version import __version__
from .job_store import JobCapacityError, JobStatus, JobStore
from .wrapper import (
    clean_arxiv,
    clean_changes,
    clean_trackchanges,
    detect_cleaning_module,
    generate_output_filename,
    is_valid_output_suffix,
)


_auth_token = os.environ.get("TEXCLEANER_AUTH_TOKEN") or secrets.token_urlsafe(32)


def configure_auth_token(token: str):
    """Configure the bearer token used by HTTP and WebSocket clients."""
    if not token:
        raise ValueError("The API authentication token cannot be empty")
    global _auth_token
    _auth_token = token


def _is_authorized(authorization: str | None) -> bool:
    expected = f"Bearer {_auth_token}"
    return authorization is not None and secrets.compare_digest(authorization, expected)


def require_auth(authorization: str | None = Header(default=None)):
    if not _is_authorized(authorization):
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")


app = FastAPI(title="TeXCleaner API", version=__version__)
job_store = JobStore()
job_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="texcleaner-job")


class TrackChangesRequest(BaseModel):
    input_path: str
    keep_version: Literal["new", "old"] = "new"
    remove_annotations: bool = True
    output_suffix: str = "-cleaned"
    overwrite: bool = False


class ArxivRequest(BaseModel):
    folder_path: str
    resize_images: bool = True
    image_size: int = Field(default=500, ge=1, le=10000)
    compress_pdf: bool = False
    pdf_resolution: int = Field(default=500, ge=1, le=2400)
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


def _validate_output_suffix(suffix: str):
    if not is_valid_output_suffix(suffix):
        raise HTTPException(
            status_code=422,
            detail="Output suffix must be non-empty and contain no separators or control characters",
        )


def _create_job():
    try:
        return job_store.create_job()
    except JobCapacityError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/", dependencies=[Depends(require_auth)])
def root():
    return {"name": "TeXCleaner API", "version": __version__}


@app.get("/detect", dependencies=[Depends(require_auth)])
def detect_module(input_path: str = Query(...)):
    path = Path(input_path).expanduser()
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Input file not found: {input_path}")
    detected = detect_cleaning_module(path)
    return {"input_path": str(path), "detected": detected}


@app.get("/jobs/{job_id}", dependencies=[Depends(require_auth)])
def get_job_detail(job_id: str):
    job = job_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    snapshot = job.snapshot()
    return JobDetail(
        job_id=snapshot["job_id"],
        status=snapshot["status"].value,
        logs=snapshot["logs"],
        result=snapshot["result"],
        output_path=snapshot["output_path"],
        created_at=snapshot["created_at"],
        finished_at=snapshot["finished_at"],
    )


def _run_job(job, target_func, *args, **kwargs):
    job.mark_running()
    job.append_log(f"Job {job.job_id} started.\n")

    def callback(message: str):
        job.append_log(message)

    try:
        success, message = target_func(callback=callback, *args, **kwargs)
        if success:
            job.append_log(f"SUCCESS: {message}\n")
            job.finish(JobStatus.SUCCESS, message)
        else:
            job.append_log(f"FAILED: {message}\n")
            job.finish(JobStatus.ERROR, message)
    except Exception as error:
        error_message = f"Unexpected error: {error}"
        job.append_log(f"ERROR: {error_message}\n")
        job.finish(JobStatus.ERROR, error_message)


@app.post("/clean/trackchanges", dependencies=[Depends(require_auth)])
def start_trackchanges(request: TrackChangesRequest):
    input_path = Path(request.input_path).expanduser()
    if not input_path.is_file():
        raise HTTPException(status_code=404, detail=f"Input file not found: {request.input_path}")
    _validate_output_suffix(request.output_suffix)

    output_path = generate_output_filename(input_path.resolve(), request.output_suffix)
    job = _create_job()
    job.set_output_path(output_path)
    job_executor.submit(
        _run_job,
        job,
        clean_trackchanges,
        str(input_path.resolve()),
        output_path,
        accept_changes=request.keep_version == "new",
        remove_annotations=request.remove_annotations,
        overwrite=request.overwrite,
    )
    return JobResponse(job_id=job.job_id, status=job.snapshot()["status"].value)


@app.post("/clean/changes", dependencies=[Depends(require_auth)])
def start_changes(request: TrackChangesRequest):
    input_path = Path(request.input_path).expanduser()
    if not input_path.is_file():
        raise HTTPException(status_code=404, detail=f"Input file not found: {request.input_path}")
    _validate_output_suffix(request.output_suffix)

    output_path = generate_output_filename(input_path.resolve(), request.output_suffix)
    job = _create_job()
    job.set_output_path(output_path)
    job_executor.submit(
        _run_job,
        job,
        clean_changes,
        str(input_path.resolve()),
        output_path,
        accept_changes=request.keep_version == "new",
        remove_annotations=request.remove_annotations,
        overwrite=request.overwrite,
    )
    return JobResponse(job_id=job.job_id, status=job.snapshot()["status"].value)


@app.post("/clean/arxiv", dependencies=[Depends(require_auth)])
def start_arxiv(request: ArxivRequest):
    folder_path = Path(request.folder_path).expanduser().resolve()
    if not folder_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")
    if folder_path.parent == folder_path or not folder_path.name:
        raise HTTPException(status_code=422, detail="The filesystem root is not a valid project folder")
    _validate_output_suffix(request.output_suffix)

    output_path = str(folder_path.with_name(folder_path.name + request.output_suffix))
    job = _create_job()
    job.set_output_path(output_path)
    job_executor.submit(
        _run_job,
        job,
        clean_arxiv,
        str(folder_path),
        resize_images=request.resize_images,
        im_size=request.image_size,
        compress_pdf=request.compress_pdf,
        pdf_resolution=request.pdf_resolution,
        keep_bib=request.keep_bib,
        verbose=request.verbose,
        output_suffix=request.output_suffix,
        overwrite=request.overwrite,
    )
    return JobResponse(job_id=job.job_id, status=job.snapshot()["status"].value)


@app.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    if not _is_authorized(websocket.headers.get("authorization")):
        await websocket.close(code=4401, reason="Unauthorized")
        return

    job = job_store.get_job(job_id)
    if job is None:
        await websocket.close(code=4404, reason="Job not found")
        return

    await websocket.accept()
    try:
        while True:
            snapshot = job.snapshot()
            message = {
                "logs_updated": len(snapshot["logs"]),
                "logs": snapshot["logs"],
            }
            if snapshot["status"] in (JobStatus.SUCCESS, JobStatus.ERROR):
                message.update(
                    status=snapshot["status"].value,
                    result=snapshot["result"],
                    output_path=snapshot["output_path"],
                )
                await websocket.send_json(message)
                break

            await websocket.send_json(message)
            await asyncio.sleep(0.2)
    except Exception:
        # Disconnects are expected and do not affect the underlying cleaning job.
        return


def run_server(
    port: int = 8765,
    host: str = "127.0.0.1",
    log_level: str = "info",
    auth_token: str | None = None,
):
    import uvicorn

    if auth_token:
        configure_auth_token(auth_token)
    elif "TEXCLEANER_AUTH_TOKEN" not in os.environ:
        print(f"TeXCleaner API bearer token: {_auth_token}", flush=True)

    uvicorn.run(app, host=host, port=port, log_level=log_level)
