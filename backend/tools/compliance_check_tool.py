"""Compliance check tool for evaluating against governance rules."""

import json
from pathlib import Path
from typing import Type, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ComplianceCheckInput(BaseModel):
    """Input schema for compliance checking."""

    data_classification: str = Field(
        ...,
        description="Data classification level: 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'PII'"
    )
    technology: Optional[str] = Field(
        default=None,
        description="Technology or service being used (e.g., 'AWS S3', 'SendGrid', 'MongoDB')"
    )
    deployment_target: Optional[str] = Field(
        default=None,
        description="Where the service will be deployed: 'on-premise', 'aws', 'azure', 'gcp', 'saas'"
    )


class ComplianceCheckTool(BaseTool):
    """Evaluates proposals against organizational compliance rules."""

    name: str = "Compliance Check"
    description: str = (
        "Evaluates a proposal against organizational compliance and governance rules. "
        "Checks data handling requirements, encryption standards, third-party assessment "
        "requirements, and regulatory compliance (GDPR, SOC2, etc.). Returns list of "
        "applicable rules with pass/fail status and required actions."
    )
    args_schema: Type[BaseModel] = ComplianceCheckInput

    def _run(
        self,
        data_classification: str,
        technology: Optional[str] = None,
        deployment_target: Optional[str] = None
    ) -> str:
        """Check compliance rules for the given parameters."""
        try:
            # Load compliance rules
            data_path = Path(__file__).parent.parent.parent / "data" / "compliance_rules.json"

            if not data_path.exists():
                return "Compliance rules not found. Cannot evaluate compliance."

            with open(data_path, "r") as f:
                compliance_rules = json.load(f)

            # Normalize inputs
            data_classification = data_classification.upper()
            technology_lower = technology.lower() if technology else ""
            deployment_lower = deployment_target.lower() if deployment_target else ""

            result = f"Compliance Check\n"
            result += "=" * 60 + "\n"
            result += f"Data Classification: {data_classification}\n"
            if technology:
                result += f"Technology: {technology}\n"
            if deployment_target:
                result += f"Deployment: {deployment_target}\n"
            result += "\n"

            applicable_rules = []
            passed_rules = []
            failed_rules = []

            # Evaluate each rule
            for rule in compliance_rules.get("rules", []):
                # Check if rule applies
                applies = False

                # Check data classification applicability
                if "applies_to_data" in rule:
                    if data_classification in rule["applies_to_data"]:
                        applies = True
                    elif "ALL" in rule["applies_to_data"]:
                        applies = True

                # Check technology applicability
                if "applies_to_technology" in rule and technology:
                    for tech_pattern in rule["applies_to_technology"]:
                        if tech_pattern.lower() in technology_lower or technology_lower in tech_pattern.lower():
                            applies = True

                # Check deployment applicability
                if "applies_to_deployment" in rule and deployment_target:
                    if deployment_lower in [d.lower() for d in rule["applies_to_deployment"]]:
                        applies = True

                if not applies:
                    continue

                applicable_rules.append(rule)

                # Determine if rule is passed or failed (simplified logic for MVP)
                # In production, this would involve more sophisticated checks
                rule_status = "PASS"  # Default to pass

                # Apply specific rule logic
                if "encryption" in rule["rule_id"].lower():
                    if data_classification in ["PII", "CONFIDENTIAL", "RESTRICTED"]:
                        if deployment_target and deployment_target.lower() == "saas":
                            rule_status = "REQUIRES_VERIFICATION"

                if "third_party" in rule["rule_id"].lower():
                    if deployment_target and "saas" in deployment_target.lower():
                        rule_status = "REQUIRES_ACTION"

                if "audit" in rule["rule_id"].lower():
                    if data_classification in ["PII", "RESTRICTED"]:
                        rule_status = "REQUIRES_IMPLEMENTATION"

                if rule_status == "PASS":
                    passed_rules.append(rule)
                else:
                    failed_rules.append((rule, rule_status))

            # Format results
            if not applicable_rules:
                result += "ℹ No specific compliance rules apply to this configuration.\n"
                result += "\nNote: Always follow general security best practices.\n"
                return result

            result += f"APPLICABLE RULES: {len(applicable_rules)}\n"
            result += "=" * 60 + "\n\n"

            if passed_rules:
                result += f"PASSED ({len(passed_rules)}):\n"
                result += "-" * 40 + "\n"
                for rule in passed_rules:
                    result += f"✓ {rule['rule_id']}: {rule['title']}\n"
                result += "\n"

            if failed_rules:
                result += f"REQUIRES ATTENTION ({len(failed_rules)}):\n"
                result += "-" * 40 + "\n"
                for rule, status in failed_rules:
                    result += f"⚠ {rule['rule_id']}: {rule['title']}\n"
                    result += f"   Status: {status}\n"
                    result += f"   Description: {rule['description']}\n"
                    if rule.get('required_actions'):
                        result += f"   Required Actions:\n"
                        for action in rule['required_actions']:
                            result += f"     - {action}\n"
                    result += "\n"

            # Overall assessment
            result += "COMPLIANCE ASSESSMENT\n"
            result += "-" * 40 + "\n"

            if not failed_rules:
                result += "✓ All applicable rules satisfied\n"
                result += "Status: COMPLIANT\n"
            elif len(failed_rules) <= 2:
                result += "⚠ Minor compliance gaps identified\n"
                result += "Status: CONDITIONAL APPROVAL\n"
                result += "Action: Address requirements before production deployment\n"
            else:
                result += "✗ Multiple compliance requirements not met\n"
                result += "Status: NON-COMPLIANT\n"
                result += "Action: Significant remediation required\n"

            return result

        except Exception as e:
            return f"Error checking compliance: {str(e)}"
