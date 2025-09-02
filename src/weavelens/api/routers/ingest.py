
from __future__ import annotations
from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from weavelens.settings import get_settings
from weavelens.pipeline.index import scan_and_index
settings = get_settings()


router = APIRouter()

class ScanIn(BaseModel):
    paths: Optional[List[str]] = None

@router.post("/ingest/scan")
async def ingest_scan(body: ScanIn):
    scan_paths: List[str] = []
    # always include INBOX_DIR
    if settings.inbox_dir:
        scan_paths.append(settings.inbox_dir)
    # add env extra dirs
    if settings.extra_scan_dirs:
        for p in settings.extra_scan_dirs.split(","):
            p = p.strip()
            if p:
                scan_paths.append(p)
    # add request-provided
    if body.paths:
        scan_paths.extend(body.paths)
    # dedupe
    seen = []
    sset = set()
    for p in scan_paths:
        if p not in sset:
            seen.append(p)
            sset.add(p)
    stats = scan_and_index(seen)
    return stats
