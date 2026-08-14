"""FastAPI entrypoint: scoring API + React SPA static files."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.lib.databricks import ENDPOINTS
from server.routes.lookup import router as lookup_router
from server.routes.score import router as score_router

app = FastAPI(
    title="Risk & Propensity Models",
    description="Customer lookup plus live scoring for churn, deposit propensity, and fraud.",
    version="1.1.0",
)

app.include_router(score_router)
app.include_router(lookup_router)

CLIENT_DIST = Path(__file__).resolve().parent / "client" / "dist"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "endpoints": ENDPOINTS}


@app.get("/api/config")
def config() -> dict:
    return {
        "auth": "oauth_app_service_principal",
        "endpoints": ENDPOINTS,
    }


if CLIENT_DIST.is_dir():
    assets_dir = CLIENT_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str = "") -> FileResponse:
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = CLIENT_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(CLIENT_DIST / "index.html")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("DATABRICKS_APP_PORT", os.environ.get("PORT", "8000")))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
