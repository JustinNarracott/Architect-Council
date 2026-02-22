"""Structure analyser tool — query repo structure by category."""

import os
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Files / dirs to always skip
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", ".nuxt", "venv", ".venv",
    "vendor", "coverage", ".cache", ".tox",
}

CATEGORY_PATTERNS: dict[str, list[str]] = {
    "test": [
        "test_*.py", "*_test.py", "*.test.ts", "*.test.tsx",
        "*.test.js", "*.test.jsx", "*.spec.ts", "*.spec.tsx",
        "*.spec.js", "*.spec.jsx",
    ],
    "config": [
        "*.toml", "*.ini", "*.cfg", "*.yaml", "*.yml", "*.json",
        ".env*", "Dockerfile*", "docker-compose*", "Makefile",
        "*.config.js", "*.config.ts", "*.config.mjs",
        "jest.config*", "vitest.config*", "webpack.config*",
        "tsconfig*", ".eslintrc*", ".prettierrc*", ".babelrc*",
    ],
    "entrypoint": [
        "main.py", "app.py", "server.py", "index.py",
        "main.ts", "main.js", "index.ts", "index.js",
        "app.ts", "app.js", "server.ts", "server.js",
        "__main__.py",
    ],
    "dependency": [
        "package.json", "package-lock.json", "yarn.lock", "bun.lockb",
        "pyproject.toml", "requirements*.txt", "Pipfile", "poetry.lock",
        "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
        "pom.xml", "build.gradle", "build.gradle.kts",
    ],
    "docs": [
        "README*", "CHANGELOG*", "CONTRIBUTING*", "*.md", "*.rst",
        "docs/**",
    ],
}


class StructureAnalyserInput(BaseModel):
    """Input schema for structure analysis."""

    query: str = Field(
        ...,
        description=(
            "Category to query. One of: 'test', 'config', 'entrypoint', 'dependency', "
            "'docs', 'all'. Or a file extension like '.py', '.ts'."
        ),
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of files to return (default 50)",
    )


class StructureAnalyserTool(BaseTool):
    """Queries repo file structure by category (tests, configs, entrypoints, etc.)."""

    name: str = "Structure Analyser"
    description: str = (
        "Analyse the structure of the repository being reviewed. "
        "Query by category: 'test', 'config', 'entrypoint', 'dependency', 'docs', 'all'. "
        "Or supply a file extension (e.g. '.py', '.ts') to list all files of that type. "
        "Returns matching files with their paths and sizes."
    )
    args_schema: Type[BaseModel] = StructureAnalyserInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self, query: str, max_results: int = 50) -> str:
        """Walk the repo and return matching files."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            query_lower = query.lower().strip()

            if query_lower == "all":
                matches = self._walk_all(repo_root, max_results)
                label = "All files"
            elif query_lower.startswith("."):
                # Extension query
                matches = self._walk_by_extension(repo_root, query_lower, max_results)
                label = f"Files with extension '{query}'"
            elif query_lower in CATEGORY_PATTERNS:
                matches = self._walk_by_category(repo_root, query_lower, max_results)
                label = f"Category: {query}"
            else:
                return (
                    f"Unknown query '{query}'. Valid categories: "
                    + ", ".join(sorted(CATEGORY_PATTERNS.keys()))
                    + ". Or use a file extension like '.py'."
                )

            if not matches:
                return f"No files found for query '{query}' in repo."

            lines = [f"{label} — {len(matches)} result(s):", "=" * 60]
            for path, size in matches:
                rel = path.relative_to(repo_root)
                size_str = self._fmt_size(size)
                lines.append(f"  {rel}  ({size_str})")

            # Summary stats for "all"
            if query_lower == "all":
                ext_counts: dict[str, int] = {}
                for path, _ in matches:
                    ext = path.suffix.lower() or "(no ext)"
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
                top = sorted(ext_counts.items(), key=lambda x: -x[1])[:10]
                lines.append("")
                lines.append("Top extensions:")
                for ext, count in top:
                    lines.append(f"  {ext}: {count}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error analysing structure: {str(e)}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_skip(self, path: Path) -> bool:
        return path.name in SKIP_DIRS

    def _walk_all(self, root: Path, limit: int) -> list[tuple[Path, int]]:
        results: list[tuple[Path, int]] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                results.append((fpath, fpath.stat().st_size))
                if len(results) >= limit:
                    return results
        return results

    def _walk_by_extension(self, root: Path, ext: str, limit: int) -> list[tuple[Path, int]]:
        results: list[tuple[Path, int]] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if Path(fname).suffix.lower() == ext:
                    fpath = Path(dirpath) / fname
                    results.append((fpath, fpath.stat().st_size))
                    if len(results) >= limit:
                        return results
        return results

    def _walk_by_category(self, root: Path, category: str, limit: int) -> list[tuple[Path, int]]:
        import fnmatch

        patterns = CATEGORY_PATTERNS[category]
        results: list[tuple[Path, int]] = []
        seen: set[Path] = set()

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                for pattern in patterns:
                    if fnmatch.fnmatch(fname, pattern) or fnmatch.fnmatch(fname.lower(), pattern):
                        fpath = Path(dirpath) / fname
                        if fpath not in seen:
                            seen.add(fpath)
                            results.append((fpath, fpath.stat().st_size))
                if len(results) >= limit:
                    return results
        return results

    @staticmethod
    def _fmt_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size // 1024} KB"
        return f"{size // (1024 * 1024)} MB"
