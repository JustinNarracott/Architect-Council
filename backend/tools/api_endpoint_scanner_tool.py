"""API endpoint scanner tool — find route definitions across frameworks."""

import os
import re
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", ".nuxt", "venv", ".venv", "vendor",
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "all"}

# ------------------------------------------------------------------
# Pattern definitions
# ------------------------------------------------------------------

# FastAPI / Flask / Starlette: @app.get("/path") or @router.post("/path")
_FASTAPI_PATTERN = re.compile(
    r"@\w+\.("
    + "|".join(HTTP_METHODS)
    + r""")\s*\(\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)

# Django urls.py: path("route/", view_func)  or  re_path(r"^route/$", view_func)
_DJANGO_PATH_PATTERN = re.compile(
    r"""(?:re_)?path\s*\(\s*[r]?['"]([^'"]+)['"]""",
    re.IGNORECASE,
)

# Express.js: app.get('/route', handler)  or  router.post('/route', handler)
_EXPRESS_PATTERN = re.compile(
    r"""(?:app|router)\s*\.\s*("""
    + "|".join(HTTP_METHODS)
    + r""")\s*\(\s*['"`]([^'"`]+)['"`]""",
    re.IGNORECASE,
)

# Next.js API routes: export default function handler  or  export { GET, POST }
# The "route" is derived from the file path, not an inline string.
_NEXTJS_API_FILE_PATTERN = re.compile(
    r"pages[/\\]api[/\\].*\.(ts|tsx|js|jsx)$"
)
_NEXTJS_APP_ROUTER_PATTERN = re.compile(
    r"app[/\\].*route\.(ts|tsx|js|jsx)$"
)
_NEXTJS_EXPORT_METHOD_PATTERN = re.compile(
    r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b",
)

Endpoint = dict  # {method, path, file, line}


class APIEndpointScannerInput(BaseModel):
    """Input schema for API endpoint scanning."""

    framework: str = Field(
        default="auto",
        description=(
            "Framework to scan for: 'fastapi', 'flask', 'express', 'nextjs', 'django', 'auto'. "
            "Use 'auto' to detect all supported frameworks."
        ),
    )


class APIEndpointScannerTool(BaseTool):
    """Scans a cloned repository for API route definitions."""

    name: str = "API Endpoint Scanner"
    description: str = (
        "Find API route definitions in the repository being reviewed. "
        "Detects FastAPI/Flask/Starlette decorators, Express.js routes, "
        "Next.js API routes (pages/api and App Router), and Django url patterns. "
        "Returns: HTTP method, path, handler file, and line number."
    )
    args_schema: Type[BaseModel] = APIEndpointScannerInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self, framework: str = "auto") -> str:
        """Scan the repo for API endpoints."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            endpoints: list[Endpoint] = []
            framework_lower = framework.lower()

            for dirpath, dirnames, filenames in os.walk(repo_root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fname in filenames:
                    fpath = Path(dirpath) / fname
                    rel_str = str(fpath.relative_to(repo_root)).replace("\\", "/")
                    suffix = fpath.suffix.lower()

                    if framework_lower in ("auto", "fastapi", "flask"):
                        if suffix == ".py":
                            endpoints.extend(
                                self._scan_fastapi_flask(fpath, rel_str)
                            )

                    if framework_lower in ("auto", "django"):
                        if fname in ("urls.py",) or "url" in fname.lower():
                            if suffix == ".py":
                                endpoints.extend(
                                    self._scan_django(fpath, rel_str)
                                )

                    if framework_lower in ("auto", "express"):
                        if suffix in {".js", ".ts", ".mjs", ".cjs"}:
                            endpoints.extend(
                                self._scan_express(fpath, rel_str)
                            )

                    if framework_lower in ("auto", "nextjs"):
                        if suffix in {".ts", ".tsx", ".js", ".jsx"}:
                            if (
                                _NEXTJS_API_FILE_PATTERN.search(rel_str)
                                or _NEXTJS_APP_ROUTER_PATTERN.search(rel_str)
                            ):
                                endpoints.extend(
                                    self._scan_nextjs(fpath, rel_str)
                                )

            if not endpoints:
                return (
                    f"No API endpoints found in repo (framework={framework}). "
                    "The repo may use an unsupported framework or have no route definitions."
                )

            lines = [
                f"API Endpoints — {len(endpoints)} found (framework={framework})",
                "=" * 60,
                "",
                f"{'METHOD':<8}  {'PATH':<40}  {'FILE:LINE'}",
                "-" * 80,
            ]
            # Sort by file then line
            endpoints.sort(key=lambda e: (e["file"], e["line"]))
            for ep in endpoints:
                method = ep["method"].upper()
                path = ep["path"]
                loc = f"{ep['file']}:{ep['line']}"
                lines.append(f"{method:<8}  {path:<40}  {loc}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error scanning API endpoints: {str(e)}"

    # ------------------------------------------------------------------
    # Scanners
    # ------------------------------------------------------------------

    def _scan_fastapi_flask(self, fpath: Path, rel: str) -> list[Endpoint]:
        endpoints: list[Endpoint] = []
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return endpoints
        for i, line in enumerate(lines, 1):
            for m in _FASTAPI_PATTERN.finditer(line):
                endpoints.append(
                    {"method": m.group(1).upper(), "path": m.group(2), "file": rel, "line": i}
                )
        return endpoints

    def _scan_django(self, fpath: Path, rel: str) -> list[Endpoint]:
        """Django url patterns don't always have HTTP methods — mark as ANY."""
        endpoints: list[Endpoint] = []
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return endpoints
        for i, line in enumerate(lines, 1):
            for m in _DJANGO_PATH_PATTERN.finditer(line):
                # Skip if it looks like a test or comment
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                endpoints.append(
                    {"method": "ANY", "path": m.group(1), "file": rel, "line": i}
                )
        return endpoints

    def _scan_express(self, fpath: Path, rel: str) -> list[Endpoint]:
        endpoints: list[Endpoint] = []
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return endpoints
        for i, line in enumerate(lines, 1):
            for m in _EXPRESS_PATTERN.finditer(line):
                endpoints.append(
                    {"method": m.group(1).upper(), "path": m.group(2), "file": rel, "line": i}
                )
        return endpoints

    def _scan_nextjs(self, fpath: Path, rel: str) -> list[Endpoint]:
        """
        For Next.js, the route path is derived from the file path.
        Pages router: pages/api/users/[id].ts → /api/users/[id]
        App router:   app/api/users/[id]/route.ts → /api/users/[id]
        """
        endpoints: list[Endpoint] = []
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
        except Exception:
            return endpoints

        # Derive route path from file path
        rel_posix = rel.replace("\\", "/")
        if "pages/api/" in rel_posix:
            route_path = "/" + re.sub(r"\.(ts|tsx|js|jsx)$", "", rel_posix)
            route_path = re.sub(r"pages", "", route_path, count=1)
        elif "app/" in rel_posix and rel_posix.endswith(("route.ts", "route.tsx", "route.js", "route.jsx")):
            route_path = "/" + re.sub(r"/route\.(ts|tsx|js|jsx)$", "", rel_posix)
            route_path = re.sub(r"^/?app", "", route_path)
        else:
            route_path = "/" + rel_posix

        # Normalise Next.js dynamic segments: [id] → {id}
        route_path = route_path.replace("[", "{").replace("]", "}")

        # Detect exported HTTP method handlers
        exported_methods: list[tuple[str, int]] = []
        for i, line in enumerate(lines, 1):
            m = _NEXTJS_EXPORT_METHOD_PATTERN.search(line)
            if m:
                exported_methods.append((m.group(1).upper(), i))

        if exported_methods:
            for method, lineno in exported_methods:
                endpoints.append(
                    {"method": method, "path": route_path, "file": rel, "line": lineno}
                )
        else:
            # Fallback: pages/api default export = ANY
            endpoints.append(
                {"method": "ANY", "path": route_path, "file": rel, "line": 1}
            )

        return endpoints
