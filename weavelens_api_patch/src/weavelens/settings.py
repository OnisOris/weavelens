
from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    weaviate_grpc_url: str = os.getenv("WEAVIATE_GRPC_URL", "http://weaviate:50051")
    inbox_dir: str = os.getenv("INBOX_DIR", "data/inbox")
    extra_scan_dirs: str = os.getenv("WEAVELENS_SCAN_DIRS", "").strip()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct-q4_0")
    api_prefix: str = os.getenv("API_PREFIX", "/api")

settings = Settings()
