from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, status

from endpoints.automation.utility import analyze_framework, generate_test_scripts, integrate_script_to_framework
from jobs.artifacts import read_text_artifact, save_text_artifact
from jobs.models import JobStatus
from jobs.store import job_store

from .schemas import (
    FrameworkAnalysisJobRequest,
    GenerateTestScriptsJobRequest,
    IntegrateScriptJobRequest,
    JobCreateResponse,
    JobResultResponse,
    JobStatusResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs")


def _job_not_found(job_id: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job not found: {job_id}")


def _run_in_thread(job_id: str, job_type: str, target) -> None:
    def _runner() -> None:
        try:
            job_store.mark_running(job_id)
            result, artifact_id = target()
            job_store.mark_succeeded(job_id, result=result, artifact_id=artifact_id)
        except Exception as e:
            logger.exception("Job %s (%s) failed", job_id, job_type)
            job_store.mark_failed(job_id, error_message=str(e))

    t = threading.Thread(target=_runner, name=f"job-{job_type}-{job_id}", daemon=True)
    t.start()


@router.post(
    "/framework-analysis",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit async framework analysis job",
)
async def submit_framework_analysis_job(request: FrameworkAnalysisJobRequest = Body(...)) -> JobCreateResponse:
    record = job_store.create(job_type="framework-analysis")

    def _target() -> tuple[Dict[str, Any], Optional[str]]:
        _, framework_results_path = analyze_framework(framework_path=request.framework_path)
        return {"framework_results_path": framework_results_path}, None

    _run_in_thread(record.job_id, record.job_type, _target)
    return JobCreateResponse(job_id=record.job_id, status=record.status.value)


@router.post(
    "/generate-test-scripts",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit async test script generation job",
)
async def submit_generate_test_scripts_job(request: GenerateTestScriptsJobRequest = Body(...)) -> JobCreateResponse:
    # Validate review/file coupling, match existing sync endpoint behaviour
    if request.review is not None and not request.file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If 'review' is provided, 'file' field is required to specify which file to modify.",
        )

    record = job_store.create(job_type="generate-test-scripts")

    def _load_test_cases() -> List[Dict[str, Any]]:
        if request.test_cases is not None:
            return request.test_cases
        if request.test_cases_file_path:
            p = request.test_cases_file_path
            if not os.path.isabs(p):
                p = os.path.join(os.getcwd(), p)
            if not os.path.exists(p):
                raise ValueError(f"test_cases_file_path not found: {p}")
            with open(p, "r", encoding="utf-8") as f:
                payload = json.load(f)
            if not isinstance(payload, dict) or "test_cases" not in payload:
                raise ValueError("Invalid test cases file format: expected key 'test_cases'")
            return payload["test_cases"]
        raise ValueError("Either 'test_cases' or 'test_cases_file_path' must be provided")

    def _target() -> tuple[Dict[str, Any], Optional[str]]:
        test_cases = _load_test_cases()
        scripts_raw, output_dir = generate_test_scripts(
            test_cases=test_cases,
            framework_markdown_path=request.framework_analyzer_path,
            review=request.review,
            file_path=request.file,
        )
        return {"output_dir": output_dir, "scripts": scripts_raw}, None

    _run_in_thread(record.job_id, record.job_type, _target)
    return JobCreateResponse(job_id=record.job_id, status=record.status.value)


@router.post(
    "/integrate-script-to-framework",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit async integrate-and-run job (pytest executed)",
)
async def submit_integrate_script_job(request: IntegrateScriptJobRequest = Body(...)) -> JobCreateResponse:
    record = job_store.create(job_type="integrate-script-to-framework")

    def _target() -> tuple[Dict[str, Any], Optional[str]]:
        result = integrate_script_to_framework(
            test_file_name=request.test_file_name,
            framework_test_dir=request.framework_test_dir,
        )
        # Persist potentially large stdout/stderr as artifact, return reference.
        output = result.get("test_execution_output")
        artifact_id = None
        if isinstance(output, str) and output.strip():
            artifact_id = save_text_artifact(output, filename_hint="pytest_output")
            # Avoid duplicating large output in job result.
            result = {**result, "test_execution_output": None}
        return result, artifact_id

    _run_in_thread(record.job_id, record.job_type, _target)
    return JobCreateResponse(job_id=record.job_id, status=record.status.value)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    record = job_store.get(job_id)
    if record is None:
        raise _job_not_found(job_id)

    return JobStatusResponse(
        job_id=record.job_id,
        job_type=record.job_type,
        status=record.status.value,
        created_at=record.created_at,
        updated_at=record.updated_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        error_message=record.error_message,
        artifact_id=record.artifact_id,
    )


@router.get(
    "/{job_id}/result",
    response_model=JobResultResponse,
    summary="Get job result (only when completed)",
)
async def get_job_result(job_id: str) -> JobResultResponse:
    record = job_store.get(job_id)
    if record is None:
        raise _job_not_found(job_id)

    if record.status in (JobStatus.queued, JobStatus.running):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job not completed. Current status: {record.status.value}",
        )

    if record.status == JobStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=record.error_message or "Job failed",
        )

    return JobResultResponse(
        job_id=record.job_id,
        job_type=record.job_type,
        result=record.result or {},
        artifact_id=record.artifact_id,
    )


@router.get(
    "/artifacts/{artifact_id}",
    summary="Retrieve stored artifact content",
)
async def get_artifact(artifact_id: str) -> Dict[str, Any]:
    try:
        content = read_text_artifact(artifact_id)
        return {"artifact_id": artifact_id, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
