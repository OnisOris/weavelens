
from __future__ import annotations
import uvicorn
from fastapi import FastAPI
from weavelens.settings import settings
from weavelens.api.routers import health, search, ingest

app = FastAPI(title="WeaveLens API")

# Mount routers under /api by default (matches bot expectations)
app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
app.include_router(search.router, prefix=settings.api_prefix, tags=["search"])
app.include_router(ingest.router, prefix=settings.api_prefix, tags=["ingest"])

def run() -> None:
    uvicorn.run("weavelens.api.main:app", host="0.0.0.0", port=8000, reload=False)

# For uvicorn autodiscovery
if __name__ == "__main__":
    run()
