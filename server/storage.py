from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from fastapi import UploadFile

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._ -]+")


def storage_base() -> Path:
    base = os.environ.get("STORAGE_DIR", "./storage")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(name: str) -> str:
    # remove path separators and normalize
    name = name.replace("\\", "/").split("/")[-1]
    name = _FILENAME_SAFE.sub("_", name).strip()
    return name or "file"


def ext_to_kind(ext: str) -> str:
    e = ext.lower().lstrip(".")
    if e in {"docx"}:
        return "docx"
    if e in {"txt"}:
        return "txt"
    if e in {"md", "markdown"}:
        return "md"
    return "txt"


def save_upload_for_project(
    *, user_id: str, project_id: str, up: UploadFile
) -> tuple[Path, str, str]:
    """Save an UploadFile under storage/<user>/<project>/ and return (path, checksum, kind).

    The file is saved streaming to avoid large memory usage, computing sha256 on the fly.
    """
    base = storage_base() / user_id / project_id
    base.mkdir(parents=True, exist_ok=True)

    original_name = safe_filename(up.filename or "file")
    ext = Path(original_name).suffix
    kind = ext_to_kind(ext)

    # Pre-allocate destination using a temporary name to avoid partial files
    tmp_path = base / (".tmp_" + original_name)
    h = hashlib.sha256()
    with tmp_path.open("wb") as f:
        while True:
            chunk = up.file.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)
    checksum = h.hexdigest()
    dest_name = f"{checksum[:8]}_{original_name}"
    dest_path = base / dest_name
    tmp_path.replace(dest_path)
    return dest_path, checksum, kind
