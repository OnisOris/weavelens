
from __future__ import annotations
import httpx
from urllib.parse import urlparse

from weavelens.settings import get_settings, pick_ollama_model

settings = get_settings()


class OllamaError(Exception):
    pass


def _normalize_host(host: str) -> str:
    p = urlparse(host)
    return (p.netloc or p.path).rstrip("/")


def _base_url(host: str, port: int) -> str:
    host = _normalize_host(host)
    if ":" not in host:
        host = f"{host}:{port}"
    return f"http://{host}"


async def generate(prompt: str, model: str | None = None, timeout: float = 60.0) -> str:
    base = _base_url(settings.ollama_host, settings.ollama_port).rstrip("/")
    mdl = model or pick_ollama_model(settings.llm_accel, settings.ollama_model_cpu, settings.ollama_model_gpu)
    url = f"{base}/api/generate"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json={"model": mdl, "prompt": prompt, "stream": False})
        r.raise_for_status()
        data = r.json()
        if "response" not in data:
            raise OllamaError("no response field from ollama")
        return data["response"]
