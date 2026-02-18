"""Codebase review crew configuration."""

from collections.abc import Callable
from typing import Any

from crewai import Crew, Process, Task

from backend.agents import (
    get_da_chair_codebase,
    get_dx_analyst_codebase,
    get_enterprise_architect_codebase,
    get_security_analyst_codebase,
    get_standards_analyst_codebase,
)
from backend.governance import load_governance
from backend.governance.formatter import (
    format_for_standards,
    format_for_dx,
    format_for_architecture,
    format_for_security,
    format_for_chair,
)
from backend.indexer import IndexedRepo

# Map agent roles to frontend agent IDs (same as ADR crew)
ROLE_TO_AGENT_ID = {
    "Standards Analyst": "standards_analyst",
    "Developer Experience Analyst": "dx_analyst",
    "Enterprise Architect": "enterprise_architect",
    "Security & Resilience Analyst": "security_analyst",
    "Design Authority Chair": "da_chair",
}


def _format_repo_metadata(repo: IndexedRepo) -> str:
    """Format IndexedRepo metadata for injection into task descriptions."""
    lang_summary = ", ".join(
        f"{lb['extension']} ({lb['count']} files)"
        for lb in repo.language_breakdown[:8]
    )
    dep_summary = ", ".join(
        f"{d['name']}=={d['version']}" if d.get("version") else d["name"]
        for d in repo.dependencies[:20]
    )
    key_files_summary = "\n".join(
        f"  - {name}: {path}" for name, path in repo.key_files.items()
    )

    return (
        f"Repository: {repo.repo_url}\n"
        f"Total files: {repo.total_files} | Estimated LOC: {repo.total_loc:,}\n"
        f"Languages: {lang_summary or 'none detected'}\n"
        f"Key files detected:\n{key_files_summary or '  (none)'}\n"
        f"Dependencies ({len(repo.dependencies)} total): {dep_summary or 'none'}\n\n"
        f"Directory structure (top 3 levels):\n{repo.directory_tree}"
    )


