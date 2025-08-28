from __future__ import annotations
from pathlib import Path
from typing import Iterator, Dict, Any
from .chunker import split_into_chunks
from ..utils.text import read_any
import hashlib, json, time

def fingerprint_text(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()

def doc_id_for_path(p: Path) -> str:
    st = p.stat()
    raw = f"{p.resolve()}:{int(st.st_mtime)}:{st.st_size}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]

def iter_documents(paths: list[Path], collection: str = "misc", source: str = "local") -> Iterator[Dict[str, Any]]:
    for p in paths:
        try:
            text = read_any(p)
            if not text.strip():
                continue
            doc_id = doc_id_for_path(p)
            yield dict(
                doc_id=doc_id,
                title=p.stem,
                path=str(p.resolve()),
                source=source,
                collection=collection,
                tags=[p.suffix.lower().lstrip(".")],
                text=text,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime)),
            )
        except Exception:
            continue
