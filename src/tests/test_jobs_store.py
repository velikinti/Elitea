from jobs.store import JobStore


def test_job_store_lifecycle():
    s = JobStore()
    rec = s.create("t", {"a": 1})

    assert rec.job_id
    assert s.get(rec.job_id) is not None

    s.set_running(rec.job_id)
    assert s.get(rec.job_id).status.value == "running"

    s.set_succeeded(rec.job_id, {"ok": True})
    rec2 = s.get(rec.job_id)
    assert rec2.status.value == "succeeded"
    assert rec2.result == {"ok": True}


def test_job_store_fail():
    s = JobStore()
    rec = s.create("t", {})
    s.set_failed(rec.job_id, "boom")
    assert s.get(rec.job_id).status.value == "failed"
    assert s.get(rec.job_id).error == "boom"
