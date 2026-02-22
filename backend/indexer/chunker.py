"""
Chunk repository files for embedding in RAG follow-up queries.

Strategy:
- Python: AST-aware chunking by function / class
- TypeScript/JS: regex split on function/class/export declarations
- Fallback: sliding window (50 lines, 10-line overlap)

Skips binary files, images, node_modules, .git, and other irrelevant dirs.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Skip lists ────────────────────────────────────────────────────────────────

SKIP_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "__pycache__",
    ".venv", "venv", "env", "vendor", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "eggs", "*.egg-info",
}

SKIP_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".tiff",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
    # Compiled / binary
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".wasm",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Media
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".pdf",
    # Lock files (large, low value)
    ".lock",
}

# Lock-file names to skip even without extension match
SKIP_FILENAMES = {"uv.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

MAX_FILE_BYTES = 500_000  # 500 KB hard ceiling per file
MAX_CHUNK_LINES = 120     # Split AST chunks larger than this into windows
WINDOW_SIZE = 50          # lines per sliding-window chunk
WINDOW_OVERLAP = 10       # lines overlap between consecutive windows


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class CodeChunk:
    """A single embeddable unit of source code."""

    file_path: str        # relative path from repo root
    language: str         # python | typescript | javascript | text | …
    chunk_type: str       # function | class | module | window
    name: str             # symbol name or empty string
    content: str          # source text
    line_start: int
    line_end: int
    metadata: dict = field(default_factory=dict)

    def as_embed_text(self) -> str:
        """Return the text to be embedded (path + content)."""
        return f"# {self.file_path}:{self.line_start}-{self.line_end}\n{self.content}"

    def as_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


def _split_if_oversized(chunk: CodeChunk) -> list[CodeChunk]:
    """Split a chunk into sliding windows if it exceeds MAX_CHUNK_LINES."""
    chunk_lines = chunk.content.splitlines()
    if len(chunk_lines) <= MAX_CHUNK_LINES:
        return [chunk]

    # Re-chunk using sliding window, preserving metadata
    windows: list[CodeChunk] = []
    step = WINDOW_SIZE - WINDOW_OVERLAP
    i = 0
    while i < len(chunk_lines):
        end = min(i + WINDOW_SIZE, len(chunk_lines))
        content = "\n".join(chunk_lines[i:end])
        if content.strip():
            windows.append(CodeChunk(
                file_path=chunk.file_path,
                language=chunk.language,
                chunk_type=chunk.chunk_type,
                name=chunk.name,
                content=content,
                line_start=chunk.line_start + i,
                line_end=chunk.line_start + end - 1,
            ))
        i += step
    return windows


# ── Language detection ────────────────────────────────────────────────────────

_EXT_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".sh": "shell",
    ".bash": "shell",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".mdx": "markdown",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
}


def _detect_language(path: Path) -> str:
    return _EXT_TO_LANG.get(path.suffix.lower(), "text")


# ── Python chunker ────────────────────────────────────────────────────────────

def _chunk_python(source: str, rel_path: str) -> list[CodeChunk]:
    """Chunk Python source by top-level functions and classes using AST."""
    chunks: list[CodeChunk] = []
    lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fall back to sliding window on parse failure
        return _sliding_window(lines, rel_path, "python")

    top_nodes = [
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not any(
            isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for parent in ast.walk(tree)
            if n in ast.walk(parent) and parent is not n
        )
    ]

    # ast.walk doesn't preserve parent info; use a simpler top-level check
    top_nodes = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]

    covered_lines: set[int] = set()

    for node in top_nodes:
        line_start = node.lineno
        line_end = getattr(node, "end_lineno", node.lineno)
        chunk_lines = lines[line_start - 1: line_end]
        content = "\n".join(chunk_lines)
        chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"

        chunks.append(CodeChunk(
            file_path=rel_path,
            language="python",
            chunk_type=chunk_type,
            name=node.name,
            content=content,
            line_start=line_start,
            line_end=line_end,
        ))
        covered_lines.update(range(line_start, line_end + 1))

    # Emit module-level code that isn't inside any function/class
    module_lines = [
        (i + 1, line) for i, line in enumerate(lines)
        if (i + 1) not in covered_lines and line.strip()
    ]
    if module_lines:
        # Group consecutive module lines into windows
        groups: list[list[tuple[int, str]]] = []
        current: list[tuple[int, str]] = [module_lines[0]]
        for prev, cur in zip(module_lines, module_lines[1:]):
            if cur[0] - prev[0] <= 3:
                current.append(cur)
            else:
                groups.append(current)
                current = [cur]
        groups.append(current)

        for grp in groups:
            if not grp:
                continue
            content = "\n".join(ln for _, ln in grp)
            chunks.append(CodeChunk(
                file_path=rel_path,
                language="python",
                chunk_type="module",
                name="",
                content=content,
                line_start=grp[0][0],
                line_end=grp[-1][0],
            ))

    return chunks or _sliding_window(lines, rel_path, "python")


# ── TypeScript/JavaScript chunker ─────────────────────────────────────────────

# Regex patterns that signal the start of a named block
_TS_BLOCK_RE = re.compile(
    r"^(?:export\s+(?:default\s+)?)?(?:"
    r"(?:async\s+)?function\s+(\w+)"           # function foo
    r"|class\s+(\w+)"                           # class Foo
    r"|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\("  # const foo = (
    r"|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function"  # const foo = function
    r")",
    re.MULTILINE,
)


def _chunk_typescript(source: str, rel_path: str, language: str) -> list[CodeChunk]:
    """Chunk TypeScript/JavaScript by function/class declarations using regex."""
    lines = source.splitlines()
    if len(lines) <= WINDOW_SIZE:
        return [CodeChunk(
            file_path=rel_path,
            language=language,
            chunk_type="module",
            name="",
            content=source,
            line_start=1,
            line_end=len(lines),
        )]

    # Find declaration start lines
    starts: list[tuple[int, str]] = []  # (1-indexed line, symbol name)
    for m in _TS_BLOCK_RE.finditer(source):
        name = next(g for g in m.groups() if g) if any(m.groups()) else ""
        # Convert char offset to line number
        line_no = source[: m.start()].count("\n") + 1
        starts.append((line_no, name))

    if not starts:
        return _sliding_window(lines, rel_path, language)

    chunks: list[CodeChunk] = []
    for idx, (line_start, name) in enumerate(starts):
        line_end = starts[idx + 1][0] - 1 if idx + 1 < len(starts) else len(lines)
        content = "\n".join(lines[line_start - 1: line_end])
        chunks.append(CodeChunk(
            file_path=rel_path,
            language=language,
            chunk_type="function",
            name=name,
            content=content,
            line_start=line_start,
            line_end=line_end,
        ))

    return chunks


# ── Sliding window fallback ───────────────────────────────────────────────────

def _sliding_window(lines: list[str], rel_path: str, language: str) -> list[CodeChunk]:
    """Fallback: fixed-size windows with overlap."""
    chunks: list[CodeChunk] = []
    step = WINDOW_SIZE - WINDOW_OVERLAP
    total = len(lines)
    i = 0
    while i < total:
        end = min(i + WINDOW_SIZE, total)
        content = "\n".join(lines[i:end])
        if content.strip():
            chunks.append(CodeChunk(
                file_path=rel_path,
                language=language,
                chunk_type="window",
                name="",
                content=content,
                line_start=i + 1,
                line_end=end,
            ))
        i += step

    return chunks


# ── Public API ────────────────────────────────────────────────────────────────

def _should_skip_path(path: Path, repo_root: Path) -> bool:
    """Return True if this path should be excluded from indexing."""
    # Check each component against skip dir set
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return True

    for part in rel.parts[:-1]:  # all directory components
        if part in SKIP_DIRS or part.endswith(".egg-info"):
            return True

    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True

    if path.name in SKIP_FILENAMES:
        return True

    return False


def chunk_file(file_path: Path, repo_root: Path) -> list[CodeChunk]:
    """
    Chunk a single file into embeddable :class:`CodeChunk` objects.

    Returns an empty list for files that should be skipped.
    """
    if _should_skip_path(file_path, repo_root):
        return []

    if file_path.stat().st_size > MAX_FILE_BYTES:
        return []

    rel_path = str(file_path.relative_to(repo_root))
    language = _detect_language(file_path)

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return []

    if not source.strip():
        return []

    if language == "python":
        raw_chunks = _chunk_python(source, rel_path)
    elif language in ("typescript", "javascript"):
        raw_chunks = _chunk_typescript(source, rel_path, language)
    else:
        lines = source.splitlines()
        raw_chunks = _sliding_window(lines, rel_path, language)

    # Split any oversized AST/regex chunks into windows
    chunks: list[CodeChunk] = []
    for c in raw_chunks:
        chunks.extend(_split_if_oversized(c))
    return chunks


def chunk_repo(repo_root: Path) -> list[CodeChunk]:
    """
    Walk a repository and return all chunks from all eligible files.

    Args:
        repo_root: Absolute path to the cloned repository.

    Returns:
        List of :class:`CodeChunk` objects ready for embedding.
    """
    chunks: list[CodeChunk] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        chunks.extend(chunk_file(path, repo_root))
    return chunks


__all__ = ["CodeChunk", "chunk_file", "chunk_repo"]
