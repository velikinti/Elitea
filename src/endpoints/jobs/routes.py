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


def _coerce_test_cases_for_automation_utility(test_cases: list) -> str:
    """
    Best-effort conversion of structured test cases into the string format expected by the
    automation utility. This mirrors the conversion logic in endpoints.automation.routes.
    """
    # Keep it compact and stable for downstream processing.
    lines: list[str] = []
    for i, tc in enumerate(test_cases or [], start=1):
        if isinstance(tc, str):
            lines.append(f"{i}. {tc}")
            continue

        if isinstance(tc, dict):
            title = tc.get("title") or tc.get("name") or tc.get("id") or f"Test Case {i}"
            desc = tc.get("description") or tc.get("summary") or ""
            steps = tc.get("steps") or tc.get("step") or []
            expected = tc.get("expected") or tc.get("expected_result") or ""

            lines.append(f"{i}. {title}".strip())
            if desc:
                lines.append(f"   Description: {desc}".strip())
            if steps:
                if isinstance(steps, str):
                    steps = [steps]
                if isinstance(steps, list):
                    lines.append("   Steps:")
                    for s_i, step in enumerate(steps, start=1):
                        lines.append(f"     {s_i}. {step}")
            if expected:
                lines.append(f"   Expected: {expected}".strip())
            continue

        # Fallback for unknown types
        lines.append(f"{i}. {str(tc)}")

    return "\n".join(lines).strip()


@router.post("/framework-analysis", response_model=JobSubmittedResponse, status_code=202)
def submit_framework_analysis_job(payload: SubmitFrameworkAnalysisJobRequest, bg: BackgroundTasks):
    job = job_store.create_job(job_type="framework-analysis")

    def _fn():
        framework_analysis_obj, framework_results_path = analyze_framework(payload.framework_path)

        # Persist the markdown content if possible; otherwise persist the results path.
        artifact_content = str(framework_results_path)
        try:
            with open(framework_results_path, "r", encoding="utf-8") as f:
                artifact_content = f.read()
        except OSError:
            pass

        artifact_id = save_text_artifact(content=artifact_content)
        return {
            "artifact_id": artifact_id,
            "framework_path": payload.framework_path,
            "framework_results_path": str(framework_results_path),
        }

    bg.add_task(run_job, job_id=job.job_id, fn=_fn)
    return JobSubmittedResponse(job_id=job.job_id, status=job.status)


@router.post("/generate-test-scripts", response_model=JobSubmittedResponse, status_code=202)
def submit_generate_test_scripts_job(payload: SubmitGenerateTestScriptsJobRequest, bg: BackgroundTasks):
    job = job_store.create_job(job_type="generate-test-scripts")

    def _fn():
        test_cases_text = _coerce_test_cases_for_automation_utility(payload.test_cases)
        result = generate_test_scripts(
            test_cases=test_cases_text,
            framework_markdown_path=payload.framework_analyzer_path,
            review=payload.review,
            file_path=payload.file,
        )

        # Persist generated content/path as an artifact; avoid returning huge inline content.
        artifact_id = save_text_artifact(content=str(result))
        return {
            "artifact_id": artifact_id,
            "generated_test_scripts_path": str(result) if isinstance(result, (str, bytes)) else None,
        }

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
            test_file_name=payload.test_file_name,
            framework_test_dir=payload.framework_test_dir,
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


@router.get("/artifacts/{artifact_id}")
def get_artifact_text(artifact_id: str):
    try:
        return {"artifact_id": artifact_id, "content": load_text_artifact(artifact_id=artifact_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
