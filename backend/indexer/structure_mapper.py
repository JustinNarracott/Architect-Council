"""Repository structure mapping and analysis utilities."""

from pathlib import Path
from typing import NamedTuple


class LanguageBreakdown(NamedTuple):
    """File count by programming language/extension."""

    extension: str
    count: int
    percentage: float


class RepoStructure(NamedTuple):
    """Summary of repository structure."""

    total_files: int
    total_loc: int
    language_breakdown: list[LanguageBreakdown]
    directory_tree: str
    key_files: dict[str, str]  # file type -> relative path


# Directories to skip during analysis
SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    "dist",
    "build",
    "vendor",
    ".next",
    "venv",
    ".venv",
    "env",
    ".pytest_cache",
    "coverage",
    ".nyc_output",
    "target",
    "out",
}

# Key configuration files to detect
KEY_FILES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "README.md",
    "README",
    "tsconfig.json",
    "jest.config.js",
    "jest.config.ts",
    "pytest.ini",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "Makefile",
}

# Extensions for LOC estimation
CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    ".sql",
    ".sh",
    ".bash",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
}


def map_structure(repo_path: Path) -> RepoStructure:
    """
    Map the structure of a repository.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        RepoStructure containing file counts, directory tree, and key files
    """
    if not repo_path.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")

    # Count files by extension
    extension_counts: dict[str, int] = {}
    total_files = 0
    total_loc = 0
    key_files: dict[str, str] = {}

    for file_path in _walk_repo(repo_path):
        total_files += 1

        # Count by extension
        ext = file_path.suffix.lower()
        if ext:
            extension_counts[ext] = extension_counts.get(ext, 0) + 1

        # Estimate LOC for code files
        if ext in CODE_EXTENSIONS:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    total_loc += sum(1 for line in f if line.strip())
            except Exception:
                # Skip files that can't be read
                pass

        # Check for key files
        file_name = file_path.name
        if file_name in KEY_FILES:
            relative_path = file_path.relative_to(repo_path)
            key_files[file_name] = str(relative_path)

    # Calculate language breakdown
    language_breakdown = _calculate_language_breakdown(extension_counts, total_files)

    # Generate directory tree (max 3 levels)
    directory_tree = _generate_tree(repo_path, max_depth=3)

    return RepoStructure(
        total_files=total_files,
        total_loc=total_loc,
        language_breakdown=language_breakdown,
        directory_tree=directory_tree,
        key_files=key_files,
    )


def _walk_repo(repo_path: Path):
    """
    Walk repository files, skipping excluded directories.

    Yields:
        Path objects for files in the repository
    """
    for item in repo_path.rglob("*"):
        # Skip if any parent directory is in SKIP_DIRS
        if any(part in SKIP_DIRS for part in item.parts):
            continue

        if item.is_file():
            yield item


def _calculate_language_breakdown(
    extension_counts: dict[str, int], total_files: int
) -> list[LanguageBreakdown]:
    """
    Calculate language breakdown from extension counts.

    Args:
        extension_counts: Dictionary of extension -> count
        total_files: Total number of files

    Returns:
        List of LanguageBreakdown sorted by count (descending)
    """
    if total_files == 0:
        return []

    breakdown = [
        LanguageBreakdown(
            extension=ext,
            count=count,
            percentage=round((count / total_files) * 100, 1),
        )
        for ext, count in extension_counts.items()
    ]

    # Sort by count (descending)
    breakdown.sort(key=lambda x: x.count, reverse=True)

    return breakdown


def _generate_tree(repo_path: Path, max_depth: int = 3) -> str:
    """
    Generate a directory tree representation.

    Args:
        repo_path: Path to the repository root
        max_depth: Maximum depth to traverse

    Returns:
        String representation of the directory tree
    """
    lines = [str(repo_path.name) + "/"]

    def _build_tree(current_path: Path, prefix: str = "", depth: int = 0):
        if depth >= max_depth:
            return

        try:
            items = sorted(
                [
                    item
                    for item in current_path.iterdir()
                    if item.name not in SKIP_DIRS and not item.name.startswith(".")
                ],
                key=lambda x: (not x.is_dir(), x.name),
            )
        except PermissionError:
            return

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if item.is_dir():
                lines.append(f"{prefix}{current_prefix}{item.name}/")
                _build_tree(item, next_prefix, depth + 1)
            else:
                lines.append(f"{prefix}{current_prefix}{item.name}")

    _build_tree(repo_path)

    return "\n".join(lines)
