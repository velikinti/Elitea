from __future__ import annotations

import logging
import threading
from fastapi import APIRouter, Body, HTTPException, status

from endpoints.automation.utility import analyze_framework, generate_test_scripts, integrate_script_to_framework
from jobs.artifacts import load_text_artifact, save_text_artifact
from jobs.models import JobStatus
from jobs.store import job_store, run_job

from .schemas import (
    ArtifactResponse,
    JobAcceptedResponse,
    JobResultResponse,
    JobStatusResponse,
    SubmitFrameworkAnalysisJobRequest,
    SubmitGenerateTestScriptsJobRequest,
    SubmitIntegrateScriptJobRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs")


def _spawn(job_id: str, job_type: str, fn):
    t = threading.Thread(target=run_job, args=(job_id, job_type, fn), daemon=True)
    t.start()


@router.post(
    "/framework-analysis",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit framework analysis as an async job",
)
async def submit_framework_analysis_job(
    request: SubmitFrameworkAnalysisJobRequest = Body(...),
) -> JobAcceptedResponse:
    rec = job_store.create(job_type="framework-analysis", request=request.model_dump())

    def fn():
        _analysis, path = analyze_framework(framework_path=request.framework_path)
        return {"framework_results_path": path}

    _spawn(rec.job_id, rec.job_type, fn)
    return JobAcceptedResponse(job_id=rec.job_id, status=rec.status.value)


@router.post(
    "/generate-test-scripts",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit test script generation as an async job",
)
async def submit_generate_test_scripts_job(
    request: SubmitGenerateTestScriptsJobRequest = Body(...),
) -> JobAcceptedResponse:
    rec = job_store.create(job_type="generate-test-scripts", request=request.model_dump())

    def fn():
        scripts_raw, output_dir = generate_test_scripts(
            test_cases=request.test_cases,
            framework_markdown_path=request.framework_analyzer_path,
            review=request.review,
            file_path=request.file,
        )
        return {"output_dir": output_dir, "scripts": scripts_raw}

    _spawn(rec.job_id, rec.job_type, fn)
    return JobAcceptedResponse(job_id=rec.job_id, status=rec.status.value)


@router.post(
    "/integrate-script-to-framework",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit framework integration + pytest run as an async job",
)
async def submit_integrate_script_job(
    request: SubmitIntegrateScriptJobRequest = Body(...),
) -> JobAcceptedResponse:
    rec = job_store.create(job_type="integrate-script-to-framework", request=request.model_dump())

    def fn():
        result = integrate_script_to_framework(
            test_file_name=request.test_file_name,
            framework_test_dir=request.framework_test_dir,
        )

        # Persist large output as artifact; return reference only
        output = result.get("test_execution_output")
        artifact_id = save_text_artifact(prefix="pytest_output", content=output or "")
        result.pop("test_execution_output", None)
        result["artifact_id"] = artifact_id
        return result

    _spawn(rec.job_id, rec.job_type, fn)
    return JobAcceptedResponse(job_id=rec.job_id, status=rec.status.value)


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    rec = job_store.get(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

    return JobStatusResponse(
        job_id=rec.job_id,
        job_type=rec.job_type,
        status=rec.status.value,
        created_at=rec.created_at,
        started_at=rec.started_at,
        finished_at=rec.finished_at,
        error=rec.error,
    )


@router.get(
    "/{job_id}/result",
    response_model=JobResultResponse,
    summary="Get job result (only if succeeded)",
)
async def get_job_result(job_id: str) -> JobResultResponse:
    rec = job_store.get(job_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")

    if rec.status in (JobStatus.queued, JobStatus.running):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="job not completed")

    if rec.status == JobStatus.failed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=rec.error or "job failed")

    return JobResultResponse(job_id=rec.job_id, job_type=rec.job_type, status=rec.status.value, result=rec.result or {})


@router.get(
    "/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Retrieve stored artifact text",
)
async def get_artifact(artifact_id: str) -> ArtifactResponse:
    content = load_text_artifact(artifact_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="artifact not found")
    return ArtifactResponse(artifact_id=artifact_id, content=content)
