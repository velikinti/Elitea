from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from jobs.models import JobStatus


class SubmitFrameworkAnalysisJobRequest(BaseModel):
    framework_path: str = Field(..., description="Path to the external test framework root")


class SubmitGenerateTestScriptsJobRequest(BaseModel):
    test_cases: list[dict | str] = Field(
        ...,
        description="List of test cases as dicts or strings to generate test scripts from",
    )
    framework_analyzer_path: str = Field(
        ...,
        description="Path to the framework analyzer output/directory",
    )
    review: str | None = Field(
        None,
        description="Optional review/instructions for generation",
    )
    file: str | None = Field(
        None,
        description="Optional file identifier/path associated with the request",
    )


class SubmitIntegrateScriptToFrameworkJobRequest(BaseModel):
    test_file_name: str
    framework_test_dir: str


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
