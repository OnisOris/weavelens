from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from ...pipeline.query import retrieve, build_context
from ...models.llm import ask_ollama

router = APIRouter()

class Q(BaseModel):
    q: str
    k: int = 8

@router.post("/search")
def search(q: Q):
    hits = retrieve(q.q, q.k)
    return {"hits": hits}

@router.post("/ask")
async def ask(q: Q):
    hits = retrieve(q.q, q.k)
    ctx = build_context(hits)
    prompt = f"Ответь строго по контексту. Если ответа нет — скажи, что ответа в документах нет.\n\nВопрос: {q.q}\n\nКонтекст:\n{ctx}"
    try:
        ans = await ask_ollama(prompt)
    except Exception:
        ans = "[LLM недоступна — вернул релевантные фрагменты]"
    return {"answer": {"text": ans, "used_chunks": len(hits)}, "hits": hits}
