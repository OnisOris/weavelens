from __future__ import annotations
from fastapi import APIRouter
from ..utils import ok_json
from ...db.weaviate_client import check_weaviate_ready, list_collections

router = APIRouter()

@router.get("/live")
def live():
    return {"status": "alive"}

@router.get("/ready")
def ready():
    ok, err = check_weaviate_ready()
    return {"weaviate_ready": ok, **({"error": err} if err else {})}

@router.get("/health")
def health():
    ok, err = check_weaviate_ready()
    status = "ok" if ok else "down"
    payload = {"status": status, "weaviate_ready": ok}
    if ok:
        payload["collections"] = list_collections()
    else:
        payload["error"] = err
    return payload
