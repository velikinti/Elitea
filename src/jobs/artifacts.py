from __future__ import annotations

import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from settings import settings


def _artifacts_dir() -> str:
    base_output_dir = os.path.join(os.getcwd(), settings.base_output_folder)
    path = os.path.join(base_output_dir, "artifacts")
    os.makedirs(path, exist_ok=True)
    return path


def save_text_artifact(content: str, filename_hint: Optional[str] = None) -> str:
    """Persist a text artifact and return artifact_id.

    The artifact_id is the filename (unique) stored under outputfolder/artifacts.
    """

    artifact_id = uuid4().hex
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    safe_hint = "artifact"
    if filename_hint:
        safe_hint = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in filename_hint)
        safe_hint = safe_hint.strip("_") or "artifact"

    filename = f"{ts}_{safe_hint}_{artifact_id}.txt"
    path = os.path.join(_artifacts_dir(), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return filename


def get_artifact_path(artifact_id: str) -> str:
    return os.path.join(_artifacts_dir(), artifact_id)


def read_text_artifact(artifact_id: str) -> str:
    path = get_artifact_path(artifact_id)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
