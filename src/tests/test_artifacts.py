from pathlib import Path

import jobs.artifacts as artifacts


def test_save_and_load_text_artifact(tmp_path, monkeypatch):
    # Patch output folder to tmp
    class _S:
        base_output_folder = str(tmp_path)

    monkeypatch.setattr(artifacts, "settings", _S())

    artifact_id = artifacts.save_text_artifact(content="hello")
    assert artifact_id.endswith(".txt")

    content = artifacts.load_text_artifact(artifact_id=artifact_id)
    assert content == "hello"

    p = Path(tmp_path) / "artifacts" / artifact_id
    assert p.exists()


def test_reject_bad_artifact_id(tmp_path, monkeypatch):
    class _S:
        base_output_folder = str(tmp_path)

    monkeypatch.setattr(artifacts, "settings", _S())

    try:
        artifacts.load_text_artifact(artifact_id="../x")
        assert False, "expected ValueError"
    except ValueError:
        assert True
