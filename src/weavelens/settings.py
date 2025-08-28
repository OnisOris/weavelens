from __future__ import annotations
from pydantic import BaseModel
import os

class Settings(BaseModel):
    offline: bool = os.getenv("WEAVELENS_OFFLINE", "true").lower() == "true"
    profile: str = os.getenv("WEAVELENS_PROFILE", "server")

    # weaviate server
    weaviate_host: str = os.getenv("WEAVIATE_HOST", "localhost")
    weaviate_port: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    weaviate_scheme: str = os.getenv("WEAVIATE_SCHEME", "http")
    weaviate_api_key: str | None = os.getenv("WEAVIATE_API_KEY") or None

    # embedded
    weaviate_embedded_path: str = os.getenv("WEAVIATE_EMBEDDED_DATA_PATH", "/app/data/weaviate")

    # embeddings
    emb_model_name: str = os.getenv("EMB_MODEL_NAME", "bge-m3")
    emb_device: str = os.getenv("EMB_DEVICE", "cpu")
    emb_max_seq: int = int(os.getenv("EMB_MAX_SEQ", "1024"))

    # llm
    ollama_host: str = os.getenv("OLLAMA_HOST", "localhost")
    ollama_port: int = int(os.getenv("OLLAMA_PORT", "11434"))
    llm_model: str = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M")

    # api
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-please-change")

    # bot
    tg_token: str | None = os.getenv("TG_BOT_TOKEN")
    tg_allowlist: list[int] = [int(x) for x in (os.getenv("TG_ALLOWLIST", "")).split(",") if x.strip().isdigit()]
    bot_api_url: str = os.getenv("BOT_API_URL", "http://localhost:8000/api")

    # paths
    data_inbox: str = os.getenv("DATA_INBOX", "/app/data/inbox")
    data_sources: str = os.getenv("DATA_SOURCES", "/app/data/sources")
    data_processed: str = os.getenv("DATA_PROCESSED", "/app/data/processed")
    models_cache: str = os.getenv("MODELS_CACHE", "/app/models/cache")

    # security/encryption
    encrypt_content: bool = os.getenv("ENCRYPT_CONTENT", "false").lower() == "true"
    fernet_key: str | None = os.getenv("FERNET_KEY") or None
