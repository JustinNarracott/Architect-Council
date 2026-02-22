"""File reader tool — read any file from a cloned repo with path traversal prevention."""

from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

MAX_CHARS = 10_000


class FileReaderInput(BaseModel):
    """Input schema for reading a file from a cloned repo."""

    file_path: str = Field(..., description="Relative path to the file within the repo (e.g. 'src/main.py')")


class FileReaderTool(BaseTool):
    """Reads a file from a cloned repository with path traversal prevention."""

    name: str = "File Reader"
    description: str = (
        "Read the contents of any file within the repository being reviewed. "
        "Provide the relative file path (e.g. 'src/main.py', 'package.json'). "
        "Files are truncated to 10,000 characters with a notice. "
        "Use this to inspect source files, configs, READMEs, etc."
    )
    args_schema: Type[BaseModel] = FileReaderInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self, file_path: str) -> str:
        """Read a file from the cloned repo, enforcing repo boundary."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            # Resolve the target path — this collapses any ../ components
            target = (repo_root / file_path).resolve()

            # Security: reject anything that escapes the repo root
            try:
                target.relative_to(repo_root)
            except ValueError:
                return (
                    f"Security Error: Path '{file_path}' resolves outside the repo root. "
                    "Path traversal is not permitted."
                )

            if not target.exists():
                return f"Error: File '{file_path}' not found in repo."

            if not target.is_file():
                return f"Error: '{file_path}' is a directory, not a file."

            # Guard against very large binary files
            size = target.stat().st_size
            if size > 5 * 1024 * 1024:  # 5 MB hard limit
                return (
                    f"File '{file_path}' is {size // 1024} KB — too large to read directly. "
                    "Use structure_analyser or focus on a specific section."
                )

            content = target.read_text(encoding="utf-8", errors="replace")

            truncated = False
            if len(content) > MAX_CHARS:
                content = content[:MAX_CHARS]
                truncated = True

            header = f"File: {file_path}\n{'=' * 60}\n"
            footer = (
                f"\n\n[TRUNCATED — showing first {MAX_CHARS:,} of {size:,} characters]"
                if truncated
                else ""
            )
            return header + content + footer

        except Exception as e:
            return f"Error reading file '{file_path}': {str(e)}"