def create_codebase_crew(
    repo_url: str,
    clone_path: str,
    repo_metadata: IndexedRepo,
    task_callback: Callable[[Any], None] | None = None,
) -> Crew:
    """
    Create a codebase review crew for the given indexed repository.

    Args:
        repo_url:      HTTPS URL of the repository being analysed.
        clone_path:    Absolute path to the locally cloned repo directory.
        repo_metadata: Fully indexed repository data from the ingestion pipeline.
        task_callback: Optional callback invoked when each agent task completes.

    Returns:
        Configured Crew ready for execution via kickoff().
    """
    # Get codebase-variant agent instances
    standards_analyst = get_standards_analyst_codebase(clone_path)
    dx_analyst = get_dx_analyst_codebase(clone_path)
    enterprise_architect = get_enterprise_architect_codebase(clone_path)
    security_analyst = get_security_analyst_codebase(clone_path)
    da_chair = get_da_chair_codebase()

    # Shared context injected into every task
    meta = _format_repo_metadata(repo_metadata)

    # Load governance config once — empty config = graceful degradation (no change in behaviour)
    governance = load_governance()

    # ── Task 1: Standards Analysis ─────────────────────────────────────────────
    standards_task = Task(
        description=(
            f"Review the codebase at '{repo_url}' for code structure, naming conventions, "
            f"dependency health, and linting/formatter configuration.\n\n"
            f"## Repository Metadata\n{meta}\n\n"
            f"{format_for_standards(governance)}\n"
            "Your analysis must include:\n"
            "1. **Code structure** — Is the project layout logical? Are concerns well-separated? "
            "Are there clear layers (controllers, services, models, utils)?\n"
            "2. **Naming conventions** — Are files, modules, functions, and variables named consistently "
            "and descriptively? Are language-specific conventions followed?\n"
            "3. **Dependency health** — Are dependencies up-to-date? Are there known vulnerable versions? "
            "Is there a mix of dev/prod dependencies that suggests poor hygiene?\n"
            "4. **Linting and formatting** — Is there a linting config (eslint, ruff, flake8, golangci-lint)? "
            "A formatter (prettier, black, gofmt)? Evidence the tooling is actively enforced?\n"
            "5. **Pattern compliance** — Are established design patterns used correctly? Are there obvious "
            "anti-patterns (god classes, deeply nested logic, magic numbers, copy-paste code)?\n"
            "6. **Code quality signals** — Dead code, TODO/FIXME density, commented-out blocks.\n\n"
            "Use your tools to read key source files and the directory structure. "
            "Cite specific files and line numbers in your findings.\n\n"
            "Conclude with a score (0-100) where 100 = exemplary standards compliance."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Standards Compliance Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Code Structure\n\n"
            "[Assessment of project layout, separation of concerns, layering]\n\n"
            "## Naming Conventions\n\n"
            "| Scope | Convention Expected | Compliant? | Notes |\n"
            "|-------|-------------------|------------|-------|\n"
            "| Files (Python) | snake_case | ✅/❌ | ... |\n"
            "| Files (TypeScript) | kebab-case | ✅/❌ | ... |\n"
            "| React Components | PascalCase | ✅/❌ | ... |\n"
            "| Functions | snake_case / camelCase | ✅/❌ | ... |\n"
            "| Classes | PascalCase | ✅/❌ | ... |\n\n"
            "[Add rows as needed for findings]\n\n"
            "## Dependency Health\n\n"
            "| Package | Version | Status | Notes |\n"
            "|---------|---------|--------|-------|\n"
            "| ... | ... | ✅ Current / ⚠️ Outdated / 🔴 Vulnerable | ... |\n\n"
            "## Linting & Formatting\n\n"
            "| Tool Type | Tool Found | Enforced? | Notes |\n"
            "|-----------|-----------|-----------|-------|\n"
            "| Linter | ... | ✅/❌ | ... |\n"
            "| Formatter | ... | ✅/❌ | ... |\n"
            "| Type Checker | ... | ✅/❌ | ... |\n"
            "| Pre-commit | ... | ✅/❌ | ... |\n\n"
            "## Anti-Patterns & Violations\n\n"
            "| # | Finding | Severity | File | Line | Description |\n"
            "|---|---------|----------|------|------|-------------|\n"
            "| 1 | ... | CRITICAL/HIGH/MEDIUM/LOW | path/to/file.py | 42 | ... |\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=standards_analyst,
        async_execution=True,
    )

    # ── Task 2: DX Analysis ────────────────────────────────────────────────────
    # NOTE: DX Analyst has tools=[] (Perplexity limitation). All repo context
    # must be injected directly into the task description.
    dx_task = Task(
        description=(
            f"Evaluate the developer experience of the codebase at '{repo_url}'.\n\n"
            f"## Repository Metadata\n{meta}\n\n"
            f"{format_for_dx(governance)}\n"
            "Using ONLY the repository metadata above (you cannot call tools), assess:\n"
            "1. **README quality** — Is there a README? Does it cover: what the project does, "
            "how to install/run it locally, how to run tests, how to contribute?\n"
            "2. **Documentation** — Is there a docs/ directory or inline docstrings? "
            "Are complex modules explained? Is there an ADR or architectural decision log?\n"
            "3. **Test coverage signals** — Are there test files? What testing frameworks are configured? "
            "What is the ratio of test files to source files?\n"
            "4. **Onboarding complexity** — How many steps does it take to run this locally? "
            "Are there Docker/compose files? Is the setup automated?\n"
            "5. **Community health** — Based on the repo URL and structure, assess: Is this a "
            "well-maintained project or an abandoned one? Are there contribution guidelines? "
            "A changelog? CI/CD configuration?\n"
            "6. **Developer tooling** — Are there pre-commit hooks, make targets, task runners, "
            "or scripts that help developers?\n\n"
            "Conclude with a score (0-100) where 100 = zero onboarding friction."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Developer Experience Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## README Quality\n\n"
            "| Criterion | Present? | Quality | Notes |\n"
            "|-----------|----------|---------|-------|\n"
            "| Project description | ✅/❌ | Good/Fair/Poor | ... |\n"
            "| Installation guide | ✅/❌ | ... | ... |\n"
            "| Usage examples | ✅/❌ | ... | ... |\n"
            "| Contributing guide | ✅/❌ | ... | ... |\n"
            "| License | ✅/❌ | ... | ... |\n\n"
            "## Documentation\n\n"
            "[Assessment of docs/ directory, inline docstrings, ADRs, changelogs]\n\n"
            "## Test Coverage\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| Test files found | X |\n"
            "| Source files | Y |\n"
            "| Test:Source ratio | X:Y |\n"
            "| Testing frameworks | ... |\n"
            "| CI integration | ✅/❌ |\n\n"
            "## Onboarding Complexity\n\n"
            "| Step | Description | Automated? |\n"
            "|------|-------------|------------|\n"
            "| 1 | ... | ✅/❌ |\n\n"
            "**Estimated time to first run:** X minutes\n\n"
            "## Developer Tooling\n\n"
            "| Tool | Present? | Notes |\n"
            "|------|----------|-------|\n"
            "| Pre-commit hooks | ✅/❌ | ... |\n"
            "| Make/Task runner | ✅/❌ | ... |\n"
            "| Docker/Compose | ✅/❌ | ... |\n"
            "| CI/CD config | ✅/❌ | ... |\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=dx_analyst,
        async_execution=True,
    )

    # ── Task 3: Enterprise Architecture Analysis ───────────────────────────────
    enterprise_task = Task(
        description=(
            f"Analyse the architectural structure of the codebase at '{repo_url}'.\n\n"
            f"## Repository Metadata\n{meta}\n\n"
            f"{format_for_architecture(governance)}\n"
            "Your analysis must include:\n"
            "1. **Coupling assessment** — Are modules/services tightly or loosely coupled? "
            "Use the import graph to identify high-coupling hotspots.\n"
            "2. **Service boundaries** — Are boundaries clearly defined? Is there evidence of "
            "a monolith, microservices, or mixed approach?\n"
            "3. **API surface** — Use the API endpoint scanner to catalogue all routes. "
            "Are they consistently structured? Versioned? Well-named?\n"
            "4. **Import depth** — How deeply nested are dependency chains? Are there circular "
            "imports? Which modules have the most dependents?\n"
            "5. **Separation of concerns** — Are infrastructure, domain logic, and presentation "
            "clearly separated? Are there clear abstraction layers?\n"
            "6. **Scalability signals** — Is the architecture amenable to horizontal scaling? "
            "Are there obvious bottlenecks (shared mutable state, sync-only I/O)?\n\n"
            "Use your tools to examine the import graph and API endpoints of key modules. "
            "Cite specific files in your findings.\n\n"
            "Conclude with a score (0-100) where 100 = excellent architectural coherence."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Enterprise Architecture Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Architecture Style\n\n"
            "[Identified architecture style: monolith, modular monolith, microservices, etc.]\n\n"
            "## Coupling Assessment\n\n"
            "| Module | Inbound Deps | Outbound Deps | Coupling Level | Notes |\n"
            "|--------|-------------|--------------|----------------|-------|\n"
            "| ... | X | Y | Low/Medium/High | ... |\n\n"
            "**Hotspot modules** (highest coupling):\n"
            "1. `path/to/module` — X imports, reason\n\n"
            "## Service Boundaries\n\n"
            "[Assessment of boundary clarity, layer separation, domain isolation]\n\n"
            "## API Surface\n\n"
            "| Endpoint Pattern | Count | Versioned? | Auth Required? | Notes |\n"
            "|-----------------|-------|-----------|----------------|-------|\n"
            "| GET /api/... | X | ✅/❌ | ✅/❌ | ... |\n\n"
            "## Import Depth Analysis\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| Max import depth | X |\n"
            "| Circular dependencies | X |\n"
            "| Most-imported module | ... |\n\n"
            "## Separation of Concerns\n\n"
            "| Layer | Properly Isolated? | Notes |\n"
            "|-------|-------------------|-------|\n"
            "| Routes/Controllers | ✅/❌ | ... |\n"
            "| Business Logic | ✅/❌ | ... |\n"
            "| Data Access | ✅/❌ | ... |\n"
            "| Configuration | ✅/❌ | ... |\n\n"
            "## Scalability Concerns\n\n"
            "[Assessment of scaling readiness, bottlenecks, shared state]\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=enterprise_architect,
        async_execution=True,
    )

    # ── Task 4: Security Analysis ──────────────────────────────────────────────
    security_task = Task(
        description=(
            f"Perform a security review of the codebase at '{repo_url}'.\n\n"
            f"## Repository Metadata\n{meta}\n\n"
            f"{format_for_security(governance)}\n"
            "Your analysis must include:\n"
            "1. **Secrets scan** — Use the secret scanner to find hardcoded credentials, API keys, "
            "tokens, or connection strings. Check .gitignore for proper .env exclusion.\n"
            "2. **Vulnerable dependencies** — Are any dependencies known to be vulnerable? "
            "Are there outdated packages with published CVEs?\n"
            "3. **Authentication patterns** — Is there auth middleware? Is it applied consistently? "
            "Is session/token handling sound?\n"
            "4. **Error handling** — Are errors handled gracefully? Are stack traces exposed in "
            "responses? Is sensitive information logged?\n"
            "5. **Input validation** — Is user input validated? Are there obvious injection risks "
            "(SQL, command, path traversal)?\n"
            "6. **Data handling** — Is sensitive data encrypted at rest/transit? Are there "
            "clear data classification patterns in the code?\n"
            "7. **Security configuration** — Are there security headers? CORS configured correctly? "
            "Rate limiting in place?\n\n"
            "Use your tools to scan for secrets and read authentication/middleware code. "
            "Cite specific files and line numbers for every finding.\n\n"
            "Conclude with a score (0-100) where 100 = no security concerns identified."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Security & Resilience Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Secrets Scan\n\n"
            "| # | Finding | Severity | File | Line | Description |\n"
            "|---|---------|----------|------|------|-------------|\n"
            "| 1 | ... | CRITICAL/HIGH/LOW | path/to/file | 42 | ... |\n\n"
            "**No secrets found** — if clean, state this explicitly.\n\n"
            "## .gitignore & Secret Hygiene\n\n"
            "| File/Pattern | In .gitignore? | Notes |\n"
            "|-------------|---------------|-------|\n"
            "| .env | ✅/❌ | ... |\n"
            "| *.pem / *.key | ✅/❌ | ... |\n\n"
            "## Dependency Vulnerabilities\n\n"
            "| Package | Version | CVE / Issue | Severity | Notes |\n"
            "|---------|---------|------------|----------|-------|\n"
            "| ... | ... | ... | CRITICAL/HIGH/MEDIUM | ... |\n\n"
            "## Authentication & Authorisation\n\n"
            "| Aspect | Status | Notes |\n"
            "|--------|--------|-------|\n"
            "| Auth middleware present | ✅/❌ | ... |\n"
            "| Applied to all routes | ✅/❌ | ... |\n"
            "| Token expiry configured | ✅/❌ | ... |\n"
            "| CORS policy | Restrictive/Permissive | ... |\n\n"
            "## Error Handling\n\n"
            "| Concern | Status | Evidence |\n"
            "|---------|--------|----------|\n"
            "| Stack traces exposed | ✅ Safe / ⚠️ Exposed | file:line |\n"
            "| Sensitive data in logs | ✅ Safe / ⚠️ Leaking | file:line |\n"
            "| Generic error responses | ✅/❌ | ... |\n\n"
            "## Input Validation\n\n"
            "[Assessment of validation at API boundaries, injection risks]\n\n"
            "## Findings Summary\n\n"
            "| # | Finding | Severity | File | Recommendation |\n"
            "|---|---------|----------|------|----------------|\n"
            "| 1 | ... | CRITICAL/HIGH/MEDIUM/LOW | path/file:line | ... |\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=security_analyst,
        async_execution=True,
    )

    # ── Task 5: DA Chair Synthesis ─────────────────────────────────────────────
    synthesis_task = Task(
        description=(
            f"Synthesise all specialist codebase reviews for '{repo_url}' and deliver a "
            f"structured findings report with prioritised improvement roadmap.\n\n"
            f"## Repository Metadata\n{meta}\n\n"
            f"{format_for_chair(governance)}\n"
            "You have received assessments from:\n"
            "1. **Standards Analyst** — Code structure, naming, dependency health, linting\n"
            "2. **DX Analyst** — README, docs, test coverage, onboarding complexity\n"
            "3. **Enterprise Architect** — Coupling, service boundaries, API surface, import depth\n"
            "4. **Security & Resilience Analyst** — Secrets, vulnerable deps, auth, error handling\n\n"
            "Your synthesis must:\n"
            "1. Summarise each specialist's score and top findings\n"
            "2. Identify cross-cutting themes (issues appearing in multiple reports)\n"
            "3. Prioritise all findings using the effort/impact matrix:\n"
            "   - **Quick Win** — High impact, low effort (fix in < 1 day)\n"
            "   - **Sprint** — Medium effort (1–5 days, fits in a sprint)\n"
            "   - **Epic** — High effort (requires planning, > 1 sprint)\n"
            "4. Assign severity to each finding: CRITICAL / HIGH / MEDIUM / LOW\n"
            "5. Produce an ordered improvement roadmap: do this first, then this, then this\n"
            "6. Give an overall codebase health score (weighted average of specialist scores)\n"
            "7. Provide an executive summary (3–5 sentences) suitable for a team lead\n\n"
            "Be specific. Reference file paths from the specialist reports. "
            "Every recommendation must map to evidence from at least one specialist."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Design Authority Ruling\n\n"
            "## Overall Health Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Overall Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Ruling** | APPROVED / CONDITIONAL / REJECTED |\n\n"
            "## Executive Summary\n\n"
            "[3-5 sentences for a team lead — what is the state of this codebase and what matters most]\n\n"
            "## Specialist Scores\n\n"
            "| Analyst | Score | Rating | Top Finding |\n"
            "|---------|-------|--------|-------------|\n"
            "| Standards | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Developer Experience | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Enterprise Architecture | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Security & Resilience | X/100 | GREEN/AMBER/RED | ... |\n\n"
            "**Weighting:** Standards 25% · DX 20% · Architecture 25% · Security 30%\n\n"
            "## Cross-Cutting Themes\n\n"
            "[Issues flagged by 2 or more specialists]\n\n"
            "| Theme | Flagged By | Summary |\n"
            "|-------|-----------|----------|\n"
            "| ... | Standards, Security | ... |\n\n"
            "## Prioritised Findings\n\n"
            "| # | Finding | Severity | Source | File(s) | Recommendation |\n"
            "|---|---------|----------|--------|---------|----------------|\n"
            "| 1 | ... | CRITICAL | Security | path/file | ... |\n"
            "| 2 | ... | HIGH | Standards | path/file | ... |\n"
            "| 3 | ... | MEDIUM | Architecture | path/file | ... |\n\n"
            "## Improvement Roadmap\n\n"
            "### Quick Wins (< 1 day each)\n\n"
            "| # | Action | Owner/Domain | Impact |\n"
            "|---|--------|-------------|--------|\n"
            "| 1 | ... | ... | ... |\n\n"
            "### Sprint Items (1-5 days each)\n\n"
            "| # | Action | Owner/Domain | Impact |\n"
            "|---|--------|-------------|--------|\n"
            "| 1 | ... | ... | ... |\n\n"
            "### Epics (> 1 sprint)\n\n"
            "| # | Action | Owner/Domain | Impact |\n"
            "|---|--------|-------------|--------|\n"
            "| 1 | ... | ... | ... |\n\n"
            "## Next Steps\n\n"
            "1. ...\n"
            "2. ...\n"
            "3. ...\n"
        ),
        agent=da_chair,
        context=[
            standards_task,
            dx_task,
            enterprise_task,
            security_task,
        ],
    )

    crew = Crew(
        agents=[
            da_chair,
            standards_analyst,
            dx_analyst,
            enterprise_architect,
            security_analyst,
        ],
        tasks=[
            standards_task,
            dx_task,
            enterprise_task,
            security_task,
            synthesis_task,
        ],
        process=Process.sequential,  # async tasks run in parallel; synthesis waits for all
        verbose=True,
        memory=False,
        planning=False,
        task_callback=task_callback,
    )

    return crew
