"""Test coverage tool — assess test presence, frameworks, and source-to-test ratio."""

import os
import re
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", ".nuxt", "venv", ".venv", "vendor",
    "coverage", ".tox", ".mypy_cache",
}

SOURCE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rb", ".java"}
TEST_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rb", ".java"}

# Test file name patterns
TEST_FILE_PATTERNS = [
    re.compile(r"^test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.test\.(ts|tsx|js|jsx|mjs)$"),
    re.compile(r".*\.spec\.(ts|tsx|js|jsx|mjs)$"),
    re.compile(r".*_test\.go$"),
    re.compile(r".*Test\.java$"),
    re.compile(r".*_spec\.rb$"),
]

# Test directories
TEST_DIR_NAMES = {"tests", "test", "__tests__", "spec", "specs", "e2e"}

# Test framework config files
TEST_CONFIG_FILES = {
    # Python
    "pytest.ini": "pytest",
    "setup.cfg": "pytest (setup.cfg)",
    "pyproject.toml": "pytest/unittest (pyproject.toml)",
    "tox.ini": "tox",
    "conftest.py": "pytest (conftest)",
    # JavaScript / TypeScript
    "jest.config.js": "Jest",
    "jest.config.ts": "Jest",
    "jest.config.mjs": "Jest",
    "jest.config.cjs": "Jest",
    "vitest.config.ts": "Vitest",
    "vitest.config.js": "Vitest",
    "vitest.config.mjs": "Vitest",
    ".mocharc.js": "Mocha",
    ".mocharc.yml": "Mocha",
    ".mocharc.json": "Mocha",
    "karma.conf.js": "Karma",
    "cypress.config.ts": "Cypress",
    "cypress.config.js": "Cypress",
    "playwright.config.ts": "Playwright",
    "playwright.config.js": "Playwright",
    # Go
    # Go tests are always in *_test.go files, no separate config needed
    # Ruby
    ".rspec": "RSpec",
    "spec_helper.rb": "RSpec",
}

# Framework detection patterns within package.json / pyproject.toml
FRAMEWORK_KEYWORDS = {
    "jest": "Jest",
    "vitest": "Vitest",
    "mocha": "Mocha",
    "jasmine": "Jasmine",
    "cypress": "Cypress",
    "playwright": "Playwright",
    "pytest": "pytest",
    "unittest": "unittest",
    "nose": "nose",
    "rspec": "RSpec",
    "minitest": "Minitest",
}


class TestCoverageInput(BaseModel):
    """Input schema for test coverage assessment."""

    # No inputs needed — repo_path is bound at construction time
    pass


