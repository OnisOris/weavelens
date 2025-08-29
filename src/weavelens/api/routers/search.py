from __future__ import annotations
from pydantic import BaseModel, Field
from fastapi import APIRouter
from typing import List
from ...pipeline.query import retrieve
from ...llm.ollama_client import generate_answer

router = APIRouter()

class SearchQuery(BaseModel):
    q: str = Field(..., description="Query text")
    k: int = Field(5, description="Top-K hits")

@router.post("/search")
def search(q: SearchQuery):
    hits = retrieve(q.q, q.k)
    return {"hits": hits}

@router.post("/ask")
def ask(q: SearchQuery):
    hits = retrieve(q.q, q.k)
    chunks = [h.get("text","") for h in hits]
    try:
        text = generate_answer(q.q, chunks)
        return {"answer": {"text": text, "used_chunks": len(chunks)}, "hits": hits}
    except Exception:
        # graceful fallback
        return {"answer": {"text": "[LLM недоступна — вернул релевантные фрагменты]", "used_chunks": len(chunks)}, "hits": hits}
