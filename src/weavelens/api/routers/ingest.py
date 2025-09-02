from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from weavelens.settings import get_settings


router = APIRouter()


@router.post("/ingest/scan")
async def ingest_scan():
    """
    Простой скан входной директории.
    Возвращает список файлов (усечённый), чтобы проверить wiring.
    """

    settings = get_settings()
    inbox = Path(settings.inbox_dir)
    if not inbox.exists():
        raise HTTPException(status_code=400, detail=f"inbox_dir does not exist: {inbox}")
    if not inbox.is_dir():
        raise HTTPException(status_code=400, detail=f"inbox_dir is not a directory: {inbox}")

    entries: List[Path] = [p for p in inbox.iterdir() if p.is_file()]
    sample = entries[:50]
    return {
        "inbox_dir": str(inbox),
        "count": len(entries),
        "sample": [p.name for p in sample],
    }

