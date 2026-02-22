"""FastAPI routes for codebase analysis (Sprint 9 — indexing + crew execution + SSE)."""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend.crews.codebase_crew import ROLE_TO_AGENT_ID, create_codebase_crew
from backend.indexer import IndexedRepo, index_local_repo, index_repo
from backend.schemas import AgentMessage, AgentMessageType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codebase", tags=["codebase"])

# In-memory store: analysis_id -> status dict
_analyses: dict[str, dict] = {}
# Per-analysis SSE message queues
_message_queues: dict[str, asyncio.Queue] = {}


# ── Request / Response schemas ────────────────────────────────────────────────

class CodebaseAnalyseRequest(BaseModel):
    """Request body for POST /api/codebase/analyse."""

    repo_url: str | None = Field(
        default=None,
        description="HTTPS URL of the Git repository to analyse",
        examples=["https://github.com/owner/repo"],
    )
    local_path: str | None = Field(
        default=None,
        description="Path to local repo inside /repos/ mount (e.g. /repos/signalbreak)",
    )
    auth_token: str | None = Field(
        default=None,
        description="Optional personal access token for private repositories",
    )


class CodebaseAnalyseResponse(BaseModel):
    """Response body for POST /api/codebase/analyse."""

    analysis_id: str = Field(description="Unique identifier for this analysis run")
    stream_url: str = Field(description="SSE endpoint to stream analysis progress")
    status: str = Field(description="Initial status: 'indexing'")


class CodebaseStatusResponse(BaseModel):
    """Response body for GET /api/codebase/{analysis_id}."""

    analysis_id: str
    repo_url: str
    status: str  # indexing | analysing | completed | failed
    started_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
    result: IndexedRepo | None = None


# ── Error classification ──────────────────────────────────────────────────────

def _classify_error(exc: Exception) -> str:
    """Return a human-readable error message from a clone/index/crew exception."""
    msg = str(exc).lower()
    if "authentication" in msg or "401" in msg:
        return (
            "Authentication failed. "
            "The repository may be private — please provide a valid auth token."
        )
    if "not found" in msg or "404" in msg:
        return "Repository not found. Please check the URL."
    if "timeout" in msg:
        return "Operation timed out. The repository may be too large or the network is slow."
    if "rate" in msg or "429" in msg:
        return (
            "Rate limit exceeded on one or more LLM providers. "
            "Please wait a moment and try again."
        )
    if "auth" in msg or "403" in msg:
        return (
            "LLM API authentication error. "
            "Please check that all API keys are correctly configured."
        )
    return f"Analysis failed: {exc}"


# ── Background task ───────────────────────────────────────────────────────────

