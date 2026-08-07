from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SubmitFrameworkAnalysisJobRequest(BaseModel):
    framework_path: str = Field(..., description="Path to test framework root")


class SubmitGenerateTestScriptsJobRequest(BaseModel):
    test_cases: list[dict[str, Any]] = Field(..., description="List of test cases")
    framework_analyzer_path: str = Field(..., description="Path to framework analysis markdown")
    review: Optional[str] = None
    file: Optional[str] = None


class SubmitIntegrateScriptJobRequest(BaseModel):
    test_file_name: str
    framework_test_dir: str


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    result: Dict[str, Any]


class ArtifactResponse(BaseModel):
    artifact_id: str
    content: str
