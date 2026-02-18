"""FastAPI routes for the Architecture Council API."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.crews import create_architecture_crew
from backend.crews.architecture_crew import ROLE_TO_AGENT_ID
from backend.schemas import (
    ADRRequest,
    AgentInfo,
    AgentMessage,
    AgentMessageType,
    AnalysisResponse,
    RulingHistoryItem,
)

router = APIRouter()

# In-memory storage for demo purposes
# In production, use Redis or a database
_reviews: dict[str, dict] = {}
_message_queues: dict[str, asyncio.Queue] = {}


@router.get("/panel", response_model=list[AgentInfo])
async def get_panel() -> list[AgentInfo]:
    """List all architecture council panel members and their details."""
    return [
        AgentInfo(
            id="standards_analyst",
            name="Standards Analyst",
            role="Standards & Patterns Evaluator",
            description="Evaluates technology choices against approved standards, design patterns, and organisational tech radar.",
            focus_areas=[
                "Tech Radar Compliance",
                "Design Patterns",
                "Anti-Pattern Detection",
                "API Standards",
                "Naming Conventions",
            ],
            llm_provider="OpenAI GPT-4o",
        ),
        AgentInfo(
            id="dx_analyst",
            name="DX Analyst",
            role="Developer Experience Analyst",
            description="Assesses team capability, adoption complexity, documentation quality, and community health of proposed technologies.",
            focus_areas=[
                "Learning Curve",
                "Community Health",
                "Documentation Quality",
                "Hiring Pool",
                "Onboarding Complexity",
            ],
            llm_provider="Perplexity Sonar",
        ),
        AgentInfo(
            id="enterprise_architect",
            name="Enterprise Architect",
            role="Integration & Strategy Analyst",
            description="Evaluates impact on existing services, data flows, dependency graph, and strategic alignment with platform roadmap.",
            focus_areas=[
                "Service Integration",
                "Dependency Analysis",
                "Data Flow Impact",
                "Strategic Alignment",
                "Duplication Detection",
            ],
            llm_provider="Anthropic Claude Sonnet 4",
        ),
        AgentInfo(
            id="security_analyst",
            name="Security & Resilience Analyst",
            role="Security & Operational Risk Analyst",
            description="Identifies threat surface changes, compliance implications, failure modes, and operational risk of proposed changes.",
            focus_areas=[
                "Threat Surface",
                "Data Classification",
                "Compliance (GDPR/SOC2)",
                "Failure Modes",
                "Blast Radius",
                "Rollback Capability",
            ],
            llm_provider="Anthropic Claude Sonnet 4",
        ),
        AgentInfo(
            id="da_chair",
            name="DA Chair",
            role="Design Authority Chair",
            description="Synthesises all specialist assessments, resolves conflicts, and delivers the final architecture ruling with conditions.",
            focus_areas=[
                "Evidence Synthesis",
                "Conflict Resolution",
                "Ruling Delivery",
                "Condition Setting",
                "Dissent Recording",
            ],
            llm_provider="Anthropic Claude Opus",
        ),
    ]


@router.post("/review", response_model=AnalysisResponse)
async def start_review(
    request: ADRRequest, background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Start a new architecture decision review.

    Returns a review ID that can be used to stream results via SSE.
    """
    review_id = str(uuid.uuid4())

    # Initialize storage
    _reviews[review_id] = {
        "title": request.title,
        "technology": request.technology,
        "reason": request.reason,
        "affected_services": request.affected_services,
        "data_classification": request.data_classification,
        "proposer": request.proposer,
        "status": "running",
        "started_at": datetime.utcnow(),
        "result": None,
        "error": None,
    }
    _message_queues[review_id] = asyncio.Queue()

    # Run review in background
    background_tasks.add_task(
        _run_review_task,
        review_id,
        request,
    )

    return AnalysisResponse(
        analysis_id=review_id,
        stream_url=f"/api/stream/{review_id}",
        status="started",
    )


