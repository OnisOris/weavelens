from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from weavelens.settings import get_settings
from weavelens.pipeline.index import scan_and_index


router = APIRouter()


@router.post("/ingest/scan")
async def ingest_scan():
    """
    Просканировать входную директорию и проиндексировать поддерживаемые файлы.
    Возвращает счётчики, совместимые с ботом (/scan ожидает keys: files, chunks_indexed).
    """

    settings = get_settings()
    inbox = Path(settings.inbox_dir)
    if not inbox.exists():
        raise HTTPException(status_code=400, detail=f"inbox_dir does not exist: {inbox}")
    if not inbox.is_dir():
        raise HTTPException(status_code=400, detail=f"inbox_dir is not a directory: {inbox}")

    # Запускаем индексацию (скан + дедуп + разбиение на чанки + запись в Weaviate)
    result = scan_and_index([str(inbox)])

    # Дополнительная справочная информация (не используется ботом, но полезна в UI)
    try:
        entries: List[Path] = [p for p in inbox.iterdir() if p.is_file()]
        sample = [p.name for p in entries[:50]]
        extras = {"count": len(entries), "sample": sample}
    except Exception:
        extras = {}

    return {"inbox_dir": str(inbox), **result, **extras}
