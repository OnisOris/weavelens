
from __future__ import annotations
import httpx
from weavelens.settings import get_settings

settings = get_settings()

class OllamaError(Exception):
    pass

async def generate(prompt: str, model: str | None = None, timeout: float = 60.0) -> str:
    base = settings.ollama_base_url.rstrip("/")
    mdl = model or settings.ollama_model
    url = f"{base}/api/generate"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json={"model": mdl, "prompt": prompt, "stream": False})
        r.raise_for_status()
        data = r.json()
        if "response" not in data:
            raise OllamaError("no response field from ollama")
        return data["response"]
