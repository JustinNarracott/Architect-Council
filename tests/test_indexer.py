"""Tests for the repo ingestion layer (Sprint 7).

Clones a small public repository and verifies that structure mapping and
dependency parsing return well-formed data.

Run with:
    pytest tests/test_indexer.py -v

Note: requires network access and gitpython installed.
"""

import asyncio
from pathlib import Path

import pytest

from backend.indexer import IndexedRepo, index_repo
from backend.indexer.dependency_parser import parse_dependencies
from backend.indexer.repo_cloner import RepoCloner
from backend.indexer.structure_mapper import map_structure

# A tiny public repo known to stay stable and clone quickly.
# flask is a well-known Python project with pyproject.toml / requirements.txt.
TEST_REPO_URL = "https://github.com/pallets/flask"


# ── RepoCloner ────────────────────────────────────────────────────────────────

class TestRepoCloner:
    def test_clone_creates_directory(self, tmp_path):
        """Shallow clone should succeed and populate the directory."""
        cloner = RepoCloner(repo_url=TEST_REPO_URL)
        clone_path = cloner.clone()

        try:
            assert clone_path.exists()
            assert clone_path.is_dir()
            # There should be at least some files
            files = list(clone_path.rglob("*"))
            assert len(files) > 0, "Cloned repo appears empty"
        finally:
            cloner.cleanup()

    def test_cleanup_removes_directory(self):
        """cleanup() should delete the temp directory."""
        cloner = RepoCloner(repo_url=TEST_REPO_URL)
        clone_path = cloner.clone()
        assert clone_path.exists()

        cloner.cleanup()
        assert not clone_path.exists()

    def test_context_manager(self):
        """Context manager form should clone and clean up automatically."""
        clone_path_capture = None
        with RepoCloner(repo_url=TEST_REPO_URL) as cloner:
            clone_path_capture = cloner.clone_path
            assert clone_path_capture is not None
            assert clone_path_capture.exists()

        # After __exit__, directory should be gone
        assert clone_path_capture is not None
        assert not clone_path_capture.exists()

    def test_invalid_url_raises(self):
        """Cloning a non-existent repo should raise GitCommandError."""
        from git.exc import GitCommandError

        cloner = RepoCloner(repo_url="https://github.com/this-user-does-not-exist-xyz/no-repo-here")
        with pytest.raises((GitCommandError, Exception)):
            cloner.clone()

    def test_authenticated_url_github(self):
        """GitHub token URL should be formatted correctly."""
        cloner = RepoCloner(
            repo_url="https://github.com/owner/repo",
            auth_token="ghp_testtoken123",
        )
        url = cloner._build_authenticated_url()
        assert url == "https://ghp_testtoken123@github.com/owner/repo"

    def test_authenticated_url_gitlab(self):
        """GitLab token URL should use oauth2: prefix."""
        cloner = RepoCloner(
            repo_url="https://gitlab.com/owner/repo",
            auth_token="glpat-testtoken",
        )
        url = cloner._build_authenticated_url()
        assert url == "https://oauth2:glpat-testtoken@gitlab.com/owner/repo"


# ── StructureMapper ───────────────────────────────────────────────────────────

class TestStructureMapper:
    @pytest.fixture(scope="class")
    def cloned_flask(self):
        """Clone flask once for all structure mapper tests."""
        cloner = RepoCloner(repo_url=TEST_REPO_URL)
        clone_path = cloner.clone()
        yield clone_path
        cloner.cleanup()

    def test_map_structure_returns_data(self, cloned_flask):
        structure = map_structure(cloned_flask)

        assert structure.total_files > 0
        assert structure.total_loc > 0
        assert isinstance(structure.directory_tree, str)
        assert len(structure.directory_tree) > 0

    def test_language_breakdown_sorted(self, cloned_flask):
        structure = map_structure(cloned_flask)

        counts = [lb.count for lb in structure.language_breakdown]
        assert counts == sorted(counts, reverse=True), "Breakdown should be sorted descending"

    def test_python_files_detected(self, cloned_flask):
        structure = map_structure(cloned_flask)

        extensions = [lb.extension for lb in structure.language_breakdown]
        assert ".py" in extensions, "Flask repo should contain Python files"

    def test_key_files_detected(self, cloned_flask):
        structure = map_structure(cloned_flask)

        # Flask uses pyproject.toml
        assert "pyproject.toml" in structure.key_files, (
            f"pyproject.toml not found; detected keys: {list(structure.key_files.keys())}"
        )

    def test_skip_dirs_honoured(self, cloned_flask):
        """node_modules and .git should not appear in tree or file count."""
        structure = map_structure(cloned_flask)

        assert ".git" not in structure.directory_tree
        assert "node_modules" not in structure.directory_tree

    def test_directory_tree_max_3_levels(self, cloned_flask):
        structure = map_structure(cloned_flask)

        # Count maximum indentation depth (each level = 4 chars: "│   " or "    ")
        max_indent = 0
        for line in structure.directory_tree.splitlines():
            indent = len(line) - len(line.lstrip("│ └├─"))
            level = indent // 4
            max_indent = max(max_indent, level)

        assert max_indent <= 3, f"Tree exceeds 3 levels (got depth {max_indent})"

    def test_invalid_path_raises(self):
        with pytest.raises(ValueError):
            map_structure(Path("/nonexistent/path/xyz"))


