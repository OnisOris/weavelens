from __future__ import annotations
from fastapi import APIRouter
from ...utils.io import list_files
from ...ingest.loader import iter_documents
from ...pipeline.index import index_documents
from ...settings import Settings

router = APIRouter()

@router.post("/ingest/scan")
def ingest_scan():
    s = Settings()
    files = list_files(s.data_inbox) + list_files(s.data_sources)
    docs = list(iter_documents(files))
    n = index_documents(docs)
    return {"files": len(files), "chunks_indexed": n}
