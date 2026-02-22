"""Main entry point for the Architecture Council backend."""

import os

import uvicorn
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables first — LLM providers need keys at import time
load_dotenv()


class Settings(BaseSettings):
    """Application settings — validated at startup."""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    perplexity_api_key: str = ""
    architect_api_key: str = ""
    cors_allowed_origins: str = "http://localhost:3011"

    class Config:
        env_file = ".env"
        extra = "ignore"


def _validate_settings(settings: Settings) -> None:
    """Warn on missing API keys at startup — don't crash, but be loud."""
    required = {
        "OPENAI_API_KEY": settings.openai_api_key,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "PERPLEXITY_API_KEY": settings.perplexity_api_key,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"⚠️  WARNING: Missing API keys: {', '.join(missing)}")
        print("   Some agents will fail. Set these in your .env file.")


# Validate settings at startup
_settings = Settings()
_validate_settings(_settings)

# ── LiteLLM configuration (must happen before any agent imports) ──────────────
import litellm  # noqa: E402

# Suppress noisy debug output (apscheduler import errors, etc.)
litellm.suppress_debug_info = True
os.environ.setdefault("LITELLM_LOG", "ERROR")
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.api import router  # noqa: E402
from backend.auth import verify_api_key  # noqa: E402

# Create FastAPI app
app = FastAPI(
    title="Architecture Council API",
    description="AI-powered Software Architecture Design Authority - Evaluating architecture decisions with multi-LLM agents",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for frontend
# Read allowed origins from env — default to localhost for dev
_cors_origins_raw = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3011,http://localhost:3000"
)
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,  # Only set True if cookies/sessions needed
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Include API routes with authentication
app.include_router(
    router,
    prefix="/api",
    dependencies=[Depends(verify_api_key)],
)


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
