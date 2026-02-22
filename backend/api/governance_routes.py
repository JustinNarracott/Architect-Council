"""Governance config API routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import yaml

from backend.governance import load_governance

router = APIRouter(prefix="/governance", tags=["governance"])

# Config directory — in Docker container this is the mounted volume;
# when running locally, fall back to repo-relative path.
_DOCKER_CONFIG_DIR = Path("/app/governance/defaults")
_LOCAL_CONFIG_DIR = Path(__file__).parent.parent.parent / "governance" / "defaults"

CONFIG_DIR: Path = (
    _DOCKER_CONFIG_DIR if _DOCKER_CONFIG_DIR.exists() else _LOCAL_CONFIG_DIR
)


class GovernanceFileContent(BaseModel):
    """Single governance file content."""
    filename: str
    content: dict
    raw_yaml: str


class GovernanceOverview(BaseModel):
    """Full governance configuration overview."""
    files: list[GovernanceFileContent]
    is_configured: bool


@router.get("/config", response_model=GovernanceOverview)
async def get_governance_config() -> GovernanceOverview:
    """Get the current governance configuration."""
    file_map = {
        "tech-radar.yaml": "Technology Radar",
        "coding-standards.yaml": "Coding Standards",
        "architecture.yaml": "Architecture Standards",
        "security.yaml": "Security Policies",
    }

    files = []
    for filename in file_map:
        filepath = CONFIG_DIR / filename
        if filepath.exists():
            raw = filepath.read_text()
            data = yaml.safe_load(raw) or {}
            files.append(GovernanceFileContent(
                filename=filename,
                content=data,
                raw_yaml=raw,
            ))
        else:
            files.append(GovernanceFileContent(
                filename=filename,
                content={},
                raw_yaml="",
            ))

    config = load_governance()
    return GovernanceOverview(files=files, is_configured=not config.is_empty)


@router.put("/config/{filename}")
async def update_governance_file(filename: str, body: dict) -> dict:
    """
    Update a governance config file.

    Accepts the raw YAML content as a string in body.raw_yaml,
    validates it parses as valid YAML, then writes to disk.
    """
    valid_files = {"tech-radar.yaml", "coding-standards.yaml", "architecture.yaml", "security.yaml"}
    if filename not in valid_files:
        raise HTTPException(status_code=400, detail=f"Invalid config file: {filename}")

    raw_yaml = body.get("raw_yaml", "")
    if not raw_yaml.strip():
        raise HTTPException(status_code=400, detail="YAML content cannot be empty")

    # Validate YAML
    try:
        parsed = yaml.safe_load(raw_yaml)
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=400, detail="YAML must be a dictionary at root level")
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    # Write to disk
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CONFIG_DIR / filename
    filepath.write_text(raw_yaml)

    return {"status": "updated", "filename": filename}
