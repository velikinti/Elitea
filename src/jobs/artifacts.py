from __future__ import annotations

import re
import uuid
from pathlib import Path

from settings import settings


_ARTIFACT_ID_RE = re.compile(r"^[a-f0-9]{32}\.txt$")


def artifacts_dir() -> Path:
    base = Path(settings.base_output_folder)
    d = base / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def new_text_artifact_id() -> str:
    return f"{uuid.uuid4().hex}.txt"


def save_text_artifact(*, content: str, artifact_id: str | None = None) -> str:
    artifact_id = artifact_id or new_text_artifact_id()
    if not _ARTIFACT_ID_RE.match(artifact_id):
        raise ValueError("Invalid artifact_id format")

    path = artifacts_dir() / artifact_id
    path.write_text(content, encoding="utf-8")
    return artifact_id


def load_text_artifact(*, artifact_id: str) -> str:
    if not _ARTIFACT_ID_RE.match(artifact_id):
        raise ValueError("Invalid artifact_id format")

    path = artifacts_dir() / artifact_id
    if not path.exists() or not path.is_file():
        raise FileNotFoundError("Artifact not found")

    return path.read_text(encoding="utf-8")
