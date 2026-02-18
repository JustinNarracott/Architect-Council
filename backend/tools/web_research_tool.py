"""Web research tool using Perplexity API for real-time technology intelligence."""

import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class WebResearchInput(BaseModel):
    """Input schema for web research."""

    technology_name: str = Field(..., description="Technology name to research")
    research_type: str = Field(
        ...,
        description="Type of research: 'community_health' | 'documentation' | 'alternatives' | 'incidents'"
    )


class WebResearchTool(BaseTool):
    """Performs real-time web research using Perplexity API."""

    name: str = "Web Research"
    description: str = (
        "Performs real-time web research about a technology using Perplexity AI. "
        "Research types: "
        "'community_health' - GitHub activity, Stack Overflow, community engagement; "
        "'documentation' - quality of docs, tutorials, examples; "
        "'alternatives' - competing technologies and comparisons; "
        "'incidents' - recent outages, security issues, or controversies. "
        "Use this to get current intelligence beyond static data sources."
    )
    args_schema: Type[BaseModel] = WebResearchInput

    def _run(self, technology_name: str, research_type: str) -> str:
        """Perform web research for the given technology."""
        try:
            # Check if Perplexity API key is available
            perplexity_key = os.getenv("PERPLEXITY_API_KEY")

            if not perplexity_key:
                return (
                    f"Web Research: {technology_name} ({research_type})\n"
                    + "=" * 60 + "\n\n"
                    + "⚠ Perplexity API key not configured\n\n"
                    + "To enable real-time web research:\n"
                    + "1. Set PERPLEXITY_API_KEY in .env file\n"
                    + "2. Perplexity API provides current web intelligence\n"
                    + "3. This is the DX Analyst's primary research tool\n\n"
                    + "For MVP: Perform manual research using:\n"
                    + "  - GitHub: github.com/{technology_name}\n"
                    + f"  - Stack Overflow: stackoverflow.com/search?q={technology_name}\n"
                    + f"  - Google Trends: trends.google.com\n"
                )

            # Build research query based on type
            queries = {
                "community_health": (
                    f"What is the current state of the {technology_name} community? "
                    f"Check GitHub activity (stars, recent commits, open issues), "
                    f"Stack Overflow questions trend, active maintainers, and community engagement. "
                    f"Is it actively maintained?"
                ),
                "documentation": (
                    f"Evaluate the documentation quality for {technology_name}. "
                    f"Are there comprehensive guides, tutorials, and examples? "
                    f"Is the documentation up-to-date? What do developers say about learning curve?"
                ),
                "alternatives": (
                    f"What are the main alternatives to {technology_name}? "
                    f"Compare features, adoption, and use cases. "
                    f"Which alternative technologies should be considered?"
                ),
                "incidents": (
                    f"Have there been any recent security vulnerabilities, outages, "
                    f"or major issues with {technology_name} in the past 12 months? "
                    f"Any breaking changes or deprecations announced?"
                )
            }

            query = queries.get(research_type)
            if not query:
                return f"Invalid research type: {research_type}"

            # For MVP without actual API call, return template
            # In production, this would call Perplexity API
            result = f"Web Research: {technology_name}\n"
            result += f"Research Type: {research_type}\n"
            result += "=" * 60 + "\n\n"

            result += "[MVP MODE - Perplexity API Integration Required]\n\n"

            result += "Query that would be sent:\n"
            result += f'"{query}"\n\n'

            result += "To implement:\n"
            result += "```python\n"
            result += "import requests\n\n"
            result += "response = requests.post(\n"
            result += '    "https://api.perplexity.ai/chat/completions",\n'
            result += "    headers={\n"
            result += '        "Authorization": f"Bearer {perplexity_key}",\n'
            result += '        "Content-Type": "application/json"\n'
            result += "    },\n"
            result += "    json={\n"
            result += '        "model": "sonar-pro",\n'
            result += '        "messages": [{"role": "user", "content": query}],\n'
            result += '        "temperature": 0.2,\n'
            result += '        "return_citations": True\n'
            result += "    }\n"
            result += ")\n"
            result += "```\n\n"

            result += "Expected output format:\n"
            result += "- Summary of findings\n"
            result += "- Key metrics (stars, downloads, activity)\n"
            result += "- Recent developments\n"
            result += "- Community sentiment\n"
            result += "- Citations/sources\n"

            return result

        except Exception as e:
            return f"Error performing web research for {technology_name}: {str(e)}"
