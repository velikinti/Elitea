from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass
class JobRecord:
    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[dict[str, Any]] = None
