from __future__ import annotations
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from weavelens.db import weaviate_client as wv
from weavelens.llm.ollama_client import generate as ollama_generate

router = APIRouter()

class QueryIn(BaseModel):
    q: str
    k: int = Field(default=8, ge=1, le=50)

@router.post("/search")
async def search(body: QueryIn):
    hits = wv.search_bm25(body.q, body.k)
    return {"hits": hits}

def _format_context(hits: List[Dict[str, Any]]) -> str:
    lines = []
    for i, h in enumerate(hits, 1):
        src = h.get("path") or h.get("title") or ""
        txt = h.get("text") or ""
        lines.append(f"[{i}] Source: {src}\n{txt}")
    return "\n\n".join(lines)

@router.post("/ask")
async def ask(body: QueryIn):
    hits = wv.search_bm25(body.q, body.k)
    if not hits:
        return {"answer": {"text": "Ничего не нашёл по базе.", "used_chunks": 0}, "hits": []}
    prompt = (
        "Ты — помощник. Отвечай кратко и по делу только на основе контекста. "
        "Если ответа нет в контексте — скажи, что в материалах не нашлось.\n\n"
        f"Контекст:\n{_format_context(hits)}\n\nВопрос: {body.q}\nОтвет:"
    )
    try:
        text = await ollama_generate(prompt, None, timeout=120.0)
    except Exception:
        text = "[LLM недоступна — вернул релевантные фрагменты]"
    return {"answer": {"text": text, "used_chunks": len(hits)}, "hits": hits}
