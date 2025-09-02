from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -------- Bot --------
    tg_token: Optional[str] = Field(default=None, alias="TG_BOT_TOKEN")
    tg_allowlist: List[int] = Field(default_factory=list, alias="TG_ALLOWLIST")
    bot_api_url: Optional[str] = Field(default=None, alias="BOT_API_URL")

    # -------- API --------
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    jwt_secret: Optional[str] = Field(default=None, alias="JWT_SECRET")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")  # <-- добавили

    # -------- WeaveLens --------
    weavelens_offline: bool = Field(default=False, alias="WEAVELENS_OFFLINE")
    weavelens_profile: str = Field(default="server", alias="WEAVELENS_PROFILE")

    # -------- Weaviate (server) --------
    weaviate_host: str = Field(default="weaviate", alias="WEAVIATE_HOST")
    weaviate_port: int = Field(default=8080, alias="WEAVIATE_PORT")
    weaviate_scheme: str = Field(default="http", alias="WEAVIATE_SCHEME")
    weaviate_api_key: Optional[str] = Field(default=None, alias="WEAVIATE_API_KEY")

    # -------- Weaviate (embedded) --------
    weaviate_embedded_data_path: str = Field(
        default="/app/data/weaviate", alias="WEAVIATE_EMBEDDED_DATA_PATH"
    )

    # -------- Embeddings --------
    emb_model_name: str = Field(default="BAAI/bge-m3", alias="EMB_MODEL_NAME")
    emb_device: str = Field(default="cpu", alias="EMB_DEVICE")
    emb_max_seq: int = Field(default=1024, alias="EMB_MAX_SEQ")

    # -------- LLM / Ollama --------
    ollama_host: str = Field(default="ollama", alias="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, alias="OLLAMA_PORT")
    llm_accel: str = Field(default="cpu", alias="LLM_ACCEL")
    ollama_model_cpu: str = Field(default="qwen2.5:3b-instruct-q4_0", alias="OLLAMA_MODEL_CPU")
    ollama_model_gpu: str = Field(default="qwen2.5:7b-instruct-q4_0", alias="OLLAMA_MODEL_GPU")
    ollama_num_gpu_layers: int = Field(default=0, alias="OLLAMA_NUM_GPU_LAYERS")

    # -------- Paths --------
    data_inbox: str = Field(default="/app/data/inbox", alias="DATA_INBOX")
    data_sources: str = Field(default="/app/data/sources", alias="DATA_SOURCES")
    data_processed: str = Field(default="/app/data/processed", alias="DATA_PROCESSED")
    models_cache: str = Field(default="/app/models/cache", alias="MODELS_CACHE")

    # -------- Security --------
    encrypt_content: bool = Field(default=False, alias="ENCRYPT_CONTENT")
    fernet_key: Optional[str] = Field(default=None, alias="FERNET_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("tg_allowlist", mode="before")
    @classmethod
    def _parse_allowlist(cls, v):
        if v in (None, "", []):
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        return [int(x) for x in str(v).replace(";", ",").split(",") if str(x).strip()]

    @field_validator("api_prefix", mode="after")
    @classmethod
    def _normalize_prefix(cls, v: str) -> str:
        # гарантируем ведущий слэш и убираем хвостовой
        v = "/" + v.lstrip("/")
        return v.rstrip("/") or "/api"


@lru_cache
def get_settings() -> Settings:
    # Лениво читаем .env один раз за процесс
    return Settings()


# Если хочется иметь модульную переменную — можно раскомментировать:
# settings = get_settings()

__all__ = ["Settings", "get_settings"]
