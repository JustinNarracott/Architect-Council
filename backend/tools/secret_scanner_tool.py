"""Secret scanner tool — detect potential secrets, tokens, and credentials in a repo."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", ".nuxt", "venv", ".venv", "vendor",
    "coverage", ".tox",
}

# Extensions to scan (text files only)
SCAN_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".go", ".rb", ".java", ".php", ".sh", ".bash",
    ".env", ".cfg", ".ini", ".toml", ".yaml", ".yml",
    ".json", ".xml", ".properties", ".conf", ".config",
    ".tf", ".tfvars",  # Terraform
}

# Files that commonly store secrets intentionally and should be reported but not alarmed
KNOWN_SECRET_FILES = {".env", ".env.local", ".env.production", ".env.staging"}


@dataclass
class SecretFinding:
    file: str
    line: int
    pattern_name: str
    severity: str
    snippet: str  # redacted line excerpt


# ------------------------------------------------------------------
# Secret patterns — ordered by severity (CRITICAL → LOW)
# ------------------------------------------------------------------
SECRET_PATTERNS = [
    # AWS
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}"), "CRITICAL"),
    ("AWS Secret Access Key", re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"][0-9a-zA-Z/+]{40}['\"]"), "CRITICAL"),
    # OpenAI / Anthropic / Google AI
    ("OpenAI API Key", re.compile(r"\bsk-[a-zA-Z0-9]{20,}"), "CRITICAL"),
    ("Anthropic API Key", re.compile(r"\bsk-ant-[a-zA-Z0-9\-_]{32,}"), "CRITICAL"),
    # Stripe
    ("Stripe Secret Key", re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}"), "CRITICAL"),
    ("Stripe Publishable Key", re.compile(r"\bpk_live_[0-9a-zA-Z]{24,}"), "HIGH"),
    # GitHub / GitLab tokens
    ("GitHub Token", re.compile(r"\bghp_[0-9a-zA-Z]{36,}"), "CRITICAL"),
    ("GitHub OAuth Token", re.compile(r"\bgho_[0-9a-zA-Z]{36,}"), "CRITICAL"),
    ("GitLab Token", re.compile(r"\bglpat-[0-9a-zA-Z\-_]{20,}"), "CRITICAL"),
    # Generic JWT
    ("JWT Token", re.compile(r"\beyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+"), "HIGH"),
    # Connection strings
    ("DB Connection String", re.compile(
        r"(?i)(?:mongodb|postgresql|mysql|redis|amqp|mssql)://[^'\"\s]{8,}"
    ), "CRITICAL"),
    ("Connection String with password", re.compile(
        r"(?i)(?:Password|Pwd)=[^;'\"\s]{4,}"
    ), "HIGH"),
    # Generic private key patterns
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "CRITICAL"),
    # Generic API key assignment patterns
    ("Generic API Key Assignment", re.compile(
        r"""(?i)(?:api[_\-]?key|apikey|secret[_\-]?key|access[_\-]?token|auth[_\-]?token)\s*[=:]\s*['"][a-zA-Z0-9\-_./+]{16,}['"]"""
    ), "HIGH"),
    # Password in config
    ("Hardcoded Password", re.compile(
        r"""(?i)password\s*[=:]\s*['"](?!.*\{)[^'"]{6,}['"]"""
    ), "MEDIUM"),
    # Slack / Discord webhook URLs
    ("Slack Webhook", re.compile(r"https://hooks\.slack\.com/services/[A-Z0-9/]+"), "HIGH"),
    ("Discord Webhook", re.compile(r"https://discord(?:app)?\.com/api/webhooks/[0-9]+/[a-zA-Z0-9\-_]+"), "HIGH"),
    # Google API keys
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}"), "HIGH"),
    # Twilio
    ("Twilio Auth Token", re.compile(r"\bSK[0-9a-f]{32}\b"), "HIGH"),
    # Generic long hex/base64 that looks like a secret
    ("Potential Secret (long hex)", re.compile(
        r"""(?i)(?:secret|token|key|passwd)\s*[=:]\s*['"][0-9a-fA-F]{32,}['"]"""
    ), "LOW"),
]

# Patterns that are just placeholder/example values — skip these
SAFE_PLACEHOLDER_PATTERN = re.compile(
    r"(?i)(?:your[_\-]?|example|placeholder|<|>|\[|]|xxx|changeme|replace|todo|fixme|test|fake|dummy)",
)


class SecretScannerInput(BaseModel):
    """Input schema for secret scanning."""

    include_low: bool = Field(
        default=False,
        description="Include LOW severity findings (default: False, only HIGH and CRITICAL)",
    )


