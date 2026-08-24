"""PhysioMind AI backend.

Serves the API and the existing static frontend from one process, so there is
one port to run and no CORS configuration for local development.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import CORS_ORIGINS, DEV_MODE, PROJECT_ROOT
from .db import init_db
from .routers import (
    analytics_router, assess_router, auth_router, exercises_router,
    plans_router, reports_router, sessions_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="PhysioMind AI API",
    description=(
        "Backend for the PhysioMind digital physiotherapy app. Pose detection "
        "runs in the browser; only keypoint coordinates reach this server."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    """Never leak a stack trace to a client; the server log keeps the detail."""
    import logging

    logging.getLogger("physio").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if DEV_MODE else "Internal server error"},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "physiomind-api"}


for module in (
    auth_router, exercises_router, assess_router, plans_router,
    sessions_router, analytics_router, reports_router,
):
    app.include_router(module.router)


# --- static frontend --------------------------------------------------------
# Mounted last so /api/* always wins.
@app.get("/")
def index() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "index.html")


app.mount("/", StaticFiles(directory=PROJECT_ROOT, html=True), name="static")
