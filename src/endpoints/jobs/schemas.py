from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from jobs.models import JobStatus


class SubmitFrameworkAnalysisJobRequest(BaseModel):
    framework_path: str = Field(..., description="Path to the external test framework root")


class SubmitGenerateTestScriptsJobRequest(BaseModel):
    api_spec: str = Field(..., description="Swagger/OpenAPI content or curl to parse")
    framework_path: str | None = Field(None, description="Optional framework path")


class SubmitIntegrateScriptToFrameworkJobRequest(BaseModel):
    framework_path: str
    test_script_path: str


class JobSubmittedResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: dict[str, Any]
