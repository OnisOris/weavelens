from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from weavelens.llm.ollama_client import generate as ollama_generate


router = APIRouter()


class IntentIn(BaseModel):
    text: str


class IntentOut(BaseModel):
    action: Literal["ask", "search", "scan", "help", "unknown"]
    query: str


_INTENT_PROMPT = (
    "Ты — маршрутизатор команд для бота. По сообщению пользователя определи действие и, если нужно, сформулируй запрос.\n"
    "Доступные действия: scan, search, ask, help. Если не уверен — unknown.\n"
    "ПРАВИЛА:\n"
    "- scan: если просят пересканировать/проиндексировать/обновить базу (\"сканируй\", \"перескан\", \"reindex\").\n"
    "- search: если просят найти что-то в базе (\"найди\", \"поиск\", \"find\").\n"
    "- ask: если задают вопрос на естественном языке (объясни, что такое…, почему…, как…).\n"
    "- help: если просят помощь/список команд.\n"
    "ОТВЕЧАЙ только JSON в точном формате: {\"action\": string, \"query\": string}. Без дополнительных слов.\n"
    "Если action=scan/help/unknown — query оставь пустой строкой.\n"
    "Сообщение: \n"  # Текст придёт ниже
)


@router.post("/bot/intent", response_model=IntentOut)
async def detect_intent(body: IntentIn) -> IntentOut:
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is empty")

    prompt = _INTENT_PROMPT + text + "\nJSON:"
    try:
        raw = await ollama_generate(prompt, None, timeout=30.0)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {e}")

    # Попробуем вытащить JSON из ответа
    raw = (raw or "").strip()
    try:
        # Иногда модель оборачивает в блоки ```json … ``` — удалим их
        if raw.startswith("```"):
            raw = raw.strip("`\n ")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()
        data = json.loads(raw)
    except Exception:
        # Последняя попытка — безопасный ответ
        return IntentOut(action="unknown", query="")

    action = str(data.get("action", "unknown")).strip().lower()
    if action not in {"ask", "search", "scan", "help", "unknown"}:
        action = "unknown"
    query = str(data.get("query", "") or "").strip()
    if action in {"scan", "help", "unknown"}:
        query = ""
    return IntentOut(action=action, query=query)

