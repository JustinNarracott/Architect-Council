"""Governance configuration loader."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GovernanceConfig:
    """Parsed governance configuration from YAML files."""
    tech_radar: dict[str, Any] = field(default_factory=dict)
    coding_standards: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not any([self.tech_radar, self.coding_standards,
                        self.architecture, self.security])


def load_governance(config_dir: str | Path | None = None) -> GovernanceConfig:
    """
    Load governance YAML files from the specified directory.

    Falls back to governance/defaults/ at repo root.
    Returns an empty GovernanceConfig if no files found (graceful degradation).
    """
    if config_dir is None:
        # Default: look for governance/defaults/ relative to repo root
        # In Docker container, this will be at /app/governance/defaults/
        # or mounted from host
        candidates = [
            Path("/app/governance/defaults"),
            Path(__file__).parent.parent.parent / "governance" / "defaults",
        ]
        config_dir = next((p for p in candidates if p.exists()), None)
        if config_dir is None:
            return GovernanceConfig()

    config_dir = Path(config_dir)
    config = GovernanceConfig()

    file_map = {
        "tech-radar.yaml": "tech_radar",
        "coding-standards.yaml": "coding_standards",
        "architecture.yaml": "architecture",
        "security.yaml": "security",
    }

    for filename, attr in file_map.items():
        filepath = config_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                data = yaml.safe_load(f)
                if data:
                    setattr(config, attr, data)

    return config


__all__ = ["GovernanceConfig", "load_governance"]
