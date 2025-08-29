from __future__ import annotations
import httpx
from typing import Optional, Sequence
from ..settings import Settings

def _sanitize_host(host: str) -> str:
    # strip scheme if present
    if host.startswith("http://"):
        return host[len("http://"):]
    if host.startswith("https://"):
        return host[len("https://"):]
    return host

def _base_url(s: Settings) -> str:
    host = _sanitize_host(s.ollama_host)
    # if host already contains a port, keep as-is
    if ":" in host:
        return f"http://{host}"
    return f"http://{host}:{s.ollama_port}"

def compose_prompt(user_question: str, context_chunks: Sequence[str] | None = None, system: Optional[str] = None) -> str:
    system_p = (system or
        "You are a concise assistant. Answer strictly based on the provided CONTEXT. "
        "If the answer is not in the context, say you don't know.")
    ctx = ""
    if context_chunks:
        joined = "\n\n".join(f"- {t.strip()}" for t in context_chunks if t and t.strip())
        ctx = f"\n\nCONTEXT:\n{joined}\n\n"
    return f"{system_p}{ctx}QUESTION: {user_question}\nANSWER:"

def generate_answer(question: str, chunks: Sequence[str], *, timeout: float = 120.0, model: Optional[str] = None) -> str:
    s = Settings()
    url = f"{_base_url(s)}/api/generate"
    payload = {
        "model": model or s.llm_model,
        "prompt": compose_prompt(question, chunks),
        "stream": False,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
            # common error when model tag mismatches: 404 with 'model not found'
            if r.status_code == 404:
                raise RuntimeError(f"Ollama: model '{payload['model']}' not found on {url}.")
            r.raise_for_status()
            data = r.json()
            text = (data or {}).get("response") or ""
            return text.strip() or "[empty response]"
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")
