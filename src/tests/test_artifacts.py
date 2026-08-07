import os

from jobs.artifacts import save_text_artifact, read_text_artifact, get_artifact_path


def test_save_and_read_text_artifact(tmp_path, monkeypatch):
    # Force cwd to tmp so we don't touch real outputfolder
    monkeypatch.chdir(tmp_path)

    artifact_id = save_text_artifact("hello", filename_hint="pytest_output")
    assert artifact_id.endswith(".txt")

    p = get_artifact_path(artifact_id)
    assert os.path.exists(p)

    assert read_text_artifact(artifact_id) == "hello"
