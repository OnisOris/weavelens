
from __future__ import annotations
import os, hashlib
from typing import List, Tuple, Dict, Any
from weavelens.settings import settings
from weavelens.db import weaviate_client as wv
from pypdf import PdfReader
from docx import Document as DocxDocument

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def read_text_from_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md"):
        with open(path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore")
    if ext == ".pdf":
        txt = []
        reader = PdfReader(path)
        for page in reader.pages:
            t = page.extract_text() or ""
            txt.append(t)
        return "\n".join(txt)
    if ext == ".docx":
        doc = DocxDocument(path)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def chunk_text(text: str, chunk_chars: int = 1200, overlap: int = 200) -> List[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        end = min(n, i + chunk_chars)
        chunks.append(text[i:end])
        if end == n:
            break
        i = end - overlap
        if i < 0:
            i = 0
    return chunks

def scan_and_index(paths: List[str]) -> Dict[str, Any]:
    files_processed = 0
    chunks_total = 0
    skipped = 0

    seen = set()
    for p in paths:
        if not p:
            continue
        p = os.path.abspath(p)
        if not os.path.exists(p):
            continue
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for fn in files:
                    full = os.path.join(root, fn)
                    if os.path.splitext(full)[1].lower() in SUPPORTED:
                        seen.add(full)
        else:
            if os.path.splitext(p)[1].lower() in SUPPORTED:
                seen.add(p)

    for fp in sorted(seen):
        try:
            with open(fp, "rb") as f:
                data = f.read()
            sha = sha256_bytes(data)
            if wv.find_document_by_sha256(sha):
                skipped += 1
                continue
            title = os.path.basename(fp)
            size = os.path.getsize(fp)
            text = read_text_from_path(fp)
            ch = chunk_text(text)
            if not ch:
                skipped += 1
                continue
            doc_uuid = wv.upsert_document(fp, sha, title, size)
            cnt = wv.add_chunks(doc_uuid, fp, title, ch)
            files_processed += 1
            chunks_total += cnt
        except Exception:
            skipped += 1

    return {
        "files_indexed": files_processed,
        "chunks_indexed": chunks_total,
        "skipped": skipped,
        # legacy keys for bot
        "files": files_processed,
        "chunks": chunks_total,
    }
