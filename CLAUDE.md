# Architecture Council — Scope Control

## Project Identity
AI-powered Software Architecture Design Authority using 5 LLMs across 4 cloud
providers for diverse, grounded architecture reviews.

## What This Project IS
- A multi-agent system that evaluates software architecture decisions (ADRs)
  AND reviews live codebases against organisational standards
- Uses 5 different LLMs (OpenAI, Anthropic, Perplexity) for diverse perspectives
- Produces scored reports with structured tables, findings, and improvement roadmaps
- CrewAI orchestration with FastAPI backend and Next.js frontend
- Supports configurable governance rules via YAML files
- RAG-powered conversational follow-up on analysed codebases

## What This Project IS NOT
- A full ITSM/service management tool
- A CI/CD pipeline tool
- A monitoring/observability platform
- A code formatter or linter (evaluates architecture, not syntax)

## Agent Lineup

| Agent               | Model              | Provider   | Location |
|---------------------|--------------------|------------|----------|
| Standards Analyst   | GPT-4.1            | OpenAI     | Cloud    |
| DX Analyst          | Sonar Pro          | Perplexity | Cloud    |
| Enterprise Architect| Claude Sonnet 4    | Anthropic  | Cloud    |
| Security Analyst    | Claude Haiku 4.5   | Anthropic  | Cloud    |
| DA Chair            | GPT-5.1            | OpenAI     | Cloud    |

## Outcomes (Every Change Must Link To One)
1. **Decision Quality** — Agents produce accurate, well-reasoned evaluations
2. **Multi-LLM Diversity** — Different perspectives from different models and providers
3. **Developer UX** — Clean, fast, intuitive submission and review experience
4. **Governance Trail** — Every ruling is traceable and auditable

## Architecture Rules
- Keep CrewAI as orchestration framework
- Each agent MUST use its assigned LLM provider (no mixing)
- Tools return structured data (JSON), agents reason over it
- Frontend streams deliberation via SSE
- All configuration via .env (no hardcoded keys or endpoints)
- Governance rules configurable via YAML (governance/defaults/)

## File Structure
```
Architect-Council/
├── backend/
│   ├── agents/           # 5 agent definitions (one per file)
│   ├── crews/            # Architecture + Codebase crew configs
│   ├── tools/            # Architecture evaluation tools (7 tools)
│   ├── indexer/          # Repo cloning, structure mapping, RAG chunking
│   ├── schemas/          # Pydantic models
│   ├── api/              # FastAPI routes (review, codebase, query)
│   └── main.py
├── frontend/
│   ├── app/              # Next.js app router (ADR + Codebase pages)
│   ├── components/       # React components (AgentPanel, TabbedOutput, etc.)
│   ├── hooks/            # SSE streaming hooks
│   ├── lib/              # API client, shared agent config
│   └── types/            # TypeScript definitions
├── governance/
│   └── defaults/         # YAML governance rules (tech-radar, coding-standards, etc.)
├── data/                 # Static config (tech radar, patterns, rules)
├── docker/               # Docker Compose + Dockerfiles
├── .env                  # API keys (gitignored)
├── .env.example          # Template for required env vars
├── CLAUDE.md             # This file
└── README.md
```
