from jobs.store import JobStore


def test_job_lifecycle_success():
    store = JobStore()
    job = store.create_job(job_type="x")
    assert job.status.value == "queued"

    store.set_running(job.job_id)
    assert store.get(job.job_id).status.value == "running"

    store.set_succeeded(job.job_id, {"ok": True})
    rec = store.get(job.job_id)
    assert rec.status.value == "succeeded"
    assert rec.result == {"ok": True}


def test_job_lifecycle_failed():
    store = JobStore()
    job = store.create_job(job_type="x")
    store.set_running(job.job_id)
    store.set_failed(job.job_id, "boom")
    rec = store.get(job.job_id)
    assert rec.status.value == "failed"
    assert rec.error_message == "boom"
