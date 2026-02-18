# The Architecture Council

An AI-powered Software Architecture Design Authority where specialized AI agents evaluate architecture decisions against organizational standards, producing scored Architecture Decision Records (ADRs) with reasoned rulings.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

The Architecture Council creates a visual panel of AI agents, each powered by a different LLM and with distinct expertise, that analyze software architecture decisions and produce consensus-based rulings. Agents evaluate proposals against standards, community health, strategic alignment, and security implications, synthesizing diverse perspectives into actionable architecture guidance.

Like having a design authority board available 24/7 in under 60 seconds.

### The Council Panel

| Agent | LLM Provider | Role | Focus |
|-------|--------------|------|-------|
| **Standards Analyst** | OpenAI GPT-4o | Standards & Patterns Evaluator | Tech radar, design patterns, anti-patterns, API standards |
| **DX Analyst** | Perplexity Sonar | Developer Experience Analyst | Learning curve, community health, documentation, hiring pool |
| **Enterprise Architect** | Google Gemini 2.0 Flash | Integration & Strategy Analyst | Service integration, dependency analysis, strategic alignment |
| **Security & Resilience Analyst** | Anthropic Claude Sonnet 4 | Security & Operational Risk Analyst | Threat surface, compliance, failure modes, blast radius |
| **DA Chair** | Anthropic Claude Opus | Design Authority Chair | Evidence synthesis, conflict resolution, final ruling |

## Features

- **Multi-LLM Diversity**: 5 different LLMs provide diverse perspectives on architecture decisions
- **Real-time Streaming**: Watch agents deliberate via Server-Sent Events
- **Parallel Evaluation**: Specialist agents execute in parallel for 3x faster reviews
- **Structured Rulings**: Clear APPROVED/CONDITIONAL/REJECTED/DEFERRED outcomes with conditions
- **Governance Trail**: Every ruling is traceable with full agent reasoning
- **Modern UI**: Dev/DevOps aesthetic with circuit patterns and code-review styling

## Tech Stack