class SecretScannerTool(BaseTool):
    """Scans a cloned repo for hardcoded secrets, tokens, and credentials."""

    name: str = "Secret Scanner"
    description: str = (
        "Scan the repository being reviewed for potential secrets, API keys, tokens, passwords, "
        "and connection strings. Also checks whether .env files are excluded via .gitignore. "
        "Returns findings with file path, line number, pattern type, and severity. "
        "Use this to assess the security hygiene of a codebase."
    )
    args_schema: Type[BaseModel] = SecretScannerInput
    repo_path: str = Field(default="", description="Absolute path to the cloned repo root (set at construction)")

    def __init__(self, repo_path: str = "", **kwargs):
        super().__init__(repo_path=repo_path, **kwargs)

    def _run(self, include_low: bool = False) -> str:
        """Scan the repo for secrets."""
        try:
            repo_root = Path(self.repo_path).resolve()
            if not repo_root.exists() or not repo_root.is_dir():
                return f"Error: repo_path '{self.repo_path}' does not exist or is not a directory."

            findings: list[SecretFinding] = []
            gitignore_status = self._check_gitignore(repo_root)

            for dirpath, dirnames, filenames in os.walk(repo_root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fname in filenames:
                    fpath = Path(dirpath) / fname
                    if fpath.suffix.lower() not in SCAN_EXTENSIONS and fname not in KNOWN_SECRET_FILES:
                        continue
                    rel = str(fpath.relative_to(repo_root)).replace("\\", "/")
                    findings.extend(self._scan_file(fpath, rel))

            # Filter by severity
            if not include_low:
                findings = [f for f in findings if f.severity in ("CRITICAL", "HIGH", "MEDIUM")]

            # Sort: CRITICAL first
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            findings.sort(key=lambda f: (severity_order.get(f.severity, 9), f.file, f.line))

            lines = [
                "Secret Scan Report",
                "=" * 60,
                "",
                f"GITIGNORE CHECK",
                "-" * 40,
            ]
            lines += gitignore_status
            lines += [
                "",
                f"FINDINGS ({len(findings)} total)",
                "-" * 40,
            ]

            if not findings:
                lines.append("No secrets detected.")
            else:
                for f in findings:
                    lines.append(
                        f"[{f.severity}] {f.pattern_name}"
                        f"\n  File:    {f.file}:{f.line}"
                        f"\n  Snippet: {f.snippet}"
                    )
                    lines.append("")

            # Summary counts
            counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for f in findings:
                counts[f.severity] = counts.get(f.severity, 0) + 1

            lines += [
                "SUMMARY",
                "-" * 40,
                f"  CRITICAL: {counts['CRITICAL']}",
                f"  HIGH:     {counts['HIGH']}",
                f"  MEDIUM:   {counts['MEDIUM']}",
                f"  LOW:      {counts['LOW']}",
            ]

            return "\n".join(lines)

        except Exception as e:
            return f"Error running secret scan: {str(e)}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_gitignore(self, repo_root: Path) -> list[str]:
        """Check whether .env files are properly excluded via .gitignore."""
        gitignore_path = repo_root / ".gitignore"
        results: list[str] = []

        if not gitignore_path.exists():
            results.append("WARNING: No .gitignore found at repo root.")
            return results

        try:
            gitignore_content = gitignore_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            results.append("WARNING: Could not read .gitignore.")
            return results

        env_excluded = bool(re.search(r"^\.env", gitignore_content, re.MULTILINE))
        env_star_excluded = bool(re.search(r"^\.env\*", gitignore_content, re.MULTILINE))

        if env_excluded or env_star_excluded:
            results.append("OK: .env files are excluded in .gitignore.")
        else:
            results.append("WARNING: .env files are NOT excluded in .gitignore — risk of secret exposure.")

        # Check if any .env files actually exist in the repo
        env_files = list(repo_root.glob(".env*"))
        env_files = [f for f in env_files if f.is_file()]
        if env_files:
            if env_excluded or env_star_excluded:
                results.append(
                    f"NOTE: {len(env_files)} .env file(s) found locally (expected — excluded from git)."
                )
            else:
                results.append(
                    f"CRITICAL: {len(env_files)} .env file(s) found and NOT excluded from git: "
                    + ", ".join(f.name for f in env_files)
                )
        else:
            results.append("OK: No .env files found at repo root.")

        return results

    def _scan_file(self, fpath: Path, rel: str) -> list[SecretFinding]:
        findings: list[SecretFinding] = []
        try:
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return findings

        for lineno, line in enumerate(lines, 1):
            # Skip comment-only lines
            stripped = line.strip()
            if stripped.startswith(("#", "//", "*", "<!--")):
                continue

            for pattern_name, pattern, severity in SECRET_PATTERNS:
                if pattern.search(line):
                    # Skip if it looks like a placeholder / example
                    if SAFE_PLACEHOLDER_PATTERN.search(line):
                        continue
                    # Redact the sensitive value in the snippet
                    snippet = self._redact(line.strip()[:120])
                    findings.append(
                        SecretFinding(
                            file=rel,
                            line=lineno,
                            pattern_name=pattern_name,
                            severity=severity,
                            snippet=snippet,
                        )
                    )
                    # One finding per line per pattern is enough
                    break

        return findings

    @staticmethod
    def _redact(line: str) -> str:
        """Partially redact potential secret values for display."""
        # Replace long alphanumeric sequences (likely token values) with partial redaction
        return re.sub(
            r"""(['"=:\s])([a-zA-Z0-9\-_./+]{8,})""",
            lambda m: m.group(1) + m.group(2)[:4] + "****",
            line,
        )
