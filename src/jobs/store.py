from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Any, Callable

from jobs.models import JobRecord, JobStatus


class JobStore:
    """In-memory job store.

    Note: this is per-process. If the app runs with multiple workers, polling will
    only see jobs created in the same worker process.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}

    def create_job(self, *, job_type: str) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.queued,
            created_at=datetime.utcnow(),
        )
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def set_running(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.running
            job.started_at = datetime.utcnow()

    def set_succeeded(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.succeeded
            job.result = result
            job.finished_at = datetime.utcnow()
            job.error_message = None

    def set_failed(self, job_id: str, error_message: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.failed
            job.error_message = error_message
            job.finished_at = datetime.utcnow()


job_store = JobStore()


def run_job(*, job_id: str, fn: Callable[[], dict[str, Any]]) -> None:
    """Run a job function and update state.

    This helper is intended to be invoked inside a FastAPI BackgroundTask.
    """

    job_store.set_running(job_id)
    try:
        result = fn()
        job_store.set_succeeded(job_id, result)
    except Exception as exc:  # noqa: BLE001
        job_store.set_failed(job_id, str(exc))
