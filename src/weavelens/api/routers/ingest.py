from __future__ import annotations

from fastapi import APIRouter
from weavelens.settings import settings
from weavelens.pipeline.index import scan_and_index

router = APIRouter()


@router.post("/ingest/scan")
async def ingest_scan():
    """
    Scan configured folders and (re)index supported documents.
    Safe when no folders configured: returns zero stats instead of 500.
    """
    paths: list[str] = []
    if settings.inbox_dir:
        paths.append(settings.inbox_dir)
    if settings.extra_scan_dirs:
        paths.extend([p for p in settings.extra_scan_dirs if p])

    if not paths:
        return {
            "indexed": {"files": 0, "chunks": 0, "skipped": 0},
            "paths": [],
            "note": "No INBOX_DIR / EXTRA_SCAN_DIRS configured; nothing to scan.",
        }

    stats = scan_and_index(paths)
    return {"indexed": stats, "paths": paths}
