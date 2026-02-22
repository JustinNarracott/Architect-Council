"""
RAG conversational follow-up routes.

POST /api/codebase/{analysis_id}/query
    - Accept { question }
    - Retrieve top-8 relevant chunks from ChromaDB
    - Build prompt with analysis findings + code chunks + user question
    - Stream Claude Opus response via SSE

DELETE /api/codebase/{analysis_id}
    - Manual cleanup of analysis session and RAG index
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import datetime

import litellm
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Import the codebase_routes store so we can read analysis findings context
from backend.api.codebase_routes import _analyses
from backend.indexer.embedder import (
    cleanup_expired_sessions,
    cleanup_session,
    has_session,
    index_repo_for_rag,
    query_chunks,
)

router = APIRouter(prefix="/codebase", tags=["codebase-rag"])

# Model used for query answering
_QUERY_MODEL = "anthropic/claude-opus-4-20250514"

# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_findings_context(analysis_id: str) -> str:
    """Extract the DA Chair synthesis from the completed analysis, if available."""
    entry = _analyses.get(analysis_id)
    if not entry:
        return ""

    crew_result = entry.get("crew_result", "")
    if crew_result:
        return f"## Analysis Findings (DA Chair Synthesis)\n\n{crew_result}"

    return ""


def _build_rag_prompt(
    question: str,
    chunks: list[dict],
    findings_context: str,
) -> str:
    """Construct the full RAG prompt for Claude Opus."""
    chunks_text = "\n\n".join(
        f"### {c['file_path']}:{c['line_start']}-{c['line_end']}"
        f" ({c['chunk_type']})\n```{c['language']}\n{c['content']}\n```"
        for c in chunks
    )

    parts = [
        "You are a senior software architect answering questions about a codebase "
        "that has just been analysed by the Architecture Council.",
        "",
        "Answer the user's question based on the code evidence and analysis findings "
        "provided below. Be specific and cite file paths and line numbers when "
        "referencing code. If the evidence doesn't contain enough information, "
        "say so clearly rather than guessing.",
        "",
    ]

    if findings_context:
        parts += [findings_context, ""]

    parts += [
        "## Relevant Code Excerpts",
        "",
        chunks_text,
        "",
        "---",
        "",
        f"## User Question\n\n{question}",
    ]

    return "\n".join(parts)


# ── Background indexing helper ─────────────────────────────────────────────────


async def ensure_rag_indexed(analysis_id: str) -> bool:
    """
    Ensure the analysis is indexed for RAG. Triggers indexing if not yet done.

    Returns True if the session is (now) available, False otherwise.
    """
    if has_session(analysis_id):
        return True

    entry = _analyses.get(analysis_id)
    if not entry:
        return False

    # Only index completed analyses
    if entry.get("status") not in ("completed", "analysing"):
        return False

    indexed_repo = entry.get("result")
    if not indexed_repo:
        return False

    clone_path = indexed_repo.clone_path
    if not clone_path:
        return False

    # Run blocking embed in executor to avoid blocking event loop
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: index_repo_for_rag(analysis_id, clone_path),
        )
        return True
    except ImportError as exc:
        raise exc  # re-raise so caller can return 503
    except Exception:
        return False


# ── Request / Response models ──────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Request body for POST /api/codebase/{analysis_id}/query."""

    question: str = Field(
        description="Natural language question about the analysed codebase",
        min_length=1,
        max_length=2000,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.post("/{analysis_id}/query")
async def query_codebase(
    analysis_id: str,
    request: QueryRequest,
) -> EventSourceResponse:
    """
    Ask a question about the analysed codebase.

    Retrieves relevant code chunks via vector search, injects analysis findings
    context, and streams a Claude Opus response via SSE.
    """
    # Validate analysis exists
    entry = _analyses.get(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if entry.get("status") not in ("completed", "analysing"):
        raise HTTPException(
            status_code=409,
            detail=f"Analysis is not ready for querying (status: {entry.get('status')})",
        )

    # Ensure RAG index is built
    try:
        indexed = await ensure_rag_indexed(analysis_id)
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG follow-up requires chromadb. "
                f"Install it with: pip install chromadb\n\nDetails: {exc}"
            ),
        ) from exc

    if not indexed:
        raise HTTPException(
            status_code=503,
            detail="Failed to build RAG index for this analysis. Please try again.",
        )

    # Retrieve relevant chunks
    try:
        chunks = query_chunks(analysis_id, request.question)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Build prompt
    findings_context = _get_findings_context(analysis_id)
    prompt = _build_rag_prompt(request.question, chunks, findings_context)

    # Build source attribution (unique file references)
    seen: set[str] = set()
    sources: list[dict] = []
    for c in chunks:
        key = f"{c['file_path']}:{c['line_start']}"
        if key not in seen:
            seen.add(key)
            sources.append({
                "file": c["file_path"],
                "lines": f"{c['line_start']}-{c['line_end']}",
                "type": c["chunk_type"],
                "name": c.get("name", ""),
            })

    # Periodic cleanup on each query (cheap, O(n) over session count)
    cleanup_expired_sessions()

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Stream Claude Opus response token by token."""
        # Emit source attribution first so the UI can display it immediately
        yield {
            "event": "sources",
            "data": json.dumps({"sources": sources}),
        }

        try:
            response = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: litellm.completion(
                    model=_QUERY_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=4096,
                ),
            )

            # litellm streaming returns a generator — iterate synchronously
            # in executor to avoid blocking the event loop
            buffer = []
            for chunk in response:
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None) or ""
                if token:
                    buffer.append(token)

            # Yield collected tokens as one payload
            # (True token-by-token SSE would require async generator from litellm;
            # this collects in executor then yields for simplicity)
            full_text = "".join(buffer)

            # Stream in ~200 char chunks to give the UI a progressive feel
            chunk_size = 200
            for i in range(0, len(full_text), chunk_size):
                yield {
                    "event": "token",
                    "data": json.dumps({"token": full_text[i: i + chunk_size]}),
                }
                await asyncio.sleep(0)  # yield control

        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

        finally:
            yield {
                "event": "done",
                "data": json.dumps({
                    "status": "done",
                    "ts": int(datetime.utcnow().timestamp()),
                }),
            }

    return EventSourceResponse(event_generator())


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str) -> dict:
    """
    Manually clean up an analysis session and its RAG index.

    Frees memory by removing the ChromaDB collection and analysis state.
    """
    if analysis_id not in _analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")

    cleanup_session(analysis_id)
    _analyses.pop(analysis_id, None)

    return {"status": "deleted", "analysis_id": analysis_id}
