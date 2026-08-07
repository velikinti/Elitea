from __future__ import annotations

import os
import re
import uuid
from datetime import datetime
from typing import Optional

from settings import settings


_ARTIFACT_ID_RE = re.compile(r"^[a-f0-9]{32}\.txt$")


def _artifacts_dir() -> str:
    base_output_dir = os.path.join(os.getcwd(), settings.base_output_folder)
    p = os.path.join(base_output_dir, "artifacts")
    os.makedirs(p, exist_ok=True)
    return p


def save_text_artifact(prefix: str, content: str) -> str:
    """Persist content to outputfolder/artifacts and return artifact_id.

    artifact_id is a filename with strict allowlist format: <uuidhex>.txt
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_id = f"{uuid.uuid4().hex}.txt"
    filename = f"{ts}_{prefix}_{artifact_id}"

    path = os.path.join(_artifacts_dir(), filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")

    # Return only the final uuid-based token portion for retrieval.
    # Retrieval scans directory for *_<artifact_id>
    return artifact_id


def load_text_artifact(artifact_id: str) -> Optional[str]:
    """Load artifact content by artifact_id.

    We do not accept arbitrary paths. We only accept a strict UUID-hex token.
    """
    if not _ARTIFACT_ID_RE.fullmatch(artifact_id):
        return None

    d = _artifacts_dir()
    # Match suffix *_<artifact_id>
    for name in os.listdir(d):
        if name.endswith(f"_{artifact_id}"):
            path = os.path.join(d, name)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return None