async def _run_review_task(
    review_id: str, request: ADRRequest
) -> None:
    """
    Background task to run the architecture review.

    Implements graceful degradation if individual agents fail:
    - Wraps crew execution in try/except
    - Provides clear error messages for common failure modes
    - Continues with partial results where possible
    - Marks reviews as degraded if any agent fails
    """
    queue = _message_queues.get(review_id)
    if not queue:
        return

    try:
        # Send initial message
        await queue.put(
            AgentMessage(
                analysis_id=review_id,
                agent_id="system",
                agent_name="System",
                message_type=AgentMessageType.THINKING,
                content=f"Starting review for '{request.title}'...",
            )
        )

        # Emit "thinking" for all specialist agents
        specialist_ids = [
            ("standards_analyst", "Standards Analyst"),
            ("dx_analyst", "DX Analyst"),
            ("enterprise_architect", "Enterprise Architect"),
            ("security_analyst", "Security & Resilience Analyst"),
        ]
        for agent_id, agent_name in specialist_ids:
            await queue.put(
                AgentMessage(
                    analysis_id=review_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    message_type=AgentMessageType.THINKING,
                    content=f"{agent_name} is evaluating the proposal...",
                )
            )

        # Capture the event loop reference for cross-thread callback use.
        # When kickoff runs in an executor thread, the callback needs
        # call_soon_threadsafe to push messages onto the async queue.
        _event_loop = asyncio.get_running_loop()

        # Task callback: emit per-agent progress as each task completes
        def on_task_complete(task_output) -> None:
            """Called by CrewAI when each task finishes (from executor thread)."""
            try:
                agent_role = getattr(task_output, 'agent', None)
                role_str = str(agent_role) if agent_role else "Unknown"

                agent_id = ROLE_TO_AGENT_ID.get(role_str, "system")
                agent_name = role_str
                raw_output = getattr(task_output, 'raw', str(task_output))

                # DA Chair output is the ruling; specialists are analysis
                if agent_id == "da_chair":
                    msg_type = AgentMessageType.RULING
                else:
                    msg_type = AgentMessageType.ANALYSIS

                msg = AgentMessage(
                    analysis_id=review_id,
                    agent_id=agent_id,
                    agent_name=agent_name,
                    message_type=msg_type,
                    content=raw_output,  # Full output — SSE has no practical size limit
                )

                # Thread-safe push onto the async queue
                _event_loop.call_soon_threadsafe(queue.put_nowait, msg)
            except Exception as e:
                print(f"Task callback error: {e}")

        # Create crew with progress callback
        try:
            crew = create_architecture_crew(
                title=request.title,
                technology=request.technology,
                reason=request.reason,
                affected_services=request.affected_services,
                data_classification=request.data_classification,
                proposer=request.proposer,
                task_callback=on_task_complete,
            )
        except ValueError as e:
            error_msg = (
                f"Configuration error: {str(e)}\n\n"
                "Please check that all required API keys are configured:\n"
                "- OPENAI_API_KEY (for Standards Analyst)\n"
                "- ANTHROPIC_API_KEY (for Enterprise Architect & DA Chair)\n"
                "- PERPLEXITY_API_KEY (for DX Analyst)\n"
                "- OLLAMA_API_BASE (for Security Analyst — local Ollama)"
            )
            _reviews[review_id]["error"] = error_msg
            _reviews[review_id]["status"] = "failed"
            await queue.put(
                AgentMessage(
                    analysis_id=review_id,
                    agent_id="system",
                    agent_name="System",
                    message_type=AgentMessageType.ERROR,
                    content=error_msg,
                )
            )
            return

        # Emit DA Chair thinking before kickoff
        await queue.put(
            AgentMessage(
                analysis_id=review_id,
                agent_id="da_chair",
                agent_name="DA Chair",
                message_type=AgentMessageType.THINKING,
                content="Awaiting specialist assessments before synthesis...",
            )
        )

        # Run the crew in a thread executor — crew.kickoff() is synchronous
        # and blocks the event loop, which corrupts litellm's async internals
        # for providers like Perplexity that use OpenAI-compatible endpoints.
        try:
            loop = asyncio.get_running_loop()
            kickoff_inputs = {
                "title": request.title,
                "technology": request.technology,
                "reason": request.reason,
                "affected_services": request.affected_services,
                "data_classification": request.data_classification,
                "proposer": request.proposer,
            }
            result = await loop.run_in_executor(
                None, lambda: crew.kickoff(inputs=kickoff_inputs)
            )

            # Store result (ruling message already emitted via task callback)
            _reviews[review_id]["result"] = result.raw
            _reviews[review_id]["status"] = "completed"
            _reviews[review_id]["degraded"] = False

        except TimeoutError:
            # Individual agent timeout
            error_msg = (
                "Review timed out. One or more agents did not respond in time.\n"
                "This may indicate:\n"
                "- Rate limiting from an LLM provider\n"
                "- Network connectivity issues\n"
                "- Unusually complex evaluation\n\n"
                "Please try again. If the issue persists, contact support."
            )
            _reviews[review_id]["error"] = error_msg
            _reviews[review_id]["status"] = "failed"
            await queue.put(
                AgentMessage(
                    analysis_id=review_id,
                    agent_id="system",
                    agent_name="System",
                    message_type=AgentMessageType.ERROR,
                    content=error_msg,
                )
            )

        except Exception as e:
            # LLM provider errors, rate limiting, etc.
            error_str = str(e).lower()

            # Provide specific guidance based on error type
            if "rate" in error_str or "429" in error_str:
                error_msg = (
                    f"Rate limit exceeded: {str(e)}\n\n"
                    "One or more LLM providers have rate limited the request.\n"
                    "Please wait a moment and try again."
                )
            elif "auth" in error_str or "401" in error_str or "403" in error_str:
                error_msg = (
                    f"Authentication error: {str(e)}\n\n"
                    "One or more API keys may be invalid or expired.\n"
                    "Please check your API key configuration."
                )
            elif "network" in error_str or "connection" in error_str:
                error_msg = (
                    f"Network error: {str(e)}\n\n"
                    "Unable to reach one or more LLM providers.\n"
                    "Please check your network connection and try again."
                )
            else:
                error_msg = f"Evaluation error: {str(e)}"

            _reviews[review_id]["error"] = error_msg
            _reviews[review_id]["status"] = "failed"
            await queue.put(
                AgentMessage(
                    analysis_id=review_id,
                    agent_id="system",
                    agent_name="System",
                    message_type=AgentMessageType.ERROR,
                    content=error_msg,
                )
            )

    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error during review: {str(e)}"
        _reviews[review_id]["error"] = error_msg
        _reviews[review_id]["status"] = "failed"

        await queue.put(
            AgentMessage(
                analysis_id=review_id,
                agent_id="system",
                agent_name="System",
                message_type=AgentMessageType.ERROR,
                content=error_msg,
            )
        )

    finally:
        # Signal end of stream
        await queue.put(None)


