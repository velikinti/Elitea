import os

from jobs.artifacts import load_text_artifact, save_text_artifact


def test_artifact_save_and_load(tmp_path, monkeypatch):
    # Make artifacts write into a temp cwd/outputfolder
    monkeypatch.chdir(tmp_path)

    # settings.base_output_folder is 'outputfolder' by default; create implicitly
    artifact_id = save_text_artifact(prefix="pytest_output", content="hello")
    assert artifact_id.endswith(".txt")

    content = load_text_artifact(artifact_id)
    assert content == "hello"


def test_artifact_rejects_bad_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_text_artifact("../etc/passwd") is None
    assert load_text_artifact("not-a-uuid.txt") is None
