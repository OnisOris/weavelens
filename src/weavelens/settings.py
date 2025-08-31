from __future__ import annotations

import os
import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from pydantic import Field, AliasChoices, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(val) -> List[int]:
    if val is None:
        return []
    if isinstance(val, list):
        return [int(x) for x in val if str(x).strip()]
    if isinstance(val, (int,)):
        return [int(val)]
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        parts = re.split(r"[,\s;]+", s)
        out: List[int] = []
        for p in parts:
            if not p:
                continue
            try:
                out.append(int(p))
            except ValueError:
                # silently skip junk; we just don't include it
                continue
        return out
    return []


def _derive_grpc_url(http_url: str | None) -> str | None:
    if not http_url:
        return None
    u = urlparse(http_url)
    host = u.hostname or "weaviate"
    port = 50051
    # keep the scheme http to avoid unknown scheme errors in clients that just parse/ignore it
    return urlunparse((u.scheme or "http", f"{host}:{port}", "", "", "", ""))


class Settings(BaseSettings):
    # FastAPI
    api_prefix: str = Field(default="/api", validation_alias=AliasChoices("API_PREFIX", "WEAVELENS_API_PREFIX"))

    # Paths for ingest
    inbox_dir: Optional[str] = Field(default=None, validation_alias=AliasChoices("INBOX_DIR", "WEAVELENS_INBOX_DIR"))
    extra_scan_dirs: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("EXTRA_SCAN_DIRS", "WEAVELENS_EXTRA_SCAN_DIRS"),
    )

    # Weaviate
    weaviate_url: str = Field(default="http://weaviate:8080", validation_alias=AliasChoices("WEAVIATE_URL"))
    weaviate_grpc_url: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("WEAVIATE_GRPC_URL", "WEAVIATE_GRPC")
    )

    # Ollama
    ollama_url: str = Field(default="http://ollama:11434", validation_alias=AliasChoices("OLLAMA_URL"))
    ollama_model: str = Field(default="llama3.2:3b", validation_alias=AliasChoices("OLLAMA_MODEL"))

    # Bot & auth
    # keep both names; the bot expects `tg_token` attribute, envs might be BOT_TOKEN or TG_BOT_TOKEN
    bot_token: Optional[str] = Field(default=None, validation_alias=AliasChoices("BOT_TOKEN", "TG_BOT_TOKEN"))
    tg_token: Optional[str] = Field(default=None, validation_alias=AliasChoices("TG_TOKEN", "TG_BOT_TOKEN", "BOT_TOKEN"))
    bot_api_url: Optional[str] = Field(default=None, validation_alias=AliasChoices("BOT_API_URL"))
    tg_allowlist: List[int] = Field(default_factory=list, validation_alias=AliasChoices("TG_ALLOWLIST", "BOT_ALLOWLIST"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @model_validator(mode="after")
    def _post(self) -> "Settings":
        # Normalize extra_scan_dirs: split string to list if needed
        if isinstance(self.extra_scan_dirs, str):
            raw = self.extra_scan_dirs.strip()
            self.extra_scan_dirs = [p for p in re.split(r"[,\s;]+", raw) if p]

        # Parse allowlist robustly
        self.tg_allowlist = _parse_int_list(self.tg_allowlist)

        # Ensure tg_token is present as alias to bot_token if missing
        if not self.tg_token and self.bot_token:
            self.tg_token = self.bot_token

        # Autoderive gRPC URL if not provided
        if not self.weaviate_grpc_url and self.weaviate_url:
            self.weaviate_grpc_url = _derive_grpc_url(self.weaviate_url)

        return self


settings = Settings()
