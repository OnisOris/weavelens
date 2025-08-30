from __future__ import annotations
from typing import Dict, List, Tuple
from ..db.weaviate_client import get_client

def _dedup_hits(raw: List[dict]) -> List[dict]:
    seen = set()
    out: List[dict] = []
    for h in raw:
        key = (h.get("doc_id"), h.get("order"), h.get("text"))
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out

def retrieve(query: str, k: int = 8) -> List[dict]:
    client = get_client()
    coll = client.collections.get("Chunk")
    # Try BM25 first if available
    res = coll.query.bm25(query=query, limit=max(k*2, k))
    raw = []
    for o in getattr(res, "objects", []):
        props = o.properties or {}
        raw.append({
            "text": props.get("text", ""),
            "doc_id": props.get("doc_id"),
            "chunk_id": props.get("chunk_id"),
            "order": props.get("order"),
            "path": props.get("path"),
            "filename": props.get("filename"),
            "distance": getattr(o, "distance", None),
        })
    hits = _dedup_hits(raw)[:k]
    return hits

def augment_with_paths(hits: List[dict]) -> List[dict]:
    # chunks already carry path/filename; nothing to do
    return hits