from __future__ import annotations
from typing import Any, Dict, List
from ..db.weaviate_client import get_client
from ..models.embeddings import embed_texts
from ..utils.crypto import maybe_decrypt
from ..settings import Settings
from weaviate.classes.query import MetadataQuery

def retrieve(q: str, k: int = 8) -> List[Dict[str, Any]]:
    vec = embed_texts([q])[0]
    wv = get_client()
    col = wv.collections.get("Chunk")
    res = col.query.near_vector(
        near_vector=vec, limit=k,
        return_properties=["text","doc_id","chunk_id","order"],
        return_metadata=MetadataQuery(distance=True),
    )
    s = Settings()
    hits = []
    for o in res.objects:
        props = o.properties
        text = props.get("text", "")
        text = maybe_decrypt(text, s.fernet_key) if s.encrypt_content else text
        hits.append({
            "text": text,
            "doc_id": props.get("doc_id"),
            "chunk_id": props.get("chunk_id"),
            "order": props.get("order"),
            "distance": o.metadata.distance,
        })
    return hits

def build_context(hits: List[Dict[str, Any]], max_chars: int = 4000) -> str:
    buf, n = [], 0
    for h in hits:
        t = (h.get("text") or "").strip()
        if n + len(t) > max_chars: break
        buf.append(t)
        n += len(t)
    return "\n\n---\n\n".join(buf)
