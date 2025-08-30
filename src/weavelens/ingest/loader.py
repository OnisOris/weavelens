from __future__ import annotations
import os, hashlib, time
from typing import Dict, Iterable, List, Tuple
from ..db.weaviate_client import get_client
from .chunker import iter_chunks

def _sha256_file(path: str, buf_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def _doc_id_from_sha(sha256: str) -> str:
    return sha256[:16]

def _chunk_id(doc_id: str, order: int) -> str:
    return f"{doc_id}:{order:06d}"

def _read_text_file(path: str) -> str:
    # naive: treat as utf-8; extend for pdf/docx as needed
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def scan_paths(paths: Iterable[str]) -> Tuple[int, int]:
    """Scan given paths, deduplicate by file content (sha256),

    upsert Document and Chunk objects into Weaviate.

    Returns (files_seen, chunks_indexed)

    """
    client = get_client()
    docs = client.collections.get("Document")
    chunks = client.collections.get("Chunk")

    files_seen = 0
    chunks_indexed = 0

    for base in paths:
        if not base or not os.path.exists(base):
            continue
        for root_dir, _, files in os.walk(base):
            for name in files:
                full = os.path.join(root_dir, name)
                try:
                    sha = _sha256_file(full)
                except Exception:
                    continue
                doc_id = _doc_id_from_sha(sha)
                stat = os.stat(full)
                size = stat.st_size
                mtime = stat.st_mtime

                files_seen += 1

                # Dedup by sha256: if doc exists, skip
                exists = docs.query.fetch_objects(
                    filters={"sha256": ["eq", sha]},
                    limit=1,
                )
                if exists and len(exists.objects) > 0:
                    continue

                text = ""
                try:
                    text = _read_text_file(full)
                except Exception:
                    # skip non-text for now
                    continue

                # Upsert Document
                docs.data.insert({
                    "doc_id": doc_id,
                    "path": full,
                    "filename": name,
                    "sha256": sha,
                    "size": size,
                    "mtime": mtime,
                })

                # Upsert Chunks
                for order, chunk_text in enumerate(iter_chunks(text)):
                    chunks.data.insert({
                        "chunk_id": _chunk_id(doc_id, order),
                        "doc_id": doc_id,
                        "order": order,
                        "text": chunk_text,
                        "path": full,
                        "filename": name,
                    })
                    chunks_indexed += 1
    return files_seen, chunks_indexed