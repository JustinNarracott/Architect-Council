"""Dependency parsing utilities for various package manager formats."""

import json
from pathlib import Path
from typing import Literal

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


DepType = Literal["prod", "dev"]


def parse_dependencies(repo_path: Path) -> list[dict]:
    """
    Parse dependencies from all recognised package manager files in the repo.

    Checks (in order):
      - package.json         (npm / bun)
      - pyproject.toml       (PEP 621 / Poetry)
      - requirements.txt     (plain pip)

    Args:
        repo_path: Path to the cloned repository root.

    Returns:
        List of dicts with keys: name, version, dep_type ("prod" | "dev").
        Deduplicates by (name, dep_type) — last entry wins if a package
        appears in more than one file.
    """
    seen: dict[tuple[str, str], dict] = {}

    for dep in _parse_package_json(repo_path):
        seen[(dep["name"], dep["dep_type"])] = dep

    for dep in _parse_pyproject_toml(repo_path):
        seen[(dep["name"], dep["dep_type"])] = dep

    for dep in _parse_requirements_txt(repo_path):
        seen[(dep["name"], dep["dep_type"])] = dep

    return list(seen.values())


# ── package.json ──────────────────────────────────────────────────────────────

def _parse_package_json(repo_path: Path) -> list[dict]:
    """Parse npm/bun dependencies from package.json."""
    pkg_file = repo_path / "package.json"
    if not pkg_file.exists():
        return []

    try:
        with open(pkg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    deps: list[dict] = []

    for name, version in data.get("dependencies", {}).items():
        deps.append({"name": name, "version": _clean_version(version), "dep_type": "prod"})

    for name, version in data.get("devDependencies", {}).items():
        deps.append({"name": name, "version": _clean_version(version), "dep_type": "dev"})

    return deps


# ── pyproject.toml ────────────────────────────────────────────────────────────

def _parse_pyproject_toml(repo_path: Path) -> list[dict]:
    """Parse Python dependencies from pyproject.toml (PEP 621 and Poetry)."""
    toml_file = repo_path / "pyproject.toml"
    if not toml_file.exists():
        return []

    try:
        with open(toml_file, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return []

    deps: list[dict] = []

    # PEP 621: [project].dependencies
    project = data.get("project", {})
    for spec in project.get("dependencies", []):
        name, version = _split_pep508(spec)
        deps.append({"name": name, "version": version, "dep_type": "prod"})

    # PEP 621: [dependency-groups] (PEP 735 — dev groups)
    for _group_name, specs in data.get("dependency-groups", {}).items():
        for spec in specs:
            if isinstance(spec, str):
                name, version = _split_pep508(spec)
                deps.append({"name": name, "version": version, "dep_type": "dev"})

    # Poetry: [tool.poetry.dependencies] / [tool.poetry.dev-dependencies]
    poetry = data.get("tool", {}).get("poetry", {})
    for name, spec in poetry.get("dependencies", {}).items():
        if name.lower() == "python":
            continue
        version = spec if isinstance(spec, str) else spec.get("version", "*") if isinstance(spec, dict) else "*"
        deps.append({"name": name, "version": version, "dep_type": "prod"})

    for name, spec in poetry.get("dev-dependencies", {}).items():
        version = spec if isinstance(spec, str) else spec.get("version", "*") if isinstance(spec, dict) else "*"
        deps.append({"name": name, "version": version, "dep_type": "dev"})

    # Poetry group dev (newer format)
    for _group_name, group_data in poetry.get("group", {}).items():
        for name, spec in group_data.get("dependencies", {}).items():
            version = spec if isinstance(spec, str) else spec.get("version", "*") if isinstance(spec, dict) else "*"
            deps.append({"name": name, "version": version, "dep_type": "dev"})

    return deps


# ── requirements.txt ──────────────────────────────────────────────────────────

def _parse_requirements_txt(repo_path: Path) -> list[dict]:
    """Parse Python dependencies from requirements.txt."""
    req_file = repo_path / "requirements.txt"
    if not req_file.exists():
        return []

    deps: list[dict] = []
    try:
        with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                line = raw_line.strip()
                # Skip comments, blank lines, and options (e.g. -r other.txt, --index-url)
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                name, version = _split_pep508(line)
                deps.append({"name": name, "version": version, "dep_type": "prod"})
    except OSError:
        return []

    return deps


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_version(version: str) -> str:
    """
    Normalise npm/bun version strings.

    Strips leading ^ ~ = characters used by package.json range specifiers.
    """
    return version.lstrip("^~=").strip() if version else "*"


def _split_pep508(spec: str) -> tuple[str, str]:
    """
    Split a PEP 508 dependency specifier into (name, version).

    Examples:
        "requests>=2.31.0"   -> ("requests", ">=2.31.0")
        "fastapi[all]"       -> ("fastapi[all]", "*")
        "numpy==1.26.0"      -> ("numpy", "==1.26.0")
    """
    import re

    # Match package name (with optional extras) and version constraint
    match = re.match(r"^([A-Za-z0-9_.\\-]+(?:\[[^\]]+\])?)\s*([><=!~^][^\s;]*)?", spec)
    if match:
        name = match.group(1).strip()
        version = match.group(2).strip() if match.group(2) else "*"
        return name, version

    return spec.strip(), "*"