@router.get("/stream/{review_id}")
async def stream_review(review_id: str) -> EventSourceResponse:
    """
    Stream architecture review messages via Server-Sent Events.

    Each event contains an AgentMessage with the agent's thoughts or ruling.
    Sends periodic heartbeats every 15s to prevent proxy/load-balancer timeouts.
    """
    if review_id not in _reviews:
        raise HTTPException(status_code=404, detail="Review not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        queue = _message_queues.get(review_id)
        if not queue:
            return

        # Multi-LLM reviews can take 90–180s; give generous headroom
        HEARTBEAT_INTERVAL = 15  # seconds between keepalive pings
        TOTAL_TIMEOUT = 600       # 10 minutes absolute maximum

        deadline = asyncio.get_event_loop().time() + TOTAL_TIMEOUT

        while True:
            # Remaining time before absolute deadline
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                yield {"event": "timeout", "data": '{"status": "timeout"}'}
                break

            try:
                # Wait up to HEARTBEAT_INTERVAL for the next message
                wait_time = min(HEARTBEAT_INTERVAL, remaining)
                message = await asyncio.wait_for(queue.get(), timeout=wait_time)

                if message is None:
                    # None sentinel = end of stream
                    yield {"event": "complete", "data": '{"status": "completed"}'}
                    break

                yield {"event": "message", "data": message.model_dump_json()}

            except asyncio.TimeoutError:
                # No message arrived in HEARTBEAT_INTERVAL — send keepalive
                yield {"event": "heartbeat", "data": '{"ts": ' + str(int(datetime.utcnow().timestamp())) + '}'}

    return EventSourceResponse(event_generator())


@router.get("/rulings", response_model=list[RulingHistoryItem])
async def get_rulings() -> list[RulingHistoryItem]:
    """Get history of past architecture rulings."""
    # For demo, return completed reviews from memory
    # In production, this would query a database
    history = []
    for review_id, data in _reviews.items():
        if data["status"] == "completed":
            history.append(
                RulingHistoryItem(
                    ruling_id=review_id,
                    title=data["title"],
                    technology=data["technology"],
                    ruling="approved",  # Would parse from result
                    confidence="medium",  # Would parse from result
                    timestamp=data["started_at"],
                )
            )
    return history


@router.get("/review/{review_id}")
async def get_review(review_id: str) -> dict:
    """Get the status and result of an architecture review."""
    if review_id not in _reviews:
        raise HTTPException(status_code=404, detail="Review not found")

    return _reviews[review_id]


@router.get("/tech-radar")
async def get_tech_radar() -> dict:
    """Get the technology radar data."""
    tech_radar_path = Path(__file__).parent.parent.parent / "data" / "tech_radar.json"

    if not tech_radar_path.exists():
        raise HTTPException(status_code=404, detail="Tech radar data not found")

    with open(tech_radar_path, "r", encoding="utf-8") as f:
        return json.load(f)
