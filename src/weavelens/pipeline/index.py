from __future__ import annotations
from typing import Iterable, Dict, Any
from ..db.weaviate_client import get_client
from ..models.embeddings import embed_texts
from ..ingest.chunker import split_into_chunks
from ..utils.crypto import maybe_encrypt
from ..settings import Settings
import hashlib, json

def index_documents(docs: Iterable[Dict[str, Any]]) -> int:
    s = Settings()
    wv = get_client()
    col_doc = wv.collections.get("Document")
    col_chunk = wv.collections.get("Chunk")
    n = 0
    for d in docs:
        col_doc.data.insert({
            "doc_id": d["doc_id"],
            "title": d["title"],
            "path": d["path"],
            "source": d["source"],
            "collection": d["collection"],
            "tags": d["tags"],
            "created_at": d["created_at"],
        })
        chunks = split_into_chunks(d["text"])
        vecs = embed_texts(chunks)
        for i, (ch, v) in enumerate(zip(chunks, vecs)):
            chunk_id = hashlib.sha1(f"{d['doc_id']}:{i}".encode()).hexdigest()[:16]
            text_store = maybe_encrypt(ch, s.fernet_key) if s.encrypt_content else ch
            col_chunk.data.insert({
                "doc_id": d["doc_id"],
                "text": text_store,
                "chunk_id": chunk_id,
                "section": "body",
                "order": i,
                "tokens": len(ch.split()),
                "keywords": [],
                "meta": json.dumps({"path": d["path"]}, ensure_ascii=False),
            }, vector=v)
            n += 1
    return n

def cli():
    # simple CLI to index files from DATA_INBOX
    from ..utils.io import list_files
    from ..ingest.loader import iter_documents
    s = Settings()
    paths = list_files(s.data_inbox)
    docs = iter_documents(paths)
    n = index_documents(docs)
    print(f"Indexed chunks: {n}")
