from __future__ import annotations
from fastapi import FastAPI, Depends, Header, HTTPException
from .routers import health, search, ingest
from ..settings import Settings
from ..monitoring.logging import setup_logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="WeaveLens API")
app.include_router(health.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

def run():
    setup_logging()
    from ..settings import Settings
    import uvicorn
    s = Settings()
    uvicorn.run("weavelens.api.main:app", host=s.api_host, port=s.api_port, reload=False)
