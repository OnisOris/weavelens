from __future__ import annotations
from ..settings import Settings
import httpx

async def ask_ollama(prompt: str) -> str:
    s = Settings()
    url = f"http://{s.ollama_host}:{s.ollama_port}/api/generate"
    payload = {"model": s.llm_model, "prompt": prompt, "stream": False}
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    return data.get("response", "").strip()
