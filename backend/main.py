"""Main entry point for the Architecture Council backend."""

import os

import uvicorn
from dotenv import load_dotenv

# Load environment variables first — LLM providers need keys at import time
load_dotenv()

# ── LiteLLM configuration (must happen before any agent imports) ──────────────
import litellm  # noqa: E402

# Suppress noisy debug output (apscheduler import errors, etc.)
litellm.suppress_debug_info = True
os.environ.setdefault("LITELLM_LOG", "ERROR")
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.api import router  # noqa: E402

# Create FastAPI app
app = FastAPI(
    title="Architecture Council API",
    description="AI-powered Software Architecture Design Authority - Evaluating architecture decisions with multi-LLM agents",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server (local)
        "http://127.0.0.1:3000",
        "http://localhost:3011",  # Docker-mapped frontend
        "http://127.0.0.1:3011",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": "Architecture Council API",
        "version": "0.1.0",
        "description": "AI-powered Software Architecture Design Authority",
        "docs": "/docs",
        "endpoints": {
            "panel": "/api/panel",
            "review": "/api/review",
            "stream": "/api/stream/{review_id}",
            "rulings": "/api/rulings",
            "tech_radar": "/api/tech-radar",
        },
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


def main() -> None:
    """Run the server."""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
