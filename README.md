# The Architecture Council

An AI-powered Software Architecture Design Authority where specialised AI agents evaluate architecture decisions and codebases, producing scored reviews with reasoned rulings.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![CI](https://github.com/JustinNarracott/Architect-Council/actions/workflows/ci.yml/badge.svg)

## Overview

The Architecture Council creates a visual panel of AI agents — each powered by a different LLM — that analyse software architecture decisions and codebases, producing consensus-based rulings. Agents evaluate proposals against standards, community health, strategic alignment, and security implications, synthesising diverse perspectives into actionable guidance.

Like having a design authority board available 24/7 in under 60 seconds.

## Two Modes

### ADR Review
Submit an Architecture Decision Record proposal. Four specialist agents evaluate in parallel, the DA Chair synthesises, and you get a structured APPROVED / CONDITIONAL / REJECTED / DEFERRED ruling with scored findings.

### Codebase Review
Point the council at any public GitHub repository. The system clones it, indexes it, and runs the full panel against the actual code — scanning for secrets, analysing imports, reviewing standards compliance, and assessing DX. Results are exported as a full markdown report.

---

## The Council Panel

| Agent | LLM | Role | Notes |
|-------|-----|------|-------|
| **Standards Analyst** | OpenAI GPT-4.1 | Code structure, naming, dependency health, linting | Uses FileReader + PatternCheck tools |
| **DX Analyst** | Perplexity Sonar Pro | README, docs, test coverage, onboarding friction | No tools — Perplexity has built-in web search; repo metadata injected into task |
| **Enterprise Architect** | Anthropic Claude Sonnet 4 | Coupling, service boundaries, API surface, import depth | Uses FileReader, ImportGraph, APIScanner tools |
| **Security & Resilience Analyst** | Perplexity Sonar Pro | Secrets, vulnerable deps, auth, error handling | Tools pre-run in Python; results + live CVE knowledge via Perplexity |
| **DA Chair** | OpenAI GPT-4.1 | Evidence synthesis, conflict resolution, final ruling | Weighted scoring across all specialist reports |

### Why different LLMs?

Deliberate diversity — each LLM has different strengths:
- **GPT-4.1**: Strong instruction-following, reliable structured output
- **Perplexity Sonar Pro**: Live web search for real-time CVE lookups and community health data
- **Claude Sonnet 4**: Deep reasoning for architectural and integration analysis

### LLM Tool Compatibility Note

Not all LLMs support tool calling in CrewAI's ReAct loop. Perplexity Sonar Pro rejects OpenAI-style function calling entirely. For agents using Perplexity, tools are pre-run in Python before the crew starts and results are injected directly into the task description — giving the agent full evidence without needing to call tools itself. This is intentional and documented in the agent source files.

---

## Features

- **Multi-LLM Council**: 3 different LLM providers for genuine perspective diversity
- **Real-time Streaming**: Watch agents deliberate via Server-Sent Events
- **Parallel Evaluation**: Specialist agents execute in parallel (sequential only for DA Chair synthesis)
- **Codebase Review**: Clone any GitHub repo and run the full council against actual code
- **Secret Scanning**: Pre-run secret scanner with file-level evidence injected into security analysis
- **Live CVE Lookup**: Perplexity brings current vulnerability data to dependency assessments
- **Governance Config**: Per-instance governance rules loaded at runtime
- **Export**: Full markdown report export for every review
- **Ask Questions**: Post-review Q&A against completed analysis
- **Docker Support**: Full docker-compose setup for production deployment

---

## Tech Stack

### Backend
- **[CrewAI](https://www.crewai.com/)** — Multi-agent orchestration
- **[FastAPI](https://fastapi.tiangolo.com/)** — REST API & SSE streaming
- **[LiteLLM](https://litellm.ai/)** — Unified LLM provider interface
- **Python 3.11+** with [uv](https://github.com/astral-sh/uv)

### Frontend
- **[Next.js 14](https://nextjs.org/)** — React framework with App Router
- **[Tailwind CSS](https://tailwindcss.com/)** — Dev/DevOps aesthetic
- **[Framer Motion](https://www.framer.com/motion/)** — Agent panel animations
- **TypeScript**

### Tools (Codebase Review)
- `FileReaderTool` — reads source files from the cloned repo
- `SecretScannerTool` — scans for hardcoded credentials and key files
- `ImportGraphTool` — analyses Python/JS import graphs and coupling
- `APIEndpointScannerTool` — catalogues API routes and surface
- `StructureAnalyserTool` — directory structure and language breakdown
- `TestCoverageTool` — test file ratio and framework detection
- `DependencyCheckTool` — dependency health and vulnerability signals
- `ComplianceCheckTool` — governance rule evaluation

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Bun](https://bun.sh/) (or npm)
- API keys for OpenAI, Anthropic, and Perplexity

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustinNarracott/Architect-Council.git
   cd Architect-Council
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Fill in your API keys
   ```

3. **Install backend dependencies**
   ```bash
   uv sync
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend && bun install
   ```

5. **Start backend** (from project root)
   ```bash
   uv run architecture-council
   # API available at http://localhost:8000
   ```

6. **Start frontend** (separate terminal)
   ```bash
   cd frontend && bun dev
   # UI available at http://localhost:3000
   ```

### Docker (Recommended for Production)

```bash
cd docker
docker compose up --build -d
# Backend: http://localhost:8011
# Frontend: http://localhost:3011
```

---

## Configuration

### Required Environment Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Standards Analyst, DA Chair (GPT-4.1) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Enterprise Architect (Claude Sonnet 4) |
| `PERPLEXITY_API_KEY` | Perplexity API key | DX Analyst, Security Analyst (Sonar Pro) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Backend host |
| `PORT` | `8000` | Backend port |
| `RELOAD` | `false` | Hot reload (dev only) |

> **Note:** Google/Gemini is no longer used. The Enterprise Architect was migrated to Claude Sonnet 4 for more reliable tool calling in CrewAI's ReAct loop.

---

## API Reference

### ADR Review

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/panel` | List council members and their LLMs |
| `POST` | `/api/review` | Start ADR review |
| `GET` | `/api/stream/{id}` | SSE stream for review progress |
| `GET` | `/api/review/{id}` | Get completed review |
| `GET` | `/api/rulings` | List past rulings |

### Codebase Review

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/codebase/panel` | List codebase council members |
| `POST` | `/api/codebase/analyse` | Start codebase review (GitHub URL or local path) |
| `GET` | `/api/codebase/stream/{id}` | SSE stream for codebase review |
| `GET` | `/api/codebase/review/{id}` | Get completed codebase review |

### Example: Start Codebase Review

```bash
curl -X POST http://localhost:8000/api/codebase/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-org/your-repo.git"
  }'
```

### Example: Start ADR Review

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add Redis caching layer to Customer API",
    "technology": "Redis 7.x (AWS ElastiCache)",
    "reason": "Reduce database load and improve p95 latency from 800ms to <200ms",
    "affected_services": ["customer-api", "order-service"],
    "data_classification": "OFFICIAL",
    "proposer": "Platform Team"
  }'
```

---

## Project Structure

```
Architect-Council/
├── backend/
│   ├── agents/           # Agent definitions — one file per agent, one LLM per agent
│   │   ├── standards_analyst.py
│   │   ├── dx_analyst.py
│   │   ├── enterprise_architect.py
│   │   ├── security_analyst.py
│   │   └── da_chair.py
│   ├── crews/
│   │   ├── architecture_crew.py   # ADR review crew
│   │   └── codebase_crew.py       # Codebase review crew (with pre-run tool injection)
│   ├── tools/            # 8 evaluation tools for codebase review
│   ├── schemas/          # Pydantic models
│   ├── api/
│   │   ├── routes.py             # ADR review endpoints
│   │   ├── codebase_routes.py    # Codebase review endpoints
│   │   ├── governance_routes.py  # Governance config endpoints
│   │   └── query_routes.py       # Post-review Q&A endpoints
│   ├── indexer/          # Repo cloning and indexing pipeline
│   ├── governance/       # Governance rule loading and formatting
│   └── main.py
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # ADR Review
│   │   ├── codebase/page.tsx     # Codebase Review
│   │   └── governance/page.tsx   # Governance Config
│   ├── components/
│   └── lib/
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── governance/
│   └── defaults/         # Default governance rules (YAML)
├── data/                 # Static config (tech radar, patterns, compliance rules)
├── .env.example
├── pyproject.toml
└── CLAUDE.md             # Scope control for AI-assisted development
```

---

## How It Works

### ADR Review Flow
1. User submits an ADR (title, technology, reason, affected services, data classification)
2. Four specialist agents evaluate in parallel (~30–60 seconds)
3. DA Chair synthesises all assessments into a weighted ruling
4. Result streamed live via SSE; full report available for export

### Codebase Review Flow
1. User submits a GitHub URL (or local path)
2. Indexer clones the repo and builds metadata (file tree, language breakdown, dependencies, key files)
3. Security tools (`SecretScannerTool`, `FileReaderTool`) are **pre-run in Python** and results injected into the security task description — this is required because Perplexity doesn't support function calling
4. Four specialist agents evaluate in parallel against the indexed repo
5. DA Chair synthesises with weighted scoring and produces a prioritised improvement roadmap

---

## Governance

The council respects a governance configuration that can be set per-instance via the Governance Config UI or API. Governance rules influence agent scoring thresholds, mandatory findings, and compliance checks. Default rules are in `governance/defaults/`.

---

## CI / Quality Gates

Every push runs:
- **Ruff** lint check (`uv run ruff check backend/`)
- **mypy** type check (`uv run mypy backend/`)
- **pytest** test suite
- Across Python 3.11, 3.12, and 3.13

Frontend CI runs `bun lint` and `bun build` on every push.

---

## Contributing

Contributions welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit with clear messages
4. Ensure CI passes before opening a PR
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- [CrewAI](https://www.crewai.com/) for multi-agent orchestration
- [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Perplexity](https://www.perplexity.ai/) for LLM APIs
- Inspired by real design authority boards and architecture review processes
