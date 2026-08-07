from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from .models import JobRecord, JobStatus


class JobStore:
    """Thread-safe in-memory job store.

    NOTE: In-memory means job visibility is per-process.
    If you run multiple gunicorn workers, clients may hit a different worker
    and not see the job they created.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: Dict[str, JobRecord] = {}

    def create(self, job_type: str, request: Dict[str, Any]) -> JobRecord:
        with self._lock:
            job_id = uuid.uuid4().hex
            rec = JobRecord(job_id=job_id, job_type=job_type, status=JobStatus.queued, request=request)
            self._jobs[job_id] = rec
            return rec

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def set_running(self, job_id: str) -> None:
        with self._lock:
            rec = self._require(job_id)
            rec.status = JobStatus.running
            rec.started_at = datetime.now(timezone.utc)

    def set_succeeded(self, job_id: str, result: Dict[str, Any]) -> None:
        with self._lock:
            rec = self._require(job_id)
            rec.status = JobStatus.succeeded
            rec.result = result
            rec.finished_at = datetime.now(timezone.utc)

    def set_failed(self, job_id: str, error: str) -> None:
        with self._lock:
            rec = self._require(job_id)
            rec.status = JobStatus.failed
            rec.error = error
            rec.finished_at = datetime.now(timezone.utc)

    def _require(self, job_id: str) -> JobRecord:
        rec = self._jobs.get(job_id)
        if rec is None:
            raise KeyError(job_id)
        return rec


job_store = JobStore()


def run_job(job_id: str, job_type: str, func: Callable[[], Dict[str, Any]]) -> None:
    """Helper to execute a job function and record success/failure."""
    job_store.set_running(job_id)
    try:
        result = func()
        job_store.set_succeeded(job_id, result=result)
    except Exception as e:  # noqa: BLE001
        job_store.set_failed(job_id, error=str(e))
