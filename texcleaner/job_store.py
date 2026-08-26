"""
job_store.py - Thread-safe in-memory job registry for the API server.

Tracks the status, logs, and results of each cleaning job so the SwiftUI
frontend can poll for progress or subscribe via WebSocket.
"""

import uuid
import threading
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class Job:
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: JobStatus = JobStatus.PENDING
    logs: List[str] = field(default_factory=list)
    result: Optional[str] = None
    output_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    created_timestamp: float = field(default_factory=time.time, repr=False)
    finished_timestamp: Optional[float] = field(default=None, repr=False)

    def append_log(self, message: str):
        with self.lock:
            self.logs.append(message)

    def append_logs(self, messages: List[str]):
        with self.lock:
            self.logs.extend(messages)

    def mark_running(self):
        with self.lock:
            self.status = JobStatus.RUNNING

    def set_output_path(self, output_path: str):
        with self.lock:
            self.output_path = output_path

    def finish(self, status: JobStatus, result: str):
        now = datetime.now(timezone.utc)
        with self.lock:
            self.status = status
            self.result = result
            self.finished_at = now.isoformat()
            self.finished_timestamp = now.timestamp()

    def snapshot(self):
        with self.lock:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "logs": list(self.logs),
                "result": self.result,
                "output_path": self.output_path,
                "created_at": self.created_at,
                "finished_at": self.finished_at,
            }


class JobCapacityError(RuntimeError):
    pass


class JobStore:
    """Thread-safe registry for active and completed jobs."""

    def __init__(self, max_jobs=200, max_active_jobs=32, retention_seconds=3600):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs
        self._max_active_jobs = max_active_jobs
        self._retention_seconds = retention_seconds

    def _purge_locked(self):
        now = time.time()
        completed = [
            job
            for job in self._jobs.values()
            if job.status in (JobStatus.SUCCESS, JobStatus.ERROR)
        ]
        for job in completed:
            if (
                job.finished_timestamp is not None
                and now - job.finished_timestamp > self._retention_seconds
            ):
                self._jobs.pop(job.job_id, None)

        completed = sorted(
            (
                job
                for job in self._jobs.values()
                if job.status in (JobStatus.SUCCESS, JobStatus.ERROR)
            ),
            key=lambda job: job.finished_timestamp or job.created_timestamp,
        )
        excess = max(0, len(self._jobs) - self._max_jobs)
        for job in completed[:excess]:
            self._jobs.pop(job.job_id, None)

    def create_job(self) -> Job:
        with self._lock:
            self._purge_locked()
            active_count = sum(
                job.status in (JobStatus.PENDING, JobStatus.RUNNING)
                for job in self._jobs.values()
            )
            if active_count >= self._max_active_jobs:
                raise JobCapacityError("Too many cleaning jobs are already active")
            job = Job()
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            self._purge_locked()
            return self._jobs.get(job_id)

    def get_jobs(self):
        with self._lock:
            self._purge_locked()
            return list(self._jobs.values())

    def clear(self):
        with self._lock:
            self._jobs.clear()
