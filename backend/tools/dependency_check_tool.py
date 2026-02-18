"""Dependency check tool for evaluating package health and security."""

import json
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DependencyCheckInput(BaseModel):
    """Input schema for dependency checking."""

    package_name: str = Field(..., description="Name of the package/dependency")
    ecosystem: str = Field(
        ...,
        description="Package ecosystem: 'npm', 'pypi', 'maven', or 'nuget'"
    )


class DependencyCheckTool(BaseTool):
    """Checks package metadata, maintenance status, and security issues."""

    name: str = "Dependency Check"
    description: str = (
        "Evaluates a package dependency for version currency, maintenance status, "
        "security vulnerabilities (CVEs), license compliance, and popularity metrics. "
        "For MVP, uses curated data file. Use this to assess dependency risk before "
        "introducing new packages."
    )
    args_schema: Type[BaseModel] = DependencyCheckInput

    def _run(self, package_name: str, ecosystem: str) -> str:
        """Check dependency health and security."""
        try:
            # Load dependency data
            data_path = Path(__file__).parent.parent.parent / "data" / "dependencies.json"

            # For MVP, use static data file
            # Future enhancement: call npm registry API, pypi API, etc.
            if not data_path.exists():
                return (
                    f"Dependency data not available.\n\n"
                    f"For production use, integrate with:\n"
                    f"  - npm: registry.npmjs.org API\n"
                    f"  - pypi: pypi.org/pypi/{package_name}/json\n"
                    f"  - maven: search.maven.org API\n"
                    f"  - nuget: api.nuget.org API\n\n"
                    f"Recommendation: Perform manual dependency review for {package_name}"
                )

            with open(data_path, "r") as f:
                dependency_db = json.load(f)

            # Look up package
            package_key = f"{ecosystem}:{package_name}".lower()

            if package_key not in dependency_db:
                return (
                    f"Dependency Check: {package_name} ({ecosystem})\n"
                    + "=" * 60 + "\n"
                    + "Status: NOT IN CURATED DATABASE\n\n"
                    + "This package has not been pre-evaluated.\n\n"
                    + "Required checks:\n"
                    + "  1. Verify package authenticity and ownership\n"
                    + "  2. Check recent release activity (< 12 months)\n"
                    + "  3. Review open issues and CVEs\n"
                    + "  4. Verify license compatibility\n"
                    + "  5. Assess weekly download volume\n"
                    + "  6. Check for active maintainers\n"
                )

            pkg = dependency_db[package_key]

            result = f"Dependency Check: {pkg['name']} ({ecosystem})\n"
            result += "=" * 60 + "\n\n"

            result += "VERSION & FRESHNESS\n"
            result += "-" * 40 + "\n"
            result += f"Latest Version: {pkg['latest_version']}\n"
            result += f"Last Updated: {pkg['last_updated']}\n"
            result += f"Release Frequency: {pkg.get('release_frequency', 'Unknown')}\n\n"

            result += "POPULARITY & ADOPTION\n"
            result += "-" * 40 + "\n"
            result += f"Weekly Downloads: {pkg.get('weekly_downloads', 'N/A'):,}\n"
            result += f"GitHub Stars: {pkg.get('github_stars', 'N/A'):,}\n"
            result += f"Dependents: {pkg.get('dependents', 'N/A'):,}\n\n"

            result += "MAINTENANCE STATUS\n"
            result += "-" * 40 + "\n"
            status = pkg.get('maintenance_status', 'unknown')
            if status == "active":
                result += "Status: ✓ ACTIVE (regular updates)\n"
            elif status == "maintained":
                result += "Status: ✓ MAINTAINED (stable, occasional updates)\n"
            elif status == "unmaintained":
                result += "Status: ⚠ UNMAINTAINED (no recent activity)\n"
            elif status == "deprecated":
                result += "Status: ✗ DEPRECATED (do not use)\n"

            if pkg.get("maintainers"):
                result += f"Maintainers: {', '.join(pkg['maintainers'])}\n"
            result += "\n"

            result += "SECURITY\n"
            result += "-" * 40 + "\n"
            cve_count = pkg.get('known_cves', 0)
            if cve_count == 0:
                result += "Known CVEs: ✓ None\n"
            else:
                result += f"Known CVEs: ⚠ {cve_count} vulnerabilities\n"
                if pkg.get('cve_details'):
                    for cve in pkg['cve_details']:
                        result += f"  - {cve['id']}: {cve['severity']} - {cve['description']}\n"
            result += "\n"

            result += "LICENSE\n"
            result += "-" * 40 + "\n"
            license_name = pkg.get('license', 'Unknown')
            result += f"License: {license_name}\n"

            # License risk assessment
            permissive_licenses = ['MIT', 'Apache-2.0', 'BSD-3-Clause', 'BSD-2-Clause', 'ISC']
            copyleft_licenses = ['GPL-3.0', 'GPL-2.0', 'AGPL-3.0', 'LGPL-3.0']

            if license_name in permissive_licenses:
                result += "Risk: ✓ LOW (permissive license)\n"
            elif license_name in copyleft_licenses:
                result += "Risk: ⚠ MEDIUM (copyleft license - legal review required)\n"
            else:
                result += "Risk: ⚠ UNKNOWN (license review required)\n"
            result += "\n"

            result += "RECOMMENDATION\n"
            result += "-" * 40 + "\n"

            # Generate recommendation
            issues = []
            if status in ['unmaintained', 'deprecated']:
                issues.append(f"Package is {status}")
            if cve_count > 0:
                issues.append(f"{cve_count} known security vulnerabilities")
            if license_name in copyleft_licenses:
                issues.append("Copyleft license requires legal review")

            if not issues:
                result += "✓ APPROVED - No significant concerns\n"
            elif len(issues) == 1 and "legal review" in issues[0]:
                result += "⚠ CONDITIONAL - Proceed after legal review\n"
            else:
                result += "✗ NOT RECOMMENDED\n"
                result += "Issues:\n"
                for issue in issues:
                    result += f"  - {issue}\n"

                if pkg.get('alternatives'):
                    result += "\nConsider alternatives:\n"
                    for alt in pkg['alternatives']:
                        result += f"  - {alt}\n"

            return result

        except Exception as e:
            return f"Error checking dependency {package_name}: {str(e)}"