# ── DependencyParser ──────────────────────────────────────────────────────────

class TestDependencyParser:
    @pytest.fixture(scope="class")
    def cloned_flask(self):
        """Clone flask once for all dependency parser tests."""
        cloner = RepoCloner(repo_url=TEST_REPO_URL)
        clone_path = cloner.clone()
        yield clone_path
        cloner.cleanup()

    def test_parse_returns_list(self, cloned_flask):
        deps = parse_dependencies(cloned_flask)
        assert isinstance(deps, list)

    def test_deps_have_required_keys(self, cloned_flask):
        deps = parse_dependencies(cloned_flask)
        for dep in deps:
            assert "name" in dep, f"Missing 'name' in {dep}"
            assert "version" in dep, f"Missing 'version' in {dep}"
            assert "dep_type" in dep, f"Missing 'dep_type' in {dep}"

    def test_dep_type_values(self, cloned_flask):
        deps = parse_dependencies(cloned_flask)
        for dep in deps:
            assert dep["dep_type"] in ("prod", "dev"), (
                f"Invalid dep_type '{dep['dep_type']}' for {dep['name']}"
            )

    def test_flask_has_werkzeug_dependency(self, cloned_flask):
        """Flask depends on Werkzeug — it should appear in the parsed deps."""
        deps = parse_dependencies(cloned_flask)
        prod_names = [d["name"].lower() for d in deps if d["dep_type"] == "prod"]
        assert any("werkzeug" in n for n in prod_names), (
            f"Werkzeug not found in prod deps; found: {prod_names[:10]}"
        )

    def test_empty_repo_returns_empty_list(self, tmp_path):
        """A directory with no package files should return an empty list."""
        deps = parse_dependencies(tmp_path)
        assert deps == []

    def test_parse_package_json(self, tmp_path):
        """package.json parsing should separate prod and dev deps correctly."""
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text(
            '{"dependencies": {"react": "^18.0.0"}, "devDependencies": {"jest": "29.0.0"}}'
        )
        deps = parse_dependencies(tmp_path)

        prod = [d for d in deps if d["dep_type"] == "prod"]
        dev = [d for d in deps if d["dep_type"] == "dev"]

        assert any(d["name"] == "react" for d in prod)
        assert any(d["name"] == "jest" for d in dev)

    def test_parse_requirements_txt(self, tmp_path):
        """requirements.txt entries should parse into prod deps."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("requests>=2.31.0\nflask==3.0.0\n# a comment\n\n")
        deps = parse_dependencies(tmp_path)

        names = [d["name"] for d in deps]
        assert "requests" in names
        assert "flask" in names

    def test_npm_version_strips_caret(self, tmp_path):
        """Caret and tilde should be stripped from npm version strings."""
        pkg_json = tmp_path / "package.json"
        pkg_json.write_text('{"dependencies": {"lodash": "^4.17.21"}}')
        deps = parse_dependencies(tmp_path)

        lodash = next((d for d in deps if d["name"] == "lodash"), None)
        assert lodash is not None
        assert lodash["version"] == "4.17.21"


# ── index_repo (integration) ──────────────────────────────────────────────────

class TestIndexRepo:
    def test_index_repo_returns_indexed_repo(self):
        """Full pipeline should return a populated IndexedRepo instance."""
        result = asyncio.run(index_repo(TEST_REPO_URL))

        assert isinstance(result, IndexedRepo)
        assert result.repo_url == TEST_REPO_URL
        assert result.analysis_id  # non-empty UUID string
        assert result.total_files > 0
        assert result.total_loc > 0
        assert len(result.language_breakdown) > 0
        assert isinstance(result.key_files, dict)
        assert isinstance(result.dependencies, list)

    def test_index_repo_clone_path_is_string(self):
        """clone_path should be a non-empty string (serialisable)."""
        result = asyncio.run(index_repo(TEST_REPO_URL))
        assert isinstance(result.clone_path, str)
        assert len(result.clone_path) > 0

    def test_index_repo_serialisable(self):
        """IndexedRepo should serialise to JSON without error."""
        result = asyncio.run(index_repo(TEST_REPO_URL))
        json_str = result.model_dump_json()
        assert len(json_str) > 0
