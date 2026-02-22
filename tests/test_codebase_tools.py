"""Tests for Sprint 8 codebase agent tools.

Each tool is tested against a synthetic repo built in a pytest tmp_path fixture.
No network access required.

Run with:
    pytest tests/test_codebase_tools.py -v
"""

import json
from pathlib import Path

import pytest

from backend.tools.file_reader_tool import FileReaderTool
from backend.tools.structure_analyser_tool import StructureAnalyserTool
from backend.tools.import_graph_tool import ImportGraphTool
from backend.tools.api_endpoint_scanner_tool import APIEndpointScannerTool
from backend.tools.secret_scanner_tool import SecretScannerTool
from backend.tools.test_coverage_tool import TestCoverageTool


# ---------------------------------------------------------------------------
# Shared fixture — build a minimal sample repository
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    """Create a minimal synthetic repo structure for tool tests."""
    root = tmp_path / "repo"
    root.mkdir()

    # Source files
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text(
        'import os\nimport sys\nfrom src.utils import helper\n\nprint("hello")\n'
    )
    (root / "src" / "utils.py").write_text(
        "import os\n\ndef helper():\n    return 42\n"
    )
    (root / "src" / "api.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n"
        "@app.get('/health')\ndef health():\n    return {'ok': True}\n\n"
        "@app.post('/items')\ndef create_item():\n    pass\n"
    )

    # TypeScript file
    (root / "frontend").mkdir()
    (root / "frontend" / "index.ts").write_text(
        "import { helper } from './utils';\nimport express from 'express';\n"
        "const app = express();\napp.get('/api/ping', (req, res) => res.send('pong'));\n"
    )
    (root / "frontend" / "utils.ts").write_text(
        "export function helper() { return 42; }\n"
    )

    # Next.js API route
    (root / "pages" / "api").mkdir(parents=True)
    (root / "pages" / "api" / "users.ts").write_text(
        "export async function GET(req: Request) {\n  return Response.json([]);\n}\n"
        "export async function POST(req: Request) {\n  return Response.json({});\n}\n"
    )

    # Test files
    (root / "tests").mkdir()
    (root / "tests" / "test_utils.py").write_text(
        "import pytest\nfrom src.utils import helper\n\ndef test_helper():\n    assert helper() == 42\n"
    )
    (root / "tests" / "test_api.py").write_text(
        "def test_health():\n    pass\n"
    )

    # Config and dependency files
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n\n"
        "[project]\nname = 'sample'\n\n"
        "[project.optional-dependencies]\ntest = ['pytest>=7']\n"
    )
    (root / "package.json").write_text(
        json.dumps({
            "name": "sample-frontend",
            "devDependencies": {"jest": "^29.0.0", "typescript": "^5.0.0"},
        }, indent=2)
    )

    # .gitignore with .env excluded
    (root / ".gitignore").write_text(".env\n*.pyc\nnode_modules/\n__pycache__/\n")

    # A file containing a fake secret (for secret scanner tests)
    (root / "src" / "config_bad.py").write_text(
        "# Bad practice — DO NOT commit real secrets\n"
        'API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456789"\n'
        'PASSWORD = "hunter2"\n'
    )

    # A large file (to test truncation)
    (root / "src" / "large_file.py").write_text("# padding\n" + "x = 1\n" * 3000)

    return root


# ---------------------------------------------------------------------------
# FileReaderTool
# ---------------------------------------------------------------------------

class TestFileReaderTool:
    def test_reads_existing_file(self, sample_repo):
        tool = FileReaderTool(repo_path=str(sample_repo))
        result = tool._run("src/main.py")
        assert "import os" in result
        assert "File: src/main.py" in result

    def test_truncates_large_file(self, sample_repo):
        tool = FileReaderTool(repo_path=str(sample_repo))
        result = tool._run("src/large_file.py")
        assert "TRUNCATED" in result

    def test_rejects_path_traversal(self, sample_repo):
        tool = FileReaderTool(repo_path=str(sample_repo))
        result = tool._run("../../etc/passwd")
        assert "Security Error" in result or "Error" in result

    def test_missing_file_returns_error(self, sample_repo):
        tool = FileReaderTool(repo_path=str(sample_repo))
        result = tool._run("nonexistent.py")
        assert "Error" in result or "not found" in result.lower()

    def test_directory_target_returns_error(self, sample_repo):
        tool = FileReaderTool(repo_path=str(sample_repo))
        result = tool._run("src")
        assert "Error" in result

    def test_invalid_repo_path(self, tmp_path):
        tool = FileReaderTool(repo_path=str(tmp_path / "does_not_exist"))
        result = tool._run("file.py")
        assert "Error" in result


# ---------------------------------------------------------------------------
# StructureAnalyserTool
# ---------------------------------------------------------------------------

