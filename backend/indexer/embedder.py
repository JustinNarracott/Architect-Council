"""
Embed code chunks and store in ChromaDB for per-session RAG retrieval.

One ChromaDB collection per analysis_id.
Uses OpenAI text-embedding-3-small via litellm (cheap and fast).

ChromaDB is an optional dependency — if not installed, all public functions
raise a helpful ImportError rather than crashing at module load time.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .chunker import CodeChunk, chunk_repo

if TYPE_CHECKING:
    # Type hints only — not imported at runtime unless chromadb is present
    import chromadb  # noqa: F401

# ── Availability check ────────────────────────────────────────────────────────

try:
    import chromadb as _chromadb  # noqa: F401
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False


def _require_chromadb() -> None:
    if not _CHROMA_AVAILABLE:
        raise ImportError(
            "chromadb is not installed. "
            "Install it with: pip install chromadb\n"
            "Or add 'chromadb' to your pyproject.toml dependencies."
        )


# ── Session store ─────────────────────────────────────────────────────────────

@dataclass
class EmbeddedSession:
    """Holds the ChromaDB collection and metadata for one analysis session."""

    analysis_id: str
    collection_name: str
    chunk_count: int
    created_at: float = field(default_factory=time.time)
    ttl_seconds: float = 3600.0  # 1 hour default

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds


# In-memory registry: analysis_id -> EmbeddedSession
_sessions: dict[str, EmbeddedSession] = {}

# Single shared in-memory ChromaDB client (lazy-initialised)
_chroma_client = None


def _get_chroma_client():
    """Return (and lazily create) the shared in-memory ChromaDB client."""
    global _chroma_client
    _require_chromadb()
    if _chroma_client is None:
        import chromadb as chromadb_mod
        _chroma_client = chromadb_mod.Client()  # ephemeral in-memory
    return _chroma_client


# ── Embedding helper ──────────────────────────────────────────────────────────

_MAX_EMBED_CHARS = 28_000  # ~7 000 tokens — safe margin for 8 192 limit


def _truncate(text: str, max_chars: int = _MAX_EMBED_CHARS) -> str:
    """Truncate text to stay within embedding model token limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings using OpenAI text-embedding-3-small via litellm.

    Truncates oversized inputs and batches to 20 at a time to stay within
    per-request token limits.
    """
    import litellm

    embeddings: list[list[float]] = []
    batch_size = 20  # smaller batches to avoid aggregate token overflow

    for i in range(0, len(texts), batch_size):
        batch = [_truncate(t) for t in texts[i: i + batch_size]]
        response = litellm.embedding(
            model="text-embedding-3-small",
            input=batch,
        )
        for item in response.data:
            embeddings.append(item["embedding"])

    return embeddings


def _chunk_id(chunk: CodeChunk) -> str:
    """Stable ID for a chunk based on its file path and line range."""
    raw = f"{chunk.file_path}:{chunk.line_start}:{chunk.line_end}"
    return hashlib.md5(raw.encode()).hexdigest()


# ── Public API ────────────────────────────────────────────────────────────────

def index_repo_for_rag(
    analysis_id: str,
    repo_root: Path | str,
    ttl_seconds: float = 3600.0,
) -> EmbeddedSession:
    """
    Chunk, embed, and store a cloned repository in ChromaDB.

    Args:
        analysis_id: Unique identifier for this analysis (used as collection name).
        repo_root:   Absolute path to the cloned repository.
        ttl_seconds: How long to keep the session alive (default 1 hour).

    Returns:
        :class:`EmbeddedSession` describing the indexed collection.

    Raises:
        ImportError: If chromadb is not installed.
    """
    _require_chromadb()
    repo_root = Path(repo_root)

    # Chunk the repo
    chunks = chunk_repo(repo_root)
    if not chunks:
        raise ValueError(f"No chunks produced from {repo_root}")

    # Build collection (replace if already exists for this analysis_id)
    client = _get_chroma_client()
    collection_name = f"repo_{analysis_id[:16]}"  # ChromaDB name length limit

    # Delete old collection if it exists
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Embed in batches
    texts = [c.as_embed_text() for c in chunks]
    ids = [_chunk_id(c) for c in chunks]
    metadatas = [c.as_dict() for c in chunks]

    embeddings = _embed_texts(texts)

    # Upsert into ChromaDB
    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i: i + batch_size],
            embeddings=embeddings[i: i + batch_size],
            documents=texts[i: i + batch_size],
            metadatas=metadatas[i: i + batch_size],
        )

    session = EmbeddedSession(
        analysis_id=analysis_id,
        collection_name=collection_name,
        chunk_count=len(chunks),
        ttl_seconds=ttl_seconds,
    )
    _sessions[analysis_id] = session
    return session


def query_chunks(
    analysis_id: str,
    question: str,
    n_results: int = 8,
) -> list[dict]:
    """
    Retrieve the top-N most relevant chunks for a question.

    Args:
        analysis_id: The session to query.
        question:    Natural language question from the user.
        n_results:   How many chunks to retrieve (default 8).

    Returns:
        List of chunk dicts (as_dict() + 'document' key for the embed text).

    Raises:
        KeyError:    If the analysis_id session is not found.
        ImportError: If chromadb is not installed.
    """
    _require_chromadb()

    session = _sessions.get(analysis_id)
    if not session:
        raise KeyError(f"No RAG session found for analysis_id={analysis_id!r}")

    if session.is_expired():
        cleanup_session(analysis_id)
        raise KeyError(f"RAG session for {analysis_id!r} has expired")

    client = _get_chroma_client()
    collection = client.get_collection(session.collection_name)

    # Embed the question
    q_embeddings = _embed_texts([question])

    results = collection.query(
        query_embeddings=q_embeddings,
        n_results=min(n_results, session.chunk_count),
        include=["documents", "metadatas", "distances"],
    )

    chunks_out: list[dict] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        entry = dict(meta)
        entry["document"] = doc
        entry["relevance_score"] = round(1.0 - dist, 4)  # cosine: 1=identical
        chunks_out.append(entry)

    return chunks_out


def has_session(analysis_id: str) -> bool:
    """Return True if a live (non-expired) RAG session exists."""
    session = _sessions.get(analysis_id)
    if not session:
        return False
    if session.is_expired():
        cleanup_session(analysis_id)
        return False
    return True


def cleanup_session(analysis_id: str) -> None:
    """Delete the ChromaDB collection and remove the session from the registry."""
    session = _sessions.pop(analysis_id, None)
    if not session:
        return

    if not _CHROMA_AVAILABLE:
        return

    try:
        client = _get_chroma_client()
        client.delete_collection(session.collection_name)
    except Exception:
        pass  # Best-effort cleanup


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions. Returns count of sessions removed."""
    expired = [aid for aid, s in _sessions.items() if s.is_expired()]
    for aid in expired:
        cleanup_session(aid)
    return len(expired)


__all__ = [
    "EmbeddedSession",
    "index_repo_for_rag",
    "query_chunks",
    "has_session",
    "cleanup_session",
    "cleanup_expired_sessions",
]