### Backend
- **[CrewAI](https://www.crewai.com/)** - Multi-agent orchestration
- **[FastAPI](https://fastapi.tiangolo.com/)** - REST API & SSE streaming
- **Multiple LLMs** - OpenAI, Anthropic, Google, Perplexity
- **Python 3.11+**

### Frontend
- **[Next.js 14](https://nextjs.org/)** - React framework
- **[Tailwind CSS](https://tailwindcss.com/)** - Styling (dev/devops theme)
- **[Framer Motion](https://www.framer.com/motion/)** - Animations
- **TypeScript**

### Architecture Tools
- Tech Radar compliance checker
- Design pattern library matcher
- Service catalogue query
- Compliance rules evaluator
- Real-time web research (community health, adoption rates)
- Dependency analysis

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Bun](https://bun.sh/) (or npm/yarn)
- **4 API keys** (see Configuration below)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JustinNarracott/architect-council.git
   cd architect-council
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add ALL 4 API keys (see Configuration section)
   ```

3. **Install backend dependencies**
   ```bash
   uv sync
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   bun install
   ```

### Running the Application

1. **Start the backend** (from project root)
   ```bash
   uv run architecture-council
   ```
   The API will be available at `http://localhost:8000`

2. **Start the frontend** (in another terminal)
   ```bash
   cd frontend
   bun dev
   ```
   The UI will be available at `http://localhost:3000`

3. **Open your browser** and navigate to `http://localhost:3000`

## Configuration

### Backend Environment Variables

**IMPORTANT**: All 4 API keys are required for the council to function.

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key (for Standards Analyst using GPT-4o) | **Yes** |
| `ANTHROPIC_API_KEY` | Anthropic API key (for Security Analyst + DA Chair using Claude) | **Yes** |
| `GOOGLE_API_KEY` | Google API key (for Enterprise Architect using Gemini 2.0) | **Yes** |
| `PERPLEXITY_API_KEY` | Perplexity API key (for DX Analyst using Sonar) | **Yes** |
| `HOST` | Backend host | No (default: `0.0.0.0`) |
| `PORT` | Backend port | No (default: `8000`) |
| `RELOAD` | Enable hot reload | No (default: `true`) |

**Example `.env`:**
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
PERPLEXITY_API_KEY=pplx-...

HOST=0.0.0.0
PORT=8000
RELOAD=true
```

### Frontend Environment Variables

Create `frontend/.env.local` for frontend configuration:

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | No (default: `http://localhost:8000`) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API information |
| `GET` | `/health` | Health check |
| `GET` | `/api/panel` | List all council panel members |
| `POST` | `/api/review` | Start architecture review for an ADR |
| `GET` | `/api/stream/{id}` | SSE stream for review |
| `GET` | `/api/rulings` | Past architecture rulings |
| `GET` | `/api/review/{id}` | Get review result |
| `GET` | `/api/tech-radar` | Get technology radar data |

### Example: Start Architecture Review

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

### Example Response:

```json
{
  "analysis_id": "a3f5c8e7-...",
  "stream_url": "/api/stream/a3f5c8e7-...",
  "status": "started"
}
```

## Project Structure

```
architecture-council/
├── backend/
│   ├── agents/           # 5 agent definitions (one per file, one per LLM)
│   ├── crews/            # Architecture crew configuration
│   ├── tools/            # Architecture evaluation tools
│   ├── schemas/          # Pydantic models for ADR domain
│   ├── api/              # FastAPI routes
│   └── main.py           # Application entry point
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities & API client
│   └── types/            # TypeScript definitions
├── data/                 # Static config (tech radar, patterns, rules)
│   ├── tech_radar.json
│   ├── patterns.json
│   ├── services.json
│   ├── compliance_rules.json
│   └── test_adrs.json
├── .env.example          # Environment template
├── pyproject.toml        # Python dependencies
├── CONTRIBUTING.md       # Contribution guidelines
└── README.md
```

## Development

### Backend Development

```bash
# Run with hot reload
uv run architecture-council

# Run tests
uv run pytest

# Type checking (if configured)
uv run mypy backend
```

### Frontend Development

```bash
cd frontend

# Development server
bun dev

# Lint
bun lint

# Build
bun build
```

## How It Works

1. **Input**: User submits an ADR proposal (title, technology, reason, affected services, data classification)
2. **Parallel Evaluation**: 4 specialist agents evaluate in parallel:
   - Standards Analyst checks tech radar, patterns, API standards
   - DX Analyst researches community health, learning curve, adoption
   - Enterprise Architect assesses strategic alignment, integration impact
   - Security Analyst evaluates threat surface, compliance, failure modes
3. **Synthesis**: DA Chair reviews all assessments, resolves conflicts, delivers ruling
4. **Output**: Structured ruling (APPROVED/CONDITIONAL/REJECTED/DEFERRED) with conditions and rationale

**Typical execution time**: 30-60 seconds (with parallel execution)

## Test Cases

The `data/test_adrs.json` file contains 5 realistic test cases covering:
- SHOULD APPROVE: Standard caching pattern (Redis)
- APPROVE WITH CONDITIONS: GraphQL gateway (trial tech, multi-service)
- SHOULD REJECT: MongoDB replacement for PostgreSQL (anti-pattern)
- SHOULD DEFER: Dagger CI/CD migration (too new, unproven)
- SHOULD DEFER: Effect-TS for billing (niche tech, team capability question)

## Error Handling

The system implements graceful degradation:
- **Configuration errors**: Clear messaging if API keys are missing
- **Rate limiting**: Specific guidance for each provider
- **Authentication errors**: Prompt to check API key validity
- **Network errors**: Retry suggestions
- **Timeouts**: Individual agent timeouts won't block the entire review
- **Partial failures**: DA Chair synthesizes whatever assessments were received

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CrewAI](https://www.crewai.com/) for the multi-agent orchestration framework
- [OpenAI](https://openai.com/), [Anthropic](https://www.anthropic.com/), [Google](https://ai.google.dev/), [Perplexity](https://www.perplexity.ai/) for LLM APIs
- Inspired by real design authority boards and architecture review processes
