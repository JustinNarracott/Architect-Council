# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers directly with details
3. Include steps to reproduce if possible
4. Allow reasonable time for a fix before disclosure

## Security Considerations

### API Keys
- Never commit API keys or secrets to the repository
- Use environment variables for all sensitive configuration
- The `.env` file is gitignored by default
- Ollama local model requires no API key

### Architecture Reviews
- Codebase reviews clone repos to temporary directories
- Cloned repos are cleaned up after analysis
- File reading tools are sandboxed to the clone directory (path traversal prevention)
- Local model (Ollama) keeps security analysis on-premises

### Dependencies
- Keep dependencies updated regularly
- Review security advisories for dependencies
- Use `uv sync` to ensure locked dependency versions