async def _run_analysis(
    analysis_id: str,
    repo_url: str | None,
    auth_token: str | None,
    local_path: str | None = None,
) -> None:
    """
    Background task: clone → index → run codebase crew → stream results via SSE.

    Phase 1 (indexing): Clone and map the repository (or map a local path directly).
    Phase 2 (analysing): Run the 5-agent codebase crew with SSE streaming.
    """
    queue = _message_queues.get(analysis_id)
    if not queue:
        return

    async def _emit(agent_id: str, agent_name: str, msg_type: AgentMessageType, content: str) -> None:
        """Push a message onto the SSE queue."""
        await queue.put(
            AgentMessage(
                analysis_id=analysis_id,
                agent_id=agent_id,
                agent_name=agent_name,
                message_type=msg_type,
                content=content,
            )
        )

    # Resolve display URL for status messages and crew inputs
    display_url = local_path if local_path else repo_url

    try:
        # ── Immediate signal: tell the frontend work has begun ─────────────
        # Emitted before any indexing so the sidebar transitions from
        # STANDING BY → EVALUATING without waiting for I/O to complete.
        await _emit(
            "system", "System", AgentMessageType.THINKING,
            f"Starting analysis of {local_path or repo_url}...",
        )

        # ── Phase 1: Indexing ──────────────────────────────────────────────
        if local_path:
            await _emit("system", "System", AgentMessageType.THINKING,
                        f"Indexing local repository: {local_path}...")
        else:
            await _emit("system", "System", AgentMessageType.THINKING,
                        f"Cloning and indexing repository: {repo_url}...")

        try:
            if local_path:
                indexed = await index_local_repo(local_path=local_path)
            else:
                indexed = await index_repo(repo_url=repo_url, auth_token=auth_token)  # type: ignore[arg-type]
        except Exception as e:
            error_msg = _classify_error(e)
            _analyses[analysis_id]["status"] = "failed"
            _analyses[analysis_id]["completed_at"] = datetime.utcnow()
            _analyses[analysis_id]["error"] = error_msg
            await _emit("system", "System", AgentMessageType.ERROR, error_msg)
            return

        _analyses[analysis_id]["result"] = indexed
        _analyses[analysis_id]["status"] = "analysing"

        await _emit(
            "system", "System", AgentMessageType.THINKING,
            (
                f"Repository indexed: {indexed.total_files} files, "
                f"~{indexed.total_loc:,} LOC. Starting specialist analysis..."
            ),
        )

        # ── Phase 2: Crew Execution ────────────────────────────────────────
        # Emit "thinking" for all specialist agents upfront
        specialist_ids = [
            ("standards_analyst", "Standards Analyst"),
            ("dx_analyst", "DX Analyst"),
            ("enterprise_architect", "Enterprise Architect"),
            ("security_analyst", "Security & Resilience Analyst"),
        ]
        for agent_id, agent_name in specialist_ids:
            await _emit(agent_id, agent_name, AgentMessageType.THINKING,
                        f"{agent_name} is analysing the codebase...")

        await _emit("da_chair", "DA Chair", AgentMessageType.THINKING,
                    "Awaiting specialist assessments before synthesis...")

        # Capture event loop before entering the executor thread.
        # The task callback runs in the executor (sync) thread and needs
        # call_soon_threadsafe to push messages onto the async queue.
        _event_loop = asyncio.get_running_loop()

        def on_task_complete(task_output) -> None:
            """Called by CrewAI when each task finishes (from executor thread)."""
            try:
                agent_role = getattr(task_output, "agent", None)
                role_str = str(agent_role) if agent_role else "Unknown"

                agent_id = ROLE_TO_AGENT_ID.get(role_str, "system")
                agent_name = role_str
                raw_output = getattr(task_output, "raw", str(task_output))

                # Log and inject fallback if any agent returns empty/minimal output
                content_len = len(raw_output.strip()) if raw_output else 0
                if content_len < 50:
                    logger.warning(
                        "Agent %s returned empty/minimal output (%d chars)",
                        agent_id,
                        content_len,
                    )

                # Safety net: inject structured fallback for security_analyst empty output
                if agent_id == "security_analyst" and content_len < 50:
                    raw_output = (
                        "# Security & Resilience Report\n\n"
                        "## Score\n\n"
                        "| Metric | Value |\n"
                        "|--------|-------|\n"
                        "| **Score** | N/A |\n"
                        "| **Rating** | UNKNOWN |\n"
                        "| **Confidence** | none |\n\n"
                        "⚠️ **The Security Analyst did not produce a report for this repository.**\n\n"
                        "This may be due to:\n"
                        "- Repository size exceeding analysis capacity\n"
                        "- Tool execution timeout on large codebases\n"
                        "- Model output error\n\n"
                        "**Recommendation:** Re-run the review or check backend logs for errors.\n"
                    )

                msg_type = (
                    AgentMessageType.RULING
                    if agent_id == "da_chair"
                    else AgentMessageType.ANALYSIS
                )

                msg = AgentMessage(
                    analysis_id=analysis_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    message_type=msg_type,
                    content=raw_output,
                )
                _event_loop.call_soon_threadsafe(queue.put_nowait, msg)
            except Exception as cb_err:
                logger.error("[codebase_routes] task callback error: %s", cb_err)

        # Create and run the codebase crew
        try:
            crew = create_codebase_crew(
                repo_url=display_url or "",
                clone_path=indexed.clone_path,
                repo_metadata=indexed,
                task_callback=on_task_complete,
            )
        except (ValueError, Exception) as e:
            error_msg = (
                f"Crew configuration error: {e}\n\n"
                "Please check that all required API keys are set:\n"
                "- OPENAI_API_KEY (Standards Analyst)\n"
                "- PERPLEXITY_API_KEY (DX Analyst)\n"
                "- ANTHROPIC_API_KEY (Enterprise Architect & DA Chair)\n"
                "- OLLAMA_API_BASE (Security Analyst — local Ollama)"
            )
            _analyses[analysis_id]["status"] = "failed"
            _analyses[analysis_id]["completed_at"] = datetime.utcnow()
            _analyses[analysis_id]["error"] = error_msg
            await _emit("system", "System", AgentMessageType.ERROR, error_msg)
            return

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: crew.kickoff(
                    inputs={
                        "repo_url": display_url or "",
                        "clone_path": indexed.clone_path,
                    }
                ),
            )

            _analyses[analysis_id]["status"] = "completed"
            _analyses[analysis_id]["completed_at"] = datetime.utcnow()
            _analyses[analysis_id]["crew_result"] = result.raw

        except TimeoutError:
            error_msg = (
                "Codebase analysis timed out. One or more agents did not respond in time.\n"
                "This may indicate rate limiting from an LLM provider. Please try again."
            )
            _analyses[analysis_id]["status"] = "failed"
            _analyses[analysis_id]["completed_at"] = datetime.utcnow()
            _analyses[analysis_id]["error"] = error_msg
            await _emit("system", "System", AgentMessageType.ERROR, error_msg)

        except Exception as e:
            error_msg = _classify_error(e)
            _analyses[analysis_id]["status"] = "failed"
            _analyses[analysis_id]["completed_at"] = datetime.utcnow()
            _analyses[analysis_id]["error"] = error_msg
            await _emit("system", "System", AgentMessageType.ERROR, error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during codebase analysis: {e}"
        _analyses[analysis_id]["status"] = "failed"
        _analyses[analysis_id]["completed_at"] = datetime.utcnow()
        _analyses[analysis_id]["error"] = error_msg
        await _emit("system", "System", AgentMessageType.ERROR, error_msg)

    finally:
        # None sentinel signals end-of-stream to the SSE generator
        await queue.put(None)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/local-repos", response_model=list[str])
async def list_local_repos() -> list[str]:
    """List available project directories from the /repos volume mount."""
    repos_root = Path("/repos")
    if not repos_root.exists():
        return []
    dirs = sorted([
        d.name for d in repos_root.iterdir()
        if d.is_dir() and not d.name.startswith('.')
    ])
    return dirs


@router.post("/analyse", response_model=CodebaseAnalyseResponse)
async def analyse_codebase(
    request: CodebaseAnalyseRequest,
    background_tasks: BackgroundTasks,
) -> CodebaseAnalyseResponse:
    """
    Submit a repository for codebase analysis.

    Accepts either a ``repo_url`` (HTTPS Git URL) or a ``local_path``
    (path inside the /repos/ volume mount).  Exactly one must be provided.

    Triggers background indexing and 5-agent crew execution.
    Connect to stream_url via SSE to receive live agent output.
    """
    # Exactly one of repo_url / local_path must be supplied
    if request.repo_url and request.local_path:
        raise HTTPException(
            status_code=422,
            detail="Provide either repo_url or local_path, not both",
        )
    if not request.repo_url and not request.local_path:
        raise HTTPException(
            status_code=422,
            detail="Either repo_url or local_path must be provided",
        )

    if request.repo_url and not request.repo_url.startswith("http"):
        raise HTTPException(
            status_code=422,
            detail="repo_url must be a valid HTTPS URL",
        )

    if request.local_path:
        if not request.local_path.startswith("/repos/"):
            raise HTTPException(
                status_code=422,
                detail="local_path must start with /repos/",
            )
        import os
        if not os.path.isdir(request.local_path):
            raise HTTPException(
                status_code=422,
                detail=f"Local path not found on disk: {request.local_path}",
            )

    analysis_id = str(uuid.uuid4())
    display_url = request.local_path if request.local_path else request.repo_url

    _analyses[analysis_id] = {
        "analysis_id": analysis_id,
        "repo_url": display_url,
        "status": "indexing",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "error": None,
        "result": None,
        "crew_result": None,
    }
    _message_queues[analysis_id] = asyncio.Queue()

    background_tasks.add_task(
        _run_analysis,
        analysis_id,
        request.repo_url,
        request.auth_token,
        request.local_path,
    )

    return CodebaseAnalyseResponse(
        analysis_id=analysis_id,
        stream_url=f"/api/codebase/stream/{analysis_id}",
        status="indexing",
    )


@router.get("/stream/{analysis_id}")
async def stream_analysis(analysis_id: str) -> EventSourceResponse:
    """
    Stream codebase analysis messages via Server-Sent Events.

    Each event contains an AgentMessage with the agent's analysis or synthesis.
    Sends periodic heartbeats every 15s to prevent proxy/load-balancer timeouts.
    """
    if analysis_id not in _analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        queue = _message_queues.get(analysis_id)
        if not queue:
            return

        HEARTBEAT_INTERVAL = 15   # seconds between keepalive pings
        TOTAL_TIMEOUT = 900       # 15 minutes — codebase reviews take longer than ADR reviews

        deadline = asyncio.get_event_loop().time() + TOTAL_TIMEOUT

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                yield {"event": "timeout", "data": '{"status": "timeout"}'}
                break

            try:
                wait_time = min(HEARTBEAT_INTERVAL, remaining)
                message = await asyncio.wait_for(queue.get(), timeout=wait_time)

                if message is None:
                    # None sentinel = end of stream
                    yield {"event": "complete", "data": '{"status": "completed"}'}
                    break

                yield {"event": "message", "data": message.model_dump_json()}

            except asyncio.TimeoutError:
                # No message arrived in HEARTBEAT_INTERVAL — send keepalive
                yield {
                    "event": "heartbeat",
                    "data": '{"ts": ' + str(int(datetime.utcnow().timestamp())) + '}',
                }

    return EventSourceResponse(event_generator())


@router.get("/{analysis_id}", response_model=CodebaseStatusResponse)
async def get_analysis(analysis_id: str) -> CodebaseStatusResponse:
    """
    Get the current status and result of a codebase analysis.

    Poll this endpoint or connect to the SSE stream for live updates.
    """
    entry = _analyses.get(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return CodebaseStatusResponse(
        analysis_id=entry["analysis_id"],
        repo_url=entry["repo_url"],
        status=entry["status"],
        started_at=entry["started_at"],
        completed_at=entry.get("completed_at"),
        error=entry.get("error"),
        result=entry.get("result"),
    )
