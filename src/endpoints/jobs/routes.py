from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from endpoints.automation.utility import (
    analyze_framework,
    generate_test_scripts,
    integrate_script_to_framework,
)
from jobs.artifacts import load_text_artifact, save_text_artifact
from jobs.models import JobStatus
from jobs.store import job_store, run_job

from .schemas import (
    JobResultResponse,
    JobStatusResponse,
    JobSubmittedResponse,
    SubmitFrameworkAnalysisJobRequest,
    SubmitGenerateTestScriptsJobRequest,
    SubmitIntegrateScriptToFrameworkJobRequest,
)


router = APIRouter(prefix="/jobs")


@router.post("/framework-analysis", response_model=JobSubmittedResponse, status_code=202)
def submit_framework_analysis_job(payload: SubmitFrameworkAnalysisJobRequest, bg: BackgroundTasks):
    job = job_store.create_job(job_type="framework-analysis")

    def _fn():
        result = analyze_framework(payload.framework_path)
        artifact_id = save_text_artifact(content=str(result))
        return {"artifact_id": artifact_id, "framework_path": payload.framework_path}

    bg.add_task(run_job, job_id=job.job_id, fn=_fn)
    return JobSubmittedResponse(job_id=job.job_id, status=job.status)


@router.post("/generate-test-scripts", response_model=JobSubmittedResponse, status_code=202)
def submit_generate_test_scripts_job(payload: SubmitGenerateTestScriptsJobRequest, bg: BackgroundTasks):
    job = job_store.create_job(job_type="generate-test-scripts")

    def _fn():
        result = generate_test_scripts(payload.api_spec)
        artifact_id = save_text_artifact(content=str(result))
        return {"artifact_id": artifact_id}

    bg.add_task(run_job, job_id=job.job_id, fn=_fn)
    return JobSubmittedResponse(job_id=job.job_id, status=job.status)


@router.post("/integrate-script-to-framework", response_model=JobSubmittedResponse, status_code=202)
def submit_integrate_script_to_framework_job(
    payload: SubmitIntegrateScriptToFrameworkJobRequest,
    bg: BackgroundTasks,
):
    job = job_store.create_job(job_type="integrate-script-to-framework")

    def _fn():
        result = integrate_script_to_framework(
            framework_path=payload.framework_path,
            test_script_path=payload.test_script_path,
        )
        # Always persist output as artifact for traceability.
        output_text = str(result.get("test_execution_output", ""))
        artifact_id = save_text_artifact(content=output_text)
        # Return the rest of the integration metadata.
        result.pop("test_execution_output", None)
        result["artifact_id"] = artifact_id
        return result

    bg.add_task(run_job, job_id=job.job_id, fn=_fn)
    return JobSubmittedResponse(job_id=job.job_id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
    )


@router.get("/{job_id}/result", response_model=JobResultResponse)
def get_job_result(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in (JobStatus.queued, JobStatus.running):
        raise HTTPException(status_code=409, detail="Job is not completed")

    if job.status == JobStatus.failed:
        raise HTTPException(status_code=500, detail=job.error_message or "Job failed")

    return JobResultResponse(job_id=job.job_id, status=job.status, result=job.result or {})


@router.get("/artifacts/{artifact_id}")
def get_artifact_text(artifact_id: str):
    try:
        return {"artifact_id": artifact_id, "content": load_text_artifact(artifact_id=artifact_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
