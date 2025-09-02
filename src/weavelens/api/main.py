from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from weavelens.settings import get_settings
from weavelens.api.routers import health, search, ingest


settings = get_settings()
app = FastAPI(title="WeaveLens API")
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(search.router, prefix=settings.api_prefix, tags=["search"])
app.include_router(ingest.router, prefix=settings.api_prefix, tags=["ingest"])


def run() -> None:
    uvicorn.run(
        "weavelens.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    run()

