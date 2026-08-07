from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    artifact_id: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    job_type: str
    result: Dict[str, Any] = Field(default_factory=dict)
    artifact_id: Optional[str] = None


class FrameworkAnalysisJobRequest(BaseModel):
    framework_path: str = Field(..., description="Path to the framework directory to analyze")


class GenerateTestScriptsJobRequest(BaseModel):
    framework_analyzer_path: str = Field(..., description="Path to framework analysis markdown file")
    test_cases_file_path: Optional[str] = Field(
        None,
        description="Optional: path to saved testcases JSON file. If not provided, 'test_cases' must be provided.",
    )
    test_cases: Optional[list] = Field(
        None,
        description="Optional: inline test cases (same shape as automation.GenerateScriptRequest.test_cases)",
    )
    review: Optional[str] = None
    file: Optional[str] = None


class IntegrateScriptJobRequest(BaseModel):
    test_file_name: str
    framework_test_dir: str
