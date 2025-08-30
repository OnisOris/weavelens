
from __future__ import annotations
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weavelens.settings import settings

_client: Optional[weaviate.WeaviateClient] = None

CHUNK_COLLECTION = "chunk"
DOCUMENT_COLLECTION = "document"

def _connect() -> weaviate.WeaviateClient:
    global _client
    if _client is not None:
        return _client
    o = urlparse(settings.weaviate_url)
    host = o.hostname or "weaviate"
    port = o.port or 8080
    go = urlparse(settings.weaviate_grpc_url)
    grpc_port = go.port or 50051
    _client = weaviate.connect_to_local(host=host, port=port, grpc_port=grpc_port)
    _ensure_schema(_client)
    return _client

def client() -> weaviate.WeaviateClient:
    return _connect()

def _ensure_schema(c: weaviate.WeaviateClient) -> None:
    # document
    if not c.collections.exists(DOCUMENT_COLLECTION):
        c.collections.create(
            name=DOCUMENT_COLLECTION,
            properties=[
                Property(name="path", data_type=DataType.TEXT),
                Property(name="sha256", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="size", data_type=DataType.INT),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )
    # chunk
    if not c.collections.exists(CHUNK_COLLECTION):
        c.collections.create(
            name=CHUNK_COLLECTION,
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="order", data_type=DataType.INT),
                Property(name="doc_uuid", data_type=DataType.TEXT),
                Property(name="path", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
        )

def find_document_by_sha256(sha: str) -> Optional[str]:
    c = client()
    coll = c.collections.get(DOCUMENT_COLLECTION)
    res = coll.query.fetch_objects(
        filters=weaviate.classes.query.Filter.by_property("sha256").equal(sha),
        limit=1,
        return_properties=["sha256"],
    )
    if res.objects:
        return res.objects[0].uuid
    return None

def upsert_document(path: str, sha256: str, title: str, size: int) -> str:
    c = client()
    coll = c.collections.get(DOCUMENT_COLLECTION)
    existing = find_document_by_sha256(sha256)
    if existing:
        return existing
    uid = coll.data.insert(properties={"path": path, "sha256": sha256, "title": title, "size": int(size)})
    return uid

def add_chunks(doc_uuid: str, path: str, title: str, chunks: List[str]) -> int:
    c = client()
    coll = c.collections.get(CHUNK_COLLECTION)
    count = 0
    for i, txt in enumerate(chunks):
        coll.data.insert(
            properties={
                "text": txt,
                "order": i,
                "doc_uuid": doc_uuid,
                "path": path,
                "title": title,
            }
        )
        count += 1
    return count

def search_bm25(query: str, k: int = 8) -> List[Dict[str, Any]]:
    c = client()
    coll = c.collections.get(CHUNK_COLLECTION)
    res = coll.query.bm25(
        query=query,
        limit=k,
        return_properties=["text", "order", "doc_uuid", "path", "title"],
    )
    hits: List[Dict[str, Any]] = []
    for o in getattr(res, "objects", []) or []:
        props = o.properties or {}
        meta = getattr(o, "metadata", None)
        score = getattr(meta, "score", None) if meta else None
        hits.append({
            "text": props.get("text", ""),
            "doc_id": props.get("doc_uuid"),  # logical document id (string we stored)
            "chunk_id": o.uuid,
            "order": props.get("order", 0),
            "distance": score if score is not None else 0.0,
            "path": props.get("path"),
            "title": props.get("title"),
        })
    return hits
