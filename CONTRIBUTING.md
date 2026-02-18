# Contributing to The Architecture Council

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building something together.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment (see README.md)
4. Create a feature branch from `main`

## Development Setup

### Backend

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the server
uv run architecture-council
```

### Frontend

```bash
cd frontend

# Install dependencies
bun install

# Run development server
bun dev
```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-agent` - New features
- `fix/streaming-timeout` - Bug fixes
- `docs/update-readme` - Documentation
- `refactor/api-routes` - Refactoring

### Code Style

#### Python (Backend)
- Follow PEP 8 guidelines
- Use type hints for function signatures
- Use Ruff for linting (`uv run ruff check backend/`)
- Keep functions focused and well-documented

#### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow existing patterns in the codebase
- Run `bun lint` before committing
- Use functional components with hooks

### Commit Messages

Write clear, concise commit messages:
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be under 72 characters
- Reference issues when relevant

Examples:
```
Add sentiment analysis tool for news data

Fix SSE connection timeout in streaming endpoint

Refactor agent definitions for better modularity
```

## Pull Request Process

1. **Update documentation** if your changes affect usage
2. **Add tests** for new functionality
3. **Run all tests** locally before submitting
4. **Fill out the PR template** completely
5. **Request review** from maintainers

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] Documentation updated if needed
- [ ] No sensitive data (API keys, secrets) committed

## Adding New Agents

When adding a new agent to the council:

1. Create agent definition in `backend/agents/`
2. Add agent to the crew in `backend/crews/architecture_crew.py`
3. Update `backend/api/routes.py` with agent info
4. Add agent type to frontend `types/index.ts`
5. Update agent panel styling in frontend
6. Document the agent's role in README.md

## Adding New Tools

When adding market data or analysis tools:

1. Create tool in `backend/tools/`
2. Add proper error handling and rate limiting
3. Write unit tests for the tool
4. Document expected inputs/outputs
5. Export from `backend/tools/__init__.py`

## Testing

### Backend Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend

# Run specific test file
uv run pytest tests/test_tools.py
```

### Frontend Tests

```bash
cd frontend

# Run linting
bun lint

# Type check
bun run tsc --noEmit
```

## Questions?

Feel free to open an issue for questions or discussion about potential contributions.
