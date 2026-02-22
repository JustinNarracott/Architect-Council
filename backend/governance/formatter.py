"""Format governance config into agent-specific prompt sections."""

from backend.governance import GovernanceConfig


def format_for_standards(config: GovernanceConfig) -> str:
    """Format governance rules relevant to the Standards Analyst."""
    if config.is_empty:
        return ""

    sections = ["## Organisation Governance Rules\n"]
    sections.append("Evaluate the codebase against THESE SPECIFIC rules (not generic best practices):\n")

    # Tech radar
    if config.tech_radar:
        sections.append("### Technology Radar")
        for category in ["adopt", "trial", "assess", "hold"]:
            cat_data = config.tech_radar.get(category, {})
            if cat_data:
                desc = cat_data.get("description", "")
                techs = cat_data.get("technologies", [])
                if techs:
                    sections.append(f"**{category.upper()}** ({desc}): {', '.join(techs)}")
        sections.append("")

    # Coding standards
    if config.coding_standards:
        cs = config.coding_standards
        sections.append("### Coding Standards")

        if "naming_conventions" in cs:
            nc = cs["naming_conventions"]
            sections.append("**Naming conventions:**")
            for scope, rule in nc.items():
                if isinstance(rule, dict):
                    for lang, convention in rule.items():
                        sections.append(f"  - {scope} ({lang}): {convention}")
                else:
                    sections.append(f"  - {scope}: {rule}")

        if "required_patterns" in cs:
            sections.append("**Required patterns:**")
            for p in cs["required_patterns"]:
                sections.append(f"  - {p}")

        if "prohibited_patterns" in cs:
            sections.append("**Prohibited patterns (flag these as violations):**")
            for p in cs["prohibited_patterns"]:
                sections.append(f"  - {p}")

        if "code_quality" in cs:
            cq = cs["code_quality"]
            sections.append("**Code quality thresholds:**")
            if "max_file_lines" in cq:
                sections.append(f"  - Max file length: {cq['max_file_lines']} lines")
            if "max_function_lines" in cq:
                sections.append(f"  - Max function length: {cq['max_function_lines']} lines")
            if "required_tooling" in cq:
                sections.append("  - Required tooling:")
                for lang, tools in cq["required_tooling"].items():
                    for tool_type, tool_name in tools.items():
                        sections.append(f"    - {lang} {tool_type}: {tool_name}")
        sections.append("")

    return "\n".join(sections)


def format_for_dx(config: GovernanceConfig) -> str:
    """Format governance rules relevant to the DX Analyst."""
    if config.is_empty:
        return ""

    sections = ["## Organisation Governance Rules\n"]
    sections.append("Evaluate documentation and DX against THESE SPECIFIC expectations:\n")

    if config.coding_standards:
        cs = config.coding_standards
        if "documentation" in cs.get("code_quality", {}):
            sections.append("### Documentation Requirements")
            for req in cs["code_quality"]["documentation"]:
                sections.append(f"  - {req}")
            sections.append("")

        if "required_tooling" in cs.get("code_quality", {}):
            sections.append("### Required Developer Tooling")
            for lang, tools in cs["code_quality"]["required_tooling"].items():
                for tool_type, tool_name in tools.items():
                    sections.append(f"  - {lang} {tool_type}: {tool_name}")
            sections.append("")

    return "\n".join(sections)


def format_for_architecture(config: GovernanceConfig) -> str:
    """Format governance rules relevant to the Enterprise Architect."""
    if config.is_empty:
        return ""

    sections = ["## Organisation Governance Rules\n"]
    sections.append("Evaluate architecture against THESE SPECIFIC standards:\n")

    if config.architecture:
        arch = config.architecture

        if "approved_styles" in arch:
            sections.append("### Approved Architecture Styles")
            for style in arch["approved_styles"]:
                sections.append(f"  - {style}")
            sections.append("")

        if "constraints" in arch:
            sections.append("### Architecture Constraints")
            for key, value in arch["constraints"].items():
                if isinstance(value, list):
                    for item in value:
                        sections.append(f"  - {item}")
                else:
                    sections.append(f"  - {key}: {value}")
            sections.append("")

        if "api_standards" in arch:
            sections.append("### API Standards")
            for key, value in arch["api_standards"].items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

        if "data_layer" in arch:
            sections.append("### Data Layer Standards")
            for key, value in arch["data_layer"].items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

    return "\n".join(sections)


def format_for_security(config: GovernanceConfig) -> str:
    """Format governance rules relevant to the Security Analyst."""
    if config.is_empty:
        return ""

    sections = ["## Organisation Governance Rules\n"]
    sections.append("Evaluate security against THESE SPECIFIC policies:\n")

    if config.security:
        sec = config.security

        if "secrets" in sec:
            sections.append("### Secrets Policy")
            s = sec["secrets"]
            if "allowed_storage" in s:
                sections.append(f"  - Allowed storage: {', '.join(s['allowed_storage'])}")
            if "never_in_code" in s:
                sections.append(f"  - Never in code: {', '.join(s['never_in_code'])}")
            if "gitignore_required" in s:
                sections.append(f"  - Must be in .gitignore: {', '.join(s['gitignore_required'])}")
            sections.append("")

        if "authentication" in sec:
            sections.append("### Authentication Policy")
            auth = sec["authentication"]
            if "approved_methods" in auth:
                for method in auth["approved_methods"]:
                    sections.append(f"  - {method}")
            if "session_requirements" in auth:
                for req in auth["session_requirements"]:
                    sections.append(f"  - {req}")
            sections.append("")

        if "dependencies" in sec:
            sections.append("### Dependency Security Policy")
            deps = sec["dependencies"]
            for key, value in deps.items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

        if "error_handling" in sec:
            sections.append("### Error Handling Policy")
            for key, value in sec["error_handling"].items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

        if "input_validation" in sec:
            sections.append("### Input Validation Policy")
            iv = sec["input_validation"]
            if "approach" in iv:
                sections.append(f"  - Approach: {iv['approach']}")
            if "injection_prevention" in iv:
                for rule in iv["injection_prevention"]:
                    sections.append(f"  - {rule}")
            sections.append("")

    return "\n".join(sections)


def format_for_chair(config: GovernanceConfig) -> str:
    """Format governance rules relevant to the DA Chair."""
    if config.is_empty:
        return ""

    sections = ["## Organisation Governance Rules\n"]
    sections.append(
        "The following governance rules were provided to the specialist agents. "
        "Weight your findings accordingly — violations of these specific rules should "
        "be scored more severely than generic best-practice deviations.\n"
    )

    # Give chair a summary of all rules
    if config.tech_radar:
        hold_techs = config.tech_radar.get("hold", {}).get("technologies", [])
        if hold_techs:
            sections.append(f"**HOLD technologies (should not be used):** {', '.join(hold_techs)}")

    if config.coding_standards:
        prohibited = config.coding_standards.get("prohibited_patterns", [])
        if prohibited:
            sections.append(f"**Prohibited patterns:** {'; '.join(prohibited)}")

    if config.architecture:
        approved = config.architecture.get("approved_styles", [])
        if approved:
            sections.append(f"**Approved architecture styles:** {'; '.join(approved)}")

    if config.security:
        vuln_policy = config.security.get("dependencies", {}).get("vulnerability_policy", "")
        if vuln_policy:
            sections.append(f"**Vulnerability policy:** {vuln_policy}")

    sections.append("")
    return "\n".join(sections)
