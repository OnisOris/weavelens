from __future__ import annotations
from pathlib import Path
from typing import Iterable

def list_files(root: str, exts: tuple[str,...] = (".pdf",".docx",".md",".txt")) -> list[Path]:
    p = Path(root)
    if not p.exists(): return []
    return [x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in exts]
