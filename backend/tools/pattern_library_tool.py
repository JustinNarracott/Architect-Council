"""Pattern library tool for checking design patterns and anti-patterns."""

import json
from pathlib import Path
from typing import Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class PatternCheckInput(BaseModel):
    """Input schema for pattern checking."""

    proposal_description: str = Field(
        ..., description="Description of the proposed architecture or approach"
    )
    pattern_type: Optional[str] = Field(
        default=None,
        description="Optional filter: 'architecture' | 'integration' | 'data' | 'security'"
    )


class PatternCheckTool(BaseTool):
    """Searches for matching patterns and anti-patterns in the pattern library."""

    name: str = "Pattern Library Check"
    description: str = (
        "Searches the pattern library for relevant architecture patterns and anti-patterns. "
        "Uses keyword matching to find patterns related to the proposal. Returns matched "
        "patterns (with when_to_use/when_to_avoid guidance) and any anti-patterns to watch for. "
        "Use this to leverage organizational knowledge and avoid known pitfalls."
    )
    args_schema: Type[BaseModel] = PatternCheckInput

    def _run(self, proposal_description: str, pattern_type: Optional[str] = None) -> str:
        """Search for matching patterns and anti-patterns."""
        try:
            # Load pattern library
            data_path = Path(__file__).parent.parent.parent / "data" / "patterns.json"

            if not data_path.exists():
                return "Pattern library not found. Cannot evaluate patterns."

            with open(data_path, "r") as f:
                pattern_library = json.load(f)

            # Extract keywords from proposal (simple word tokenization)
            keywords = set(
                word.lower()
                for word in proposal_description.replace(",", " ").split()
                if len(word) > 3
            )

            matched_patterns = []
            matched_antipatterns = []

            # Search patterns
            for pattern in pattern_library.get("patterns", []):
                # Filter by type if specified
                if pattern_type and pattern.get("type") != pattern_type:
                    continue

                # Simple keyword matching
                pattern_text = (
                    f"{pattern['name']} {pattern['description']} "
                    f"{pattern.get('when_to_use', '')} {pattern.get('when_to_avoid', '')}"
                ).lower()

                # Count keyword matches
                matches = sum(1 for keyword in keywords if keyword in pattern_text)

                if matches > 0:
                    matched_patterns.append((matches, pattern))

            # Search anti-patterns
            for antipattern in pattern_library.get("antipatterns", []):
                # Filter by type if specified
                if pattern_type and antipattern.get("type") != pattern_type:
                    continue

                antipattern_text = (
                    f"{antipattern['name']} {antipattern['description']} "
                    f"{antipattern.get('why_bad', '')} {antipattern.get('alternative', '')}"
                ).lower()

                matches = sum(1 for keyword in keywords if keyword in antipattern_text)

                if matches > 0:
                    matched_antipatterns.append((matches, antipattern))

            # Sort by relevance (match count)
            matched_patterns.sort(reverse=True, key=lambda x: x[0])
            matched_antipatterns.sort(reverse=True, key=lambda x: x[0])

            # Format results
            result = "Pattern Library Analysis\n"
            result += "=" * 60 + "\n\n"

            if matched_patterns:
                result += "RELEVANT PATTERNS:\n"
                result += "-" * 40 + "\n"
                for _, pattern in matched_patterns[:5]:  # Top 5
                    result += f"\n{pattern['name']}\n"
                    result += f"Type: {pattern.get('type', 'general')}\n"
                    result += f"Description: {pattern['description']}\n"
                    if pattern.get("when_to_use"):
                        result += f"When to use: {pattern['when_to_use']}\n"
                    if pattern.get("when_to_avoid"):
                        result += f"When to avoid: {pattern['when_to_avoid']}\n"
            else:
                result += "No strongly matching patterns found.\n"

            if matched_antipatterns:
                result += "\n\nPOTENTIAL ANTI-PATTERNS TO AVOID:\n"
                result += "-" * 40 + "\n"
                for _, antipattern in matched_antipatterns[:3]:  # Top 3
                    result += f"\n⚠ {antipattern['name']}\n"
                    result += f"Type: {antipattern.get('type', 'general')}\n"
                    result += f"Description: {antipattern['description']}\n"
                    if antipattern.get("why_bad"):
                        result += f"Why bad: {antipattern['why_bad']}\n"
                    if antipattern.get("alternative"):
                        result += f"Alternative: {antipattern['alternative']}\n"
            else:
                result += "\n\nNo anti-patterns detected.\n"

            if not matched_patterns and not matched_antipatterns:
                result += "\nNo patterns or anti-patterns matched. "
                result += "Consider providing more specific architectural details.\n"

            return result

        except Exception as e:
            return f"Error checking pattern library: {str(e)}"
