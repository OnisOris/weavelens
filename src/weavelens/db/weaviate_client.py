from __future__ import annotations
import weaviate
from typing import Tuple, List
from ..settings import Settings

_client = None

def _connect_server(s: Settings):
    # v4 client: connect_to_local(host="weaviate", port=8080, grpc_port=50051, headers=...)
    return weaviate.connect_to_local(
        host=s.weaviate_host,
        port=s.weaviate_port,
        grpc_port=50051,
        headers={"X-OpenAI-Api-Key": s.weaviate_api_key} if s.weaviate_api_key else None,
    )

def _connect_embedded(s: Settings):
    # NOTE: for embedded mode if you use weaviate-embedded python SDK; if not used, ignore.
    # Keeping a placeholder for compatibility.
    return weaviate.connect_to_local(
        host=s.weaviate_host,
        port=s.weaviate_port,
        grpc_port=50051,
        headers={"X-OpenAI-Api-Key": s.weaviate_api_key} if s.weaviate_api_key else None,
    )

def get_client():
    global _client
    if _client is None:
        s = Settings()
        _client = _connect_server(s) if s.profile == "server" else _connect_embedded(s)
    return _client

def check_weaviate_ready() -> Tuple[bool, str | None]:
    try:
        c = get_client()
        # a lightweight readiness probe: list collections
        _ = c.collections.list_all()
        return True, None
    except Exception as e:
        return False, str(e)

def list_collections() -> List[str]:
    try:
        c = get_client()
        cols = c.collections.list_all()
        return sorted([co.name for co in cols])
    except Exception:
        return []
