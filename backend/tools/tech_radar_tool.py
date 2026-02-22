"""Tech radar tool for checking technology approval status."""

import json
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class TechRadarInput(BaseModel):
    """Input schema for tech radar lookup."""

    technology: str = Field(..., description="Technology name to look up (e.g., React, PostgreSQL, Docker)")


class TechRadarTool(BaseTool):
    """Looks up technology approval status in the tech radar."""

    name: str = "Tech Radar Lookup"
    description: str = (
        "Checks whether a technology is approved for use and its adoption status. "
        "Returns category (adopt/trial/assess/hold), description, approval date, "
        "conditions, and alternatives. Use this to verify if a proposed technology "
        "aligns with organizational standards."
    )
    args_schema: Type[BaseModel] = TechRadarInput

    def _run(self, technology: str) -> str:
        """Look up technology in the tech radar."""
        try:
            # Load tech radar data
            data_path = Path(__file__).parent.parent.parent / "data" / "tech_radar.json"

            if not data_path.exists():
                return f"Tech radar data not found. Cannot evaluate {technology}."

            with open(data_path, "r") as f:
                tech_radar = json.load(f)

            # Search for technology (case-insensitive)
            tech_lower = technology.lower()

            for category, items in tech_radar.items():
                for item in items:
                    if item["name"].lower() == tech_lower:
                        result = f"Tech Radar Entry: {item['name']}\n"
                        result += "=" * 60 + "\n"
                        result += f"Category: {category.upper()}\n"
                        result += f"Description: {item['description']}\n"
                        result += f"Approved Since: {item.get('approved_since', 'N/A')}\n"

                        if item.get("conditions"):
                            result += "\nConditions:\n"
                            for condition in item["conditions"]:
                                result += f"  - {condition}\n"

                        if item.get("alternatives"):
                            result += "\nAlternatives:\n"
                            for alt in item["alternatives"]:
                                result += f"  - {alt}\n"

                        # Add recommendation based on category
                        result += "\nRecommendation:\n"
                        if category == "adopt":
                            result += "  ✓ APPROVED for production use\n"
                        elif category == "trial":
                            result += "  ⚠ TRIAL phase - suitable for non-critical projects\n"
                        elif category == "assess":
                            result += "  ⚠ ASSESS only - experimental/proof-of-concept use\n"
                        elif category == "hold":
                            result += "  ✗ HOLD - not recommended for new projects\n"

                        return result

            # Technology not found
            return (
                f"Tech Radar Entry: {technology}\n"
                + "=" * 60 + "\n"
                + "Status: UNLISTED\n\n"
                + "This technology is not in the approved tech radar.\n"
                + "A Design Authority review is required before adoption.\n\n"
                + "Next steps:\n"
                + "  1. Submit ADR with technology justification\n"
                + "  2. Include comparison with approved alternatives\n"
                + "  3. Document team capability and support plan\n"
            )

        except Exception as e:
            return f"Error checking tech radar for {technology}: {str(e)}"
