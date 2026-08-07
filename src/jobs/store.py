from __future__ import annotations

import threading
from dataclasses import replace
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from .models import JobRecord, JobStatus


class JobStore:
    """Thread-safe in-memory job store.

    Notes:
    - Gunicorn with multiple workers will have per-process stores.
      This is intentional per FRD (no external DB/Redis), and callers should use
      a single worker for consistent job polling.
    - Results/artifacts should be persisted to filesystem separately.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: Dict[str, JobRecord] = {}

    def create(self, job_type: str) -> JobRecord:
        now = datetime.utcnow()
        job_id = uuid4().hex
        record = JobRecord(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.queued,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, updater: Callable[[JobRecord], JobRecord]) -> JobRecord:
        with self._lock:
            current = self._jobs.get(job_id)
            if current is None:
                raise KeyError(job_id)
            updated = updater(current)
            self._jobs[job_id] = updated
            return updated

    def mark_running(self, job_id: str) -> JobRecord:
        now = datetime.utcnow()

        def _upd(j: JobRecord) -> JobRecord:
            return replace(
                j,
                status=JobStatus.running,
                updated_at=now,
                started_at=j.started_at or now,
            )

        return self.update(job_id, _upd)

    def mark_succeeded(self, job_id: str, result: Dict[str, Any], artifact_id: Optional[str] = None) -> JobRecord:
        now = datetime.utcnow()

        def _upd(j: JobRecord) -> JobRecord:
            return replace(
                j,
                status=JobStatus.succeeded,
                updated_at=now,
                finished_at=now,
                result=result,
                artifact_id=artifact_id,
                error_message=None,
            )

        return self.update(job_id, _upd)

    def mark_failed(self, job_id: str, error_message: str) -> JobRecord:
        now = datetime.utcnow()

        def _upd(j: JobRecord) -> JobRecord:
            return replace(
                j,
                status=JobStatus.failed,
                updated_at=now,
                finished_at=now,
                error_message=error_message,
            )

        return self.update(job_id, _upd)


job_store = JobStore()
