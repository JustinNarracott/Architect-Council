"""Import graph tool — analyse what a file imports and what imports it."""

import ast
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

# Regex patterns for TS/JS imports
_TS_IMPORT_PATTERNS = [
    re.compile(r"""^\s*import\s+.*?\s+from\s+['"](.+?)['"]""", re.MULTILINE),
    re.compile(r"""^\s*import\s+['"](.+?)['"]""", re.MULTILINE),
    re.compile(r"""require\s*\(\s*['"](.+?)['"]\s*\)"""),
    re.compile(r"""^\s*export\s+.*?\s+from\s+['"](.+?)['"]""", re.MULTILINE),
]


class ImportGraphInput(BaseModel):
    """Input schema for import graph analysis."""

    file_path: str = Field(
        ...,
        description="Relative path to the file to analyse (e.g. 'src/main.py')",
    )


class ImportGraphTool(BaseTool):
    """Analyses imports for a given file — what it imports and what imports it."""

    name: str = "Import Graph"
    description: str = (
        "Analyse the import relationships of a file in the repository being reviewed. "
        "Returns: (1) what the file imports, (2) which other files in the repo import it. "
        "Supports Python (via AST) and TypeScript/JavaScript (via regex). "
        "Use this to understand coupling and dependency flow."
    )
    args_schema: Type[BaseModel] = ImportGraphInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self, file_path: str) -> str:
        """Analyse imports for the given file."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            target = (repo_root / file_path).resolve()
            try:
                target.relative_to(repo_root)
            except ValueError:
                return "Security Error: Path resolves outside the repo root."

            if not target.exists() or not target.is_file():
                return f"Error: File '{file_path}' not found."

            suffix = target.suffix.lower()

            if suffix == ".py":
                outbound = self._python_imports(target)
            elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                outbound = self._ts_js_imports(target)
            else:
                return (
                    f"Unsupported file type '{suffix}'. "
                    "Import analysis supports: .py, .ts, .tsx, .js, .jsx"
                )

            # Find what imports this file (reverse lookup across repo)
            rel_target = target.relative_to(repo_root)
            inbound = self._find_importers(repo_root, rel_target, suffix)

            lines = [
                f"Import Graph: {file_path}",
                "=" * 60,
                "",
                f"OUTBOUND IMPORTS ({len(outbound)})",
                "-" * 40,
            ]
            if outbound:
                for imp in sorted(outbound):
                    lines.append(f"  {imp}")
            else:
                lines.append("  (none detected)")

            lines += [
                "",
                f"INBOUND IMPORTERS — files that import this module ({len(inbound)})",
                "-" * 40,
            ]
            if inbound:
                for imp_file in sorted(inbound):
                    lines.append(f"  {imp_file}")
            else:
                lines.append("  (not imported by any scanned file)")

            return "\n".join(lines)

        except Exception as e:
            return f"Error analysing import graph for '{file_path}': {str(e)}"

    # ------------------------------------------------------------------
    # Python import extraction via AST
    # ------------------------------------------------------------------

    def _python_imports(self, path: Path) -> list[str]:
        """Extract import names from a Python file using the AST."""
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            # Fall back to regex for invalid Python
            return self._python_imports_regex(path)

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level  # relative import dots
                prefix = "." * level
                imports.append(f"{prefix}{module}" if module else prefix)
        return imports

    def _python_imports_regex(self, path: Path) -> list[str]:
        source = path.read_text(encoding="utf-8", errors="replace")
        pattern = re.compile(
            r"^\s*(?:import\s+([\w.,\s]+)|from\s+(\.+[\w.]*|[\w.]+)\s+import)",
            re.MULTILINE,
        )
        imports: list[str] = []
        for m in pattern.finditer(source):
            name = m.group(1) or m.group(2)
            if name:
                imports.append(name.strip())
        return imports

    # ------------------------------------------------------------------
    # TypeScript / JavaScript import extraction via regex
    # ------------------------------------------------------------------

    def _ts_js_imports(self, path: Path) -> list[str]:
        source = path.read_text(encoding="utf-8", errors="replace")
        imports: set[str] = set()
        for pattern in _TS_IMPORT_PATTERNS:
            for m in pattern.finditer(source):
                imports.add(m.group(1))
        return list(imports)

    # ------------------------------------------------------------------
    # Reverse lookup — who imports the target file?
    # ------------------------------------------------------------------

    def _find_importers(
        self,
        repo_root: Path,
        rel_target: Path,
        target_suffix: str,
    ) -> list[str]:
        """Search the repo for files that import the target module."""
        importers: list[str] = []

        # Build candidate module references for the target
        # e.g. "src/utils/helpers.py" → "src.utils.helpers", "utils.helpers", "helpers"
        parts_no_suffix = rel_target.with_suffix("").parts
        py_module_variants = set()
        for i in range(len(parts_no_suffix)):
            py_module_variants.add(".".join(parts_no_suffix[i:]))
        # Also handle __init__ stripping
        if parts_no_suffix and parts_no_suffix[-1] == "__init__":
            for i in range(len(parts_no_suffix) - 1):
                py_module_variants.add(".".join(parts_no_suffix[i:-1]))

        # For TS/JS: relative path references like './utils', '../utils/helpers'
        stem = rel_target.stem
        ts_name_variants = {stem, f"./{stem}", f"../{stem}"}
        # Also the full relative path stem
        ts_name_variants.add(str(rel_target.with_suffix("")).replace("\\", "/"))

        scan_exts_for_target: set[str]
        if target_suffix == ".py":
            scan_exts_for_target = {".py"}
        else:
            scan_exts_for_target = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

        for dirpath, dirnames, filenames in os.walk(repo_root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix.lower() not in scan_exts_for_target:
                    continue
                # Don't report the file as its own importer
                if fpath.resolve() == (repo_root / rel_target).resolve():
                    continue
                try:
                    source = fpath.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                found = False
                if target_suffix == ".py":
                    for variant in py_module_variants:
                        # import X or from X import ...
                        if re.search(
                            rf"(?:^|\s)(?:import\s+{re.escape(variant)}|from\s+{re.escape(variant)}\s+import)",
                            source,
                            re.MULTILINE,
                        ):
                            found = True
                            break
                else:
                    for variant in ts_name_variants:
                        if re.search(
                            rf"""['"]{re.escape(variant)}['"]""",
                            source,
                        ):
                            found = True
                            break

                if found:
                    importers.append(str(fpath.relative_to(repo_root)))

        return importers
