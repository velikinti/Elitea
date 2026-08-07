from jobs.store import JobStore
from jobs.models import JobStatus


def test_job_store_lifecycle_success():
    s = JobStore()
    rec = s.create("framework-analysis")
    assert rec.status == JobStatus.queued

    s.mark_running(rec.job_id)
    assert s.get(rec.job_id).status == JobStatus.running

    s.mark_succeeded(rec.job_id, result={"x": 1}, artifact_id="a.txt")
    final = s.get(rec.job_id)
    assert final.status == JobStatus.succeeded
    assert final.result == {"x": 1}
    assert final.artifact_id == "a.txt"


def test_job_store_failure():
    s = JobStore()
    rec = s.create("integrate")
    s.mark_running(rec.job_id)
    s.mark_failed(rec.job_id, "boom")
    final = s.get(rec.job_id)
    assert final.status == JobStatus.failed
    assert final.error_message == "boom"
