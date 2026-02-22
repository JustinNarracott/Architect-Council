"""Repo ingestion layer — clone, map, and parse a Git repository."""

import asyncio
import uuid
from pathlib import Path

from pydantic import BaseModel, Field

from .dependency_parser import parse_dependencies
from .repo_cloner import RepoCloner
from .structure_mapper import RepoStructure, map_structure


class IndexedRepo(BaseModel):
    """
    Fully indexed representation of a cloned repository.

    Produced by :func:`index_repo` and passed to codebase review agents.
    """

    analysis_id: str = Field(description="Unique identifier for this indexing run")
    repo_url: str = Field(description="Original HTTPS URL of the repository")
    clone_path: str = Field(description="Absolute path to the cloned directory on disk")

    # Structure
    total_files: int = Field(description="Total number of files (excluding skipped dirs)")
    total_loc: int = Field(description="Estimated non-blank lines of code")
    directory_tree: str = Field(description="ASCII directory tree (max 3 levels)")
    language_breakdown: list[dict] = Field(
        description="File counts per extension, sorted by frequency"
    )
    key_files: dict[str, str] = Field(
        description="Detected key files: {filename -> relative path}"
    )

    # Dependencies
    dependencies: list[dict] = Field(
        description="Parsed dependencies: [{name, version, dep_type}]"
    )

    class Config:
        # Allow Path objects when constructing from ORM/NamedTuple
        arbitrary_types_allowed = True


def _structure_to_dict_fields(structure: RepoStructure) -> dict:
    """Convert a RepoStructure NamedTuple to a dict suitable for IndexedRepo."""
    return {
        "total_files": structure.total_files,
        "total_loc": structure.total_loc,
        "directory_tree": structure.directory_tree,
        "language_breakdown": [
            {
                "extension": lb.extension,
                "count": lb.count,
                "percentage": lb.percentage,
            }
            for lb in structure.language_breakdown
        ],
        "key_files": structure.key_files,
    }


async def index_local_repo(local_path: str) -> IndexedRepo:
    """
    Map and parse a locally mounted repository — no cloning required.

    Accepts an absolute path that must exist on disk (e.g. ``/repos/signalbreak``).
    Runs the same structure mapping and dependency parsing as :func:`index_repo`
    but skips the git clone step entirely.

    Args:
        local_path: Absolute path to the repository root on disk.

    Returns:
        :class:`IndexedRepo` populated with structure and dependency data.
        ``repo_url`` is set to ``local://<path>`` and ``clone_path`` is the
        provided path.

    Raises:
        ValueError: If the path does not exist or is not a directory.
    """
    path = Path(local_path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Local path does not exist or is not a directory: {local_path}")

    analysis_id = str(uuid.uuid4())

    def _blocking_index() -> tuple[RepoStructure, list[dict]]:
        structure = map_structure(path)
        dependencies = parse_dependencies(path)
        return structure, dependencies

    loop = asyncio.get_running_loop()
    structure, dependencies = await loop.run_in_executor(None, _blocking_index)

    return IndexedRepo(
        analysis_id=analysis_id,
        repo_url=f"local://{local_path}",
        clone_path=str(path),
        dependencies=dependencies,
        **_structure_to_dict_fields(structure),
    )


async def index_repo(repo_url: str, auth_token: str | None = None) -> IndexedRepo:
    """
    Clone, map, and parse a repository — the full ingestion pipeline.

    Runs the blocking clone + walk in an executor to avoid blocking the
    FastAPI event loop.

    Args:
        repo_url:   HTTPS URL of the repository to analyse.
        auth_token: Optional GitHub / GitLab personal access token for
                    private repositories.

    Returns:
        :class:`IndexedRepo` populated with structure and dependency data.

    Raises:
        git.exc.GitCommandError: If cloning fails (bad URL, auth failure, etc.)
        ValueError:              If the URL is empty or the path doesn't exist.
    """
    analysis_id = str(uuid.uuid4())

    def _blocking_index() -> tuple[Path, RepoStructure, list[dict]]:
        """All I/O-bound work, runs in thread executor."""
        cloner = RepoCloner(repo_url=repo_url, auth_token=auth_token)
        clone_path = cloner.clone()

        structure = map_structure(clone_path)
        dependencies = parse_dependencies(clone_path)

        return clone_path, structure, dependencies

    loop = asyncio.get_running_loop()
    clone_path, structure, dependencies = await loop.run_in_executor(None, _blocking_index)

    return IndexedRepo(
        analysis_id=analysis_id,
        repo_url=repo_url,
        clone_path=str(clone_path),
        dependencies=dependencies,
        **_structure_to_dict_fields(structure),
    )


__all__ = ["IndexedRepo", "index_repo", "index_local_repo"]
