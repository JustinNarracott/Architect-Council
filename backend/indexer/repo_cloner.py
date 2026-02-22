"""Repository cloning utilities for codebase analysis."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import Repo
from git.exc import GitCommandError

_ALLOWED_SCHEMES = {"https", "ssh", "git"}
_BLOCKED_SCHEMES = {"file", "ftp", "http"}  # http blocked — use https only


def validate_repo_url(url: str) -> str:
    """
    Validate a repository URL before passing to GitPython.
    Allows: https://, ssh://, git@
    Rejects: file://, ftp://, bare paths, shell metacharacters
    """
    # Block obvious shell injection characters
    if any(c in url for c in [";", "&", "|", "`", "$", "\n", "\r"]):
        raise ValueError("Invalid repository URL — shell metacharacters detected")

    # Allow git@ SSH shorthand (e.g. git@github.com:user/repo.git)
    if url.startswith("git@"):
        return url

    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"Repository URL scheme '{parsed.scheme}' is not permitted. "
            "Use https:// or ssh://"
        )

    return url


class RepoCloner:
    """Handles cloning of Git repositories for analysis."""

    def __init__(self, repo_url: str, auth_token: Optional[str] = None):
        """
        Initialize the repository cloner.

        Args:
            repo_url: HTTPS URL of the Git repository
            auth_token: Optional authentication token for private repos
        """
        # Validate URL before storing
        self.repo_url = validate_repo_url(repo_url)
        self.auth_token = auth_token
        self.clone_path: Optional[Path] = None
        self._repo: Optional[Repo] = None

    def clone(self) -> Path:
        """
        Clone the repository to a temporary directory.

        Uses shallow clone (depth=1) for speed.

        Returns:
            Path to the cloned repository

        Raises:
            GitCommandError: If cloning fails
            ValueError: If URL is invalid
        """
        if not self.repo_url:
            raise ValueError("Repository URL cannot be empty")

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="architecture_council_")
        self.clone_path = Path(temp_dir)

        # Build clone URL with authentication if provided
        clone_url = self._build_authenticated_url()

        try:
            # Shallow clone for speed (only latest commit)
            self._repo = Repo.clone_from(
                clone_url,
                self.clone_path,
                depth=1,
                single_branch=True,
            )
            return self.clone_path
        except GitCommandError as e:
            # Clean up on failure
            self.cleanup()
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "401" in error_msg:
                raise GitCommandError(
                    "git clone",
                    128,
                    "Authentication failed. Please check your auth token.",
                ) from e
            elif "not found" in error_msg.lower() or "404" in error_msg:
                raise GitCommandError(
                    "git clone",
                    128,
                    "Repository not found. Please check the URL.",
                ) from e
            else:
                raise

    def _build_authenticated_url(self) -> str:
        """
        Build clone URL with authentication token if provided.

        For GitHub: https://token@github.com/user/repo.git
        For GitLab: https://oauth2:token@gitlab.com/user/repo.git

        Returns:
            Authenticated URL or original URL if no token
        """
        if not self.auth_token:
            return self.repo_url

        url = self.repo_url
        if url.startswith("https://"):
            url = url[8:]  # Remove https://

            # Detect provider and format accordingly
            if "github.com" in url:
                return f"https://{self.auth_token}@{url}"
            elif "gitlab.com" in url:
                return f"https://oauth2:{self.auth_token}@{url}"
            else:
                # Generic token format
                return f"https://{self.auth_token}@{url}"

        return self.repo_url

    def cleanup(self) -> None:
        """
        Remove the cloned repository directory.

        Safe to call multiple times.
        """
        if self.clone_path and self.clone_path.exists():
            try:
                shutil.rmtree(self.clone_path)
                self.clone_path = None
                self._repo = None
            except Exception as e:
                # Log but don't raise - cleanup failures shouldn't break flow
                print(f"Warning: Failed to cleanup {self.clone_path}: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.clone()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.cleanup()
        return False
