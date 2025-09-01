from __future__ import annotations

import os
from typing import List, Optional, Any
from urllib.parse import urlparse

from pydantic import Field, AliasChoices
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(val: Any) -> List[int]:
    if val is None or val == "":
        return []
    if isinstance(val, list):
        out: List[int] = []
        for x in val:
            if x is None or x == "":
                continue
            out.append(int(x))
        return out
    if isinstance(val, (int,)):
        return [int(val)]
    s = str(val).strip()
    # JSON-like list
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p for p in s.replace(";", ",").split(",")]
    out: List[int] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(int(p))
    return out


def _parse_str_list(val: Any) -> List[str]:
    if val is None or val == "":
        return []
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    s = str(val).strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p.strip() for p in s.replace(";", ",").split(",")]
    return [p for p in parts if p]


class Settings(BaseSettings):
    """
    Project settings with robust env parsing (Pydantic v2).
    Compatible with API + bot containers.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API ---
    api_prefix: str = Field(default="/api", validation_alias=AliasChoices("API_PREFIX"))

    inbox_dir: Optional[str] = Field(default=None, validation_alias=AliasChoices("INBOX_DIR"))
    extra_scan_dirs: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("EXTRA_SCAN_DIRS", "SCAN_DIRS"),
    )

    # --- Vector DB / Weaviate ---
    weaviate_url: str = Field(
        default="http://weaviate:8080",
        validation_alias=AliasChoices("WEAVIATE_URL"),
    )
    weaviate_grpc_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WEAVIATE_GRPC_URL"),
    )

    # --- LLM / Ollama ---
    ollama_url: str = Field(
        default="http://ollama:11434",
        validation_alias=AliasChoices("OLLAMA_URL", "OLLAMA_BASE_URL"),
    )
    ollama_model: str = Field(
        default="llama3.2:3b-instruct",
        validation_alias=AliasChoices("OLLAMA_MODEL", "LLM_MODEL"),
    )

    # --- Bot ---
    bot_api_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("BOT_API_URL", "BOT_API_BASE", "API_BASE"),
    )
    # keep both names for compatibility
    bot_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("TG_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
    )
    tg_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("TG_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "TG_TOKEN"),
    )
    tg_allowlist: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("TG_ALLOWLIST", "TELEGRAM_ALLOWLIST", "BOT_ALLOWLIST"),
    )
    tg_denied_msg: str = Field(default="Доступ запрещен", validation_alias=AliasChoices("TG_DENIED_MSG"))

    @field_validator("api_prefix", mode="before")
    @classmethod
    def _fix_api_prefix(cls, v: Any) -> str:
        if not v:
            return "/api"
        s = str(v).strip()
        if not s.startswith("/"):
            s = "/" + s
        return s

    @field_validator("tg_allowlist", mode="before")
    @classmethod
    def _fix_allowlist(cls, v: Any) -> List[int]:
        return _parse_int_list(v)

    @field_validator("extra_scan_dirs", mode="before")
    @classmethod
    def _fix_extra_dirs(cls, v: Any) -> List[str]:
        return _parse_str_list(v)

    @model_validator(mode="after")
    def _fill_derived(self) -> "Settings":
        # tg_token/bot_token mirror
        if not self.tg_token and self.bot_token:
            self.tg_token = self.bot_token
        if not self.bot_token and self.tg_token:
            self.bot_token = self.tg_token

        # derive gRPC from HTTP if missing
        if not self.weaviate_grpc_url:
            try:
                u = urlparse(self.weaviate_url)
                host = (u.netloc or u.path).split("@")[-1]  # handle userinfo if any
                host = host.split(":")[0] if ":" in host else host
                if host:
                    self.weaviate_grpc_url = f"grpc://{host}:50051"
            except Exception:
                # leave as None if parsing failed
                pass

        # bot_api_url default to api container + prefix
        if not self.bot_api_url:
            self.bot_api_url = f"http://api:8000{self.api_prefix}"

        return self


# Singleton for easy import
settings = Settings()
