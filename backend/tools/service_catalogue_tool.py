"""Service catalogue tool for checking existing services."""

import json
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ServiceCatalogueInput(BaseModel):
    """Input schema for service catalogue search."""

    query: str = Field(
        ...,
        description="Service name or capability keyword to search for (e.g., 'customer', 'auth', 'payment')"
    )


class ServiceCatalogueTool(BaseTool):
    """Searches the service catalogue for existing services and capabilities."""

    name: str = "Service Catalogue"
    description: str = (
        "Searches the organizational service catalogue to find existing services. "
        "Use this to detect duplication of capabilities, identify potential integration "
        "points, or check for conflicts with existing services. Returns matching services "
        "with owner team, technology stack, API endpoints, data classification, and status."
    )
    args_schema: Type[BaseModel] = ServiceCatalogueInput

    def _run(self, query: str) -> str:
        """Search service catalogue for matching services."""
        try:
            # Load service catalogue
            data_path = Path(__file__).parent.parent.parent / "data" / "services.json"

            if not data_path.exists():
                return "Service catalogue not found. Cannot check for existing services."

            with open(data_path, "r") as f:
                services = json.load(f)

            # Search for matching services (case-insensitive keyword matching)
            query_lower = query.lower()
            matches = []

            for service in services:
                # Search in name, capabilities, and description
                searchable = f"{service['name']} {service.get('description', '')} {' '.join(service.get('capabilities', []))}"

                if query_lower in searchable.lower():
                    matches.append(service)

            if not matches:
                result = f"Service Catalogue Search: '{query}'\n"
                result += "=" * 60 + "\n\n"
                result += "No existing services found matching this query.\n\n"
                result += "This may indicate:\n"
                result += "  ✓ New capability - no duplication risk\n"
                result += "  ⚠ Gap in service catalogue - verify manually\n"
                return result

            # Format results
            result = f"Service Catalogue Search: '{query}'\n"
            result += "=" * 60 + "\n"
            result += f"Found {len(matches)} matching service(s)\n\n"

            for service in matches:
                result += f"Service: {service['name']}\n"
                result += "-" * 40 + "\n"
                result += f"Status: {service['status'].upper()}\n"
                result += f"Owner Team: {service['owner_team']}\n"

                if service.get('description'):
                    result += f"Description: {service['description']}\n"

                if service.get('capabilities'):
                    result += "Capabilities:\n"
                    for cap in service['capabilities']:
                        result += f"  - {cap}\n"

                if service.get('technology_stack'):
                    result += f"Tech Stack: {', '.join(service['technology_stack'])}\n"

                if service.get('api_endpoints'):
                    result += "API Endpoints:\n"
                    for endpoint in service['api_endpoints']:
                        result += f"  - {endpoint}\n"

                if service.get('data_classification'):
                    result += f"Data Classification: {service['data_classification']}\n"

                if service.get('repository'):
                    result += f"Repository: {service['repository']}\n"

                result += "\n"

            # Analysis
            result += "ANALYSIS\n"
            result += "-" * 40 + "\n"

            active_matches = [s for s in matches if s['status'] == 'active']
            deprecated_matches = [s for s in matches if s['status'] == 'deprecated']
            planned_matches = [s for s in matches if s['status'] == 'planned']

            if active_matches:
                result += f"⚠ {len(active_matches)} active service(s) with similar capabilities\n"
                result += "  → Check for potential duplication\n"
                result += "  → Consider extending existing service vs creating new\n"

            if deprecated_matches:
                result += f"ℹ {len(deprecated_matches)} deprecated service(s) found\n"
                result += "  → If replacing deprecated service, plan migration strategy\n"

            if planned_matches:
                result += f"ℹ {len(planned_matches)} planned service(s) found\n"
                result += "  → Coordinate to avoid duplication of effort\n"

            if not active_matches:
                result += "✓ No active services with overlapping capabilities\n"

            return result

        except Exception as e:
            return f"Error searching service catalogue: {str(e)}"
