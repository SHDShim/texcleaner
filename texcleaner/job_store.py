"""
job_store.py - Thread-safe in-memory job registry for the API server.

Tracks the status, logs, and results of each cleaning job so the SwiftUI
frontend can poll for progress or subscribe via WebSocket.
"""

import uuid
import threading
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

    def append_log(self, message: str):
        with self.lock:
            self.logs.append(message)

    def append_logs(self, messages: List[str]):
        with self.lock:
            self.logs.extend(messages)


class JobStore:
    """Thread-safe registry for active and completed jobs."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self) -> Job:
        job = Job()
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def get_jobs(self):
        with self._lock:
            return list(self._jobs.values())