class TestStructureAnalyserTool:
    def test_all_query_returns_files(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("all")
        assert "All files" in result
        assert "main.py" in result

    def test_test_category(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("test")
        assert "test_utils.py" in result
        assert "test_api.py" in result

    def test_config_category(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("config")
        assert "pyproject.toml" in result or "package.json" in result

    def test_entrypoint_category(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("entrypoint")
        assert "main.py" in result

    def test_extension_query(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run(".ts")
        assert "index.ts" in result or "utils.ts" in result or "users.ts" in result

    def test_unknown_category_returns_error(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("unknown_category")
        assert "Unknown" in result or "Valid categories" in result

    def test_dependency_category(self, sample_repo):
        tool = StructureAnalyserTool(repo_path=str(sample_repo))
        result = tool._run("dependency")
        assert "pyproject.toml" in result or "package.json" in result


# ---------------------------------------------------------------------------
# ImportGraphTool
# ---------------------------------------------------------------------------

class TestImportGraphTool:
    def test_python_outbound_imports(self, sample_repo):
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("src/main.py")
        assert "OUTBOUND IMPORTS" in result
        assert "os" in result

    def test_python_relative_import(self, sample_repo):
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("src/main.py")
        assert "utils" in result.lower()

    def test_inbound_importers(self, sample_repo):
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("src/utils.py")
        assert "INBOUND IMPORTERS" in result
        assert "test_utils.py" in result or "main.py" in result

    def test_typescript_imports(self, sample_repo):
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("frontend/index.ts")
        assert "OUTBOUND IMPORTS" in result
        assert "utils" in result or "express" in result

    def test_unsupported_extension(self, sample_repo):
        (sample_repo / "readme.md").write_text("# hello")
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("readme.md")
        assert "Unsupported" in result

    def test_path_traversal_rejected(self, sample_repo):
        tool = ImportGraphTool(repo_path=str(sample_repo))
        result = tool._run("../../some_file.py")
        assert "Security Error" in result or "Error" in result


# ---------------------------------------------------------------------------
# APIEndpointScannerTool
# ---------------------------------------------------------------------------

class TestAPIEndpointScannerTool:
    def test_finds_fastapi_routes(self, sample_repo):
        tool = APIEndpointScannerTool(repo_path=str(sample_repo))
        result = tool._run(framework="fastapi")
        assert "GET" in result
        assert "/health" in result
        assert "POST" in result
        assert "/items" in result

    def test_finds_express_routes(self, sample_repo):
        tool = APIEndpointScannerTool(repo_path=str(sample_repo))
        result = tool._run(framework="express")
        assert "/api/ping" in result

    def test_finds_nextjs_routes(self, sample_repo):
        tool = APIEndpointScannerTool(repo_path=str(sample_repo))
        result = tool._run(framework="nextjs")
        assert "users" in result.lower()
        assert "GET" in result
        assert "POST" in result

    def test_auto_detects_all(self, sample_repo):
        tool = APIEndpointScannerTool(repo_path=str(sample_repo))
        result = tool._run(framework="auto")
        assert "/health" in result

    def test_no_endpoints_message(self, tmp_path):
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()
        (empty_repo / "hello.py").write_text("print('hello')\n")
        tool = APIEndpointScannerTool(repo_path=str(empty_repo))
        result = tool._run(framework="fastapi")
        assert "No API endpoints found" in result


# ---------------------------------------------------------------------------
# SecretScannerTool
# ---------------------------------------------------------------------------

class TestSecretScannerTool:
    def test_detects_fake_openai_key(self, sample_repo):
        tool = SecretScannerTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "OpenAI API Key" in result or "CRITICAL" in result or "HIGH" in result

    def test_gitignore_check_passes(self, sample_repo):
        tool = SecretScannerTool(repo_path=str(sample_repo))
        result = tool._run()
        assert ".env files are excluded" in result or "OK" in result

    def test_gitignore_check_warns_when_missing(self, tmp_path):
        repo = tmp_path / "nogi"
        repo.mkdir()
        (repo / "app.py").write_text('KEY = "sk-1234567890abcdefghijklmnop"\n')
        tool = SecretScannerTool(repo_path=str(repo))
        result = tool._run()
        assert "No .gitignore" in result or "WARNING" in result

    def test_no_findings_on_clean_file(self, tmp_path):
        repo = tmp_path / "clean"
        repo.mkdir()
        (repo / ".gitignore").write_text(".env\n")
        (repo / "app.py").write_text("def hello():\n    return 'world'\n")
        tool = SecretScannerTool(repo_path=str(repo))
        result = tool._run()
        assert "No secrets detected" in result

    def test_summary_section_present(self, sample_repo):
        tool = SecretScannerTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "SUMMARY" in result
        assert "CRITICAL" in result

    def test_include_low_flag(self, sample_repo):
        tool = SecretScannerTool(repo_path=str(sample_repo))
        result_high = tool._run(include_low=False)
        result_low = tool._run(include_low=True)
        assert len(result_low) >= len(result_high)


# ---------------------------------------------------------------------------
# TestCoverageTool
# ---------------------------------------------------------------------------

class TestTestCoverageTool:
    def test_finds_test_files(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "test_utils.py" in result
        assert "test_api.py" in result

    def test_calculates_ratio(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "Test/source ratio" in result

    def test_detects_pytest_framework(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "pytest" in result.lower() or "pyproject.toml" in result

    def test_detects_jest_framework(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "jest" in result.lower() or "Jest" in result

    def test_identifies_test_directory(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "tests" in result

    def test_no_tests_repo(self, tmp_path):
        repo = tmp_path / "notest"
        repo.mkdir()
        (repo / "app.py").write_text("def main(): pass\n")
        tool = TestCoverageTool(repo_path=str(repo))
        result = tool._run()
        assert "no test files" in result.lower() or "NONE" in result

    def test_assessment_section_present(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "ASSESSMENT" in result

    def test_config_files_detected(self, sample_repo):
        tool = TestCoverageTool(repo_path=str(sample_repo))
        result = tool._run()
        assert "pyproject.toml" in result


# ---------------------------------------------------------------------------
# Integration — all tools accept repo_path at construction
# ---------------------------------------------------------------------------

class TestToolsIntegration:
    def test_all_tools_run_without_exception(self, sample_repo):
        repo = str(sample_repo)
        FileReaderTool(repo_path=repo)._run("src/main.py")
        StructureAnalyserTool(repo_path=repo)._run("all")
        ImportGraphTool(repo_path=repo)._run("src/utils.py")
        APIEndpointScannerTool(repo_path=repo)._run(framework="auto")
        SecretScannerTool(repo_path=repo)._run()
        TestCoverageTool(repo_path=repo)._run()
        assert True