class TestCoverageTool(BaseTool):
    """Assesses test presence, frameworks, and coverage ratios in a cloned repo."""

    # Prevent pytest from trying to collect this class as a test suite
    __test__ = False

    name: str = "Test Coverage"
    description: str = (
        "Assess the testing setup of the repository being reviewed. "
        "Finds test files, detects test frameworks (pytest, Jest, Vitest, Mocha, etc.), "
        "locates test configuration files, and calculates the ratio of test files "
        "to source files. Returns a structured summary of testing coverage quality."
    )
    args_schema: Type[BaseModel] = TestCoverageInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self) -> str:
        """Analyse test coverage in the repo."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            source_files: list[Path] = []
            test_files: list[Path] = []
            config_found: dict[str, str] = {}  # filename → framework
            test_dirs_found: set[str] = set()

            for dirpath, dirnames, filenames in os.walk(repo_root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

                dir_name = Path(dirpath).name.lower()
                if dir_name in TEST_DIR_NAMES:
                    rel_dir = str(Path(dirpath).relative_to(repo_root)).replace("\\", "/")
                    test_dirs_found.add(rel_dir)

                for fname in filenames:
                    fpath = Path(dirpath) / fname
                    suffix = fpath.suffix.lower()
                    rel = str(fpath.relative_to(repo_root)).replace("\\", "/")

                    # Check for test config files
                    if fname in TEST_CONFIG_FILES:
                        config_found[fname] = TEST_CONFIG_FILES[fname]

                    if suffix not in SOURCE_EXTENSIONS:
                        continue

                    if self._is_test_file(fname, rel):
                        test_files.append(fpath)
                    else:
                        source_files.append(fpath)

            # Detect frameworks from config file content
            detected_frameworks = self._detect_frameworks(repo_root, config_found)

            # Calculate ratio
            n_source = len(source_files)
            n_test = len(test_files)
            ratio = (n_test / n_source) if n_source > 0 else 0.0

            # Coverage quality rating
            rating = self._rate_coverage(ratio, n_test, detected_frameworks)

            lines = [
                "Test Coverage Report",
                "=" * 60,
                "",
                "OVERVIEW",
                "-" * 40,
                f"Source files:    {n_source}",
                f"Test files:      {n_test}",
                f"Test/source ratio: {ratio:.2f} ({ratio * 100:.0f}%)",
                f"Coverage rating: {rating}",
                "",
                "TEST DIRECTORIES",
                "-" * 40,
            ]
            if test_dirs_found:
                for td in sorted(test_dirs_found):
                    lines.append(f"  {td}/")
            else:
                lines.append("  (no dedicated test directories found)")

            lines += [
                "",
                "DETECTED FRAMEWORKS",
                "-" * 40,
            ]
            if detected_frameworks:
                for fw in sorted(detected_frameworks):
                    lines.append(f"  {fw}")
            else:
                lines.append("  (none detected)")

            lines += [
                "",
                "TEST CONFIG FILES",
                "-" * 40,
            ]
            if config_found:
                for fname, fw in sorted(config_found.items()):
                    lines.append(f"  {fname}  ({fw})")
            else:
                lines.append("  (none found)")

            lines += [
                "",
                "TEST FILES (first 30)",
                "-" * 40,
            ]
            for tf in sorted(test_files)[:30]:
                rel = str(tf.relative_to(repo_root)).replace("\\", "/")
                lines.append(f"  {rel}")
            if n_test > 30:
                lines.append(f"  ... and {n_test - 30} more")

            lines += [
                "",
                "ASSESSMENT",
                "-" * 40,
            ]
            lines += self._assessment(ratio, n_test, detected_frameworks, config_found)

            return "\n".join(lines)

        except Exception as e:
            return f"Error assessing test coverage: {str(e)}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_test_file(self, fname: str, rel_path: str) -> bool:
        """Determine whether a file is a test file."""
        for pattern in TEST_FILE_PATTERNS:
            if pattern.match(fname):
                return True
        # File inside a test directory
        parts = rel_path.lower().split("/")
        for part in parts[:-1]:
            if part in TEST_DIR_NAMES:
                return True
        return False

    def _detect_frameworks(
        self, repo_root: Path, config_found: dict[str, str]
    ) -> set[str]:
        """Detect test frameworks from config files and package manifests."""
        frameworks: set[str] = set()

        # From config file presence
        for framework in config_found.values():
            # Strip parenthetical notes
            fw_clean = framework.split("(")[0].strip()
            frameworks.add(fw_clean)

        # Parse package.json for test dependencies
        pkg_json = repo_root / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
                all_deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                    **data.get("peerDependencies", {}),
                }
                for dep in all_deps:
                    dep_lower = dep.lower()
                    for keyword, fw_name in FRAMEWORK_KEYWORDS.items():
                        if keyword in dep_lower:
                            frameworks.add(fw_name)
            except Exception:
                pass

        # Parse pyproject.toml for test dependencies
        pyproject = repo_root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="replace")
                for keyword, fw_name in FRAMEWORK_KEYWORDS.items():
                    if re.search(rf"\b{keyword}\b", content, re.IGNORECASE):
                        frameworks.add(fw_name)
            except Exception:
                pass

        # Parse requirements.txt variants
        for req_file in repo_root.glob("requirements*.txt"):
            try:
                content = req_file.read_text(encoding="utf-8", errors="replace")
                for keyword, fw_name in FRAMEWORK_KEYWORDS.items():
                    if re.search(rf"\b{keyword}\b", content, re.IGNORECASE):
                        frameworks.add(fw_name)
            except Exception:
                pass

        return frameworks

    @staticmethod
    def _rate_coverage(ratio: float, n_test: int, frameworks: set[str]) -> str:
        if n_test == 0:
            return "NONE — no test files found"
        if ratio >= 0.5 and frameworks:
            return "GOOD — solid test presence with framework"
        if ratio >= 0.25:
            return "FAIR — moderate test coverage"
        if ratio >= 0.1:
            return "LOW — limited test coverage"
        return "MINIMAL — very few tests relative to source"

    @staticmethod
    def _assessment(
        ratio: float,
        n_test: int,
        frameworks: set[str],
        config_found: dict[str, str],
    ) -> list[str]:
        lines: list[str] = []
        if n_test == 0:
            lines.append("  CONCERN: No test files found. Consider adding unit tests.")
        elif ratio < 0.1:
            lines.append(f"  CONCERN: Test ratio is very low ({ratio:.0%}). Significant testing gaps likely.")
        elif ratio < 0.25:
            lines.append(f"  NOTE: Test ratio of {ratio:.0%} is below recommended 25-50%.")
        else:
            lines.append(f"  OK: Test ratio of {ratio:.0%} is acceptable.")

        if not frameworks:
            lines.append("  CONCERN: No test framework detected. Testing infrastructure may be absent.")
        else:
            lines.append(f"  OK: Framework(s) detected: {', '.join(sorted(frameworks))}")

        if not config_found:
            lines.append("  NOTE: No test configuration files found.")
        else:
            lines.append(f"  OK: Test configuration present ({', '.join(sorted(config_found.keys()))}).")

        return lines
