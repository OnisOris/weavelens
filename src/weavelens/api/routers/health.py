from __future__ import annotations
from fastapi import APIRouter
from ...db.weaviate_client import get_client

router = APIRouter()

@router.get("/health")
def health():
    # ping weaviate
    c = get_client()
    cols = [c.name for c in c.collections.list_all()]
    return {"status":"ok", "collections": cols}
