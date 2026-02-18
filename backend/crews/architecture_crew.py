"""Architecture crew configuration for ADR evaluation."""

from collections.abc import Callable
from typing import Any

from crewai import Crew, Process, Task

from backend.agents import (
    get_da_chair,
    get_dx_analyst,
    get_enterprise_architect,
    get_security_analyst,
    get_standards_analyst,
)

# Map agent roles to frontend agent IDs
ROLE_TO_AGENT_ID = {
    "Standards Analyst": "standards_analyst",
    "Developer Experience Analyst": "dx_analyst",
    "Enterprise Architect": "enterprise_architect",
    "Security & Resilience Analyst": "security_analyst",
    "Design Authority Chair": "da_chair",
}


def create_architecture_crew(
    title: str,
    technology: str,
    reason: str,
    affected_services: list[str],
    data_classification: str,
    proposer: str,
    task_callback: Callable[[Any], None] | None = None,
) -> Crew:
    """
    Create an architecture evaluation crew for the given ADR proposal.

    Args:
        title: ADR title/summary
        technology: Technology or pattern being proposed
        reason: Justification for the proposal
        affected_services: Services affected by this decision
        data_classification: Data classification level
        proposer: Name or team proposing the decision

    Returns:
        Configured Crew ready for execution
    """
    # Get agent instances (lazily created)
    standards_analyst = get_standards_analyst()
    dx_analyst = get_dx_analyst()
    enterprise_architect = get_enterprise_architect()
    security_analyst = get_security_analyst()
    da_chair = get_da_chair()

    # Format affected services for display
    services_str = (
        f"\nAffected services: {', '.join(affected_services)}"
        if affected_services
        else "\nNo services directly affected"
    )

    # Task 1: Standards Analysis (can run in parallel with other specialists)
    standards_task = Task(
        description=(
            f"Evaluate the proposal '{title}' for standards compliance.\n\n"
            f"Technology: {technology}\n"
            f"Reason: {reason}{services_str}\n"
            f"Proposer: {proposer}\n\n"
            "Your analysis must include:\n"
            "1. Technology radar status - Is this technology in ADOPT/TRIAL/ASSESS/HOLD?\n"
            "2. Design pattern compliance - Does it follow our approved patterns?\n"
            "3. Anti-pattern detection - Are there any known anti-patterns being implemented?\n"
            "4. API design standards - Does it comply with REST/GraphQL/gRPC conventions?\n"
            "5. Naming and code structure - Does it follow our conventions?\n"
            "6. Standards violations - Any specific violations of our engineering standards?\n\n"
            "Conclude with a score (0-100) where 100 = fully compliant with all standards."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Standards Compliance Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Tech Radar Status\n\n"
            "| Technology | Radar Position | Approved Since | Conditions |\n"
            "|-----------|---------------|----------------|------------|\n"
            "| ... | ADOPT/TRIAL/ASSESS/HOLD | YYYY-MM | ... |\n\n"
            "## Design Pattern Compliance\n\n"
            "| Pattern | Status | Notes |\n"
            "|---------|--------|-------|\n"
            "| ... | ✅ Compliant / ❌ Violation / ⚠️ Concern | ... |\n\n"
            "## Anti-Pattern Detection\n\n"
            "| # | Anti-Pattern | Detected? | Evidence | Severity |\n"
            "|---|-------------|-----------|----------|----------|\n"
            "| 1 | ... | ✅ None / ❌ Found | ... | CRITICAL/HIGH/MEDIUM/LOW |\n\n"
            "## API Design Standards\n\n"
            "| Standard | Compliant? | Notes |\n"
            "|----------|-----------|-------|\n"
            "| REST conventions | ✅/❌ | ... |\n"
            "| Versioning | ✅/❌ | ... |\n"
            "| Naming conventions | ✅/❌ | ... |\n\n"
            "## Standards Violations\n\n"
            "| # | Violation | Severity | Standard Reference | Recommendation |\n"
            "|---|-----------|----------|--------------------|----------------|\n"
            "| 1 | ... | CRITICAL/HIGH/MEDIUM/LOW | ... | ... |\n\n"
            "**No violations found** — state explicitly if clean.\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=standards_analyst,
        async_execution=True,  # Can run in parallel with other specialists
    )

    # Task 2: Developer Experience Analysis
    dx_task = Task(
        description=(
            f"Evaluate the proposal '{title}' for developer experience and team adoption.\n\n"
            f"Technology: {technology}\n"
            f"Reason: {reason}{services_str}\n"
            f"Proposer: {proposer}\n\n"
            "Your analysis must include:\n"
            "1. Team capability - Do we have the skills, or what's the learning curve?\n"
            "2. Documentation quality - Is the ecosystem well-documented?\n"
            "3. Community health - GitHub activity, Stack Overflow presence, maintainer responsiveness\n"
            "4. Hiring market - Can we hire people with this skill?\n"
            "5. Onboarding complexity - Time to productivity for new team members\n"
            "6. Developer tooling - IDE support, debugging tools, testing frameworks\n"
            "7. Adoption friction - What barriers exist to successful adoption?\n\n"
            "Conclude with a score (0-100) where 100 = zero adoption friction."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Developer Experience Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Adoption Friction Summary\n\n"
            "[1-2 sentence summary of adoption difficulty]\n\n"
            "## Learning Curve\n\n"
            "| Aspect | Time Estimate | Notes |\n"
            "|--------|-------------- |-------|\n"
            "| Basic proficiency | X days/weeks | ... |\n"
            "| Production readiness | X weeks/months | ... |\n"
            "| Advanced features | X months | ... |\n\n"
            "## Documentation Quality\n\n"
            "| Criterion | Rating | Notes |\n"
            "|-----------|--------|-------|\n"
            "| Official docs | Excellent/Good/Fair/Poor | ... |\n"
            "| Tutorials & guides | Excellent/Good/Fair/Poor | ... |\n"
            "| API reference | Excellent/Good/Fair/Poor | ... |\n"
            "| Community resources | Excellent/Good/Fair/Poor | ... |\n\n"
            "## Community Health\n\n"
            "| Indicator | Value | Assessment |\n"
            "|-----------|-------|------------|\n"
            "| GitHub stars | X | ... |\n"
            "| Contributors | X | ... |\n"
            "| Stack Overflow questions | X | ... |\n"
            "| Release frequency | X | ... |\n"
            "| Maintainer responsiveness | ... | ... |\n\n"
            "## Hiring Market\n\n"
            "| Metric | Value | Notes |\n"
            "|--------|-------|-------|\n"
            "| Job postings mentioning tech | X% | ... |\n"
            "| Talent availability | High/Medium/Low | ... |\n"
            "| Salary premium | +X% / neutral / -X% | ... |\n\n"
            "## Team Capability Gaps\n\n"
            "| Gap | Severity | Mitigation |\n"
            "|-----|----------|------------|\n"
            "| ... | High/Medium/Low | ... |\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=dx_analyst,
        async_execution=True,  # Can run in parallel with other specialists
    )

    # Task 3: Enterprise Architecture Analysis
    enterprise_task = Task(
        description=(
            f"Evaluate the proposal '{title}' for enterprise architecture alignment.\n\n"
            f"Technology: {technology}\n"
            f"Reason: {reason}{services_str}\n"
            f"Proposer: {proposer}\n\n"
            "Your analysis must include:\n"
            "1. Strategic alignment - Does this fit our technology roadmap?\n"
            "2. Integration impact - How does this affect existing services?\n"
            "3. API contract changes - Are there breaking changes or versioning concerns?\n"
            "4. Duplication assessment - Do we already have this capability?\n"
            "5. Dependency graph impact - What new dependencies are introduced?\n"
            "6. Data flow implications - How does data move through the system?\n"
            "7. Build vs. buy vs. reuse - Should we extend existing capabilities instead?\n\n"
            "Conclude with a score (0-100) where 100 = perfect strategic alignment."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Enterprise Architecture Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Strategic Alignment\n\n"
            "[Assessment of alignment with technology roadmap and organisational strategy]\n\n"
            "## Integration Impact\n\n"
            "| Service | Impact | Risk Level | Notes |\n"
            "|---------|--------|-----------|-------|\n"
            "| ... | Breaking/Non-breaking/None | High/Medium/Low | ... |\n\n"
            "## Duplication Assessment\n\n"
            "| Existing Capability | Overlap? | Recommendation |\n"
            "|-------------------|----------|----------------|\n"
            "| ... | ✅ None / ⚠️ Partial / ❌ Full | Build / Buy / Reuse |\n\n"
            "## Dependency Graph Impact\n\n"
            "| New Dependency | Type | Risk | Notes |\n"
            "|---------------|------|------|-------|\n"
            "| ... | Runtime/Dev/Infra | High/Medium/Low | ... |\n\n"
            "## Data Flow Implications\n\n"
            "[Assessment of data flow changes, consistency concerns, classification handling]\n\n"
            "## Build vs Buy vs Reuse\n\n"
            "| Option | Pros | Cons | Recommendation |\n"
            "|--------|------|------|----------------|\n"
            "| Build | ... | ... | ✅/❌ |\n"
            "| Buy | ... | ... | ✅/❌ |\n"
            "| Reuse | ... | ... | ✅/❌ |\n\n"
            "## Roadmap Alignment\n\n"
            "[Assessment of fit with platform roadmap and future plans]\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=enterprise_architect,
        async_execution=True,  # Can run in parallel with other specialists
    )

    # Task 4: Security & Resilience Analysis
    security_task = Task(
        description=(
            f"Evaluate the proposal '{title}' for security and resilience.\n\n"
            f"Technology: {technology}\n"
            f"Reason: {reason}{services_str}\n"
            f"Data Classification: {data_classification}\n"
            f"Proposer: {proposer}\n\n"
            "Your analysis must include:\n"
            "1. Threat surface assessment - How does this change our attack surface?\n"
            "2. Data classification compliance - Proper handling for {data_classification} data?\n"
            "3. Authentication and authorization - Are auth mechanisms appropriate?\n"
            "4. Failure mode analysis - What can go wrong and what's the impact?\n"
            "5. Blast radius - If this fails, what else is affected?\n"
            "6. Rollback capability - Can we safely rollback if needed?\n"
            "7. Compliance implications - GDPR, SOC2, ISO27001 concerns\n"
            "8. Required security controls - What safeguards must be in place?\n\n"
            "Conclude with a score (0-100) where 100 = no security or resilience concerns."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Security & Resilience Report\n\n"
            "## Score\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Score** | X / 100 |\n"
            "| **Rating** | GREEN / AMBER / RED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Threat Surface Assessment\n\n"
            "| Threat | Likelihood | Impact | Mitigation |\n"
            "|--------|-----------|--------|------------|\n"
            "| ... | High/Medium/Low | High/Medium/Low | ... |\n\n"
            "## Data Classification Handling\n\n"
            "| Requirement | Status | Notes |\n"
            "|-------------|--------|-------|\n"
            "| Encryption in transit | ✅/❌ Required | ... |\n"
            "| Encryption at rest | ✅/❌ Required | ... |\n"
            "| Access controls | ✅/❌ Required | ... |\n"
            "| Audit logging | ✅/❌ Required | ... |\n\n"
            "## Compliance Implications\n\n"
            "| Framework | Relevant? | Concern | Mitigation |\n"
            "|-----------|----------|---------|------------|\n"
            "| GDPR | ✅/❌ | ... | ... |\n"
            "| SOC2 | ✅/❌ | ... | ... |\n"
            "| ISO27001 | ✅/❌ | ... | ... |\n\n"
            "## Failure Modes\n\n"
            "| # | Failure Mode | Impact | Probability | Mitigation |\n"
            "|---|-------------|--------|------------|------------|\n"
            "| 1 | ... | High/Medium/Low | High/Medium/Low | ... |\n\n"
            "## Blast Radius\n\n"
            "| Component | Affected? | Impact if Failed |\n"
            "|-----------|----------|------------------|\n"
            "| ... | Primary/Secondary/None | ... |\n\n"
            "## Rollback Capability\n\n"
            "| Aspect | Status | Notes |\n"
            "|--------|--------|-------|\n"
            "| Feature flag available | ✅/❌ | ... |\n"
            "| Data migration reversible | ✅/❌ | ... |\n"
            "| Rollback tested | ✅/❌ | ... |\n\n"
            "## Required Security Controls\n\n"
            "| # | Control | Priority | Status |\n"
            "|---|---------|----------|--------|\n"
            "| 1 | ... | MUST/SHOULD/COULD | Proposed/Exists/Missing |\n\n"
            "## Recommendations\n\n"
            "| Priority | Recommendation | Effort | Impact |\n"
            "|----------|---------------|--------|--------|\n"
            "| 1 | ... | Low/Medium/High | Low/Medium/High |\n"
        ),
        agent=security_analyst,
        async_execution=True,  # Can run in parallel with other specialists
    )

    # Task 5: Design Authority Ruling (Synthesis)
    ruling_task = Task(
        description=(
            f"Synthesize all specialist analyses for '{title}' and deliver final architecture ruling.\n\n"
            f"Technology: {technology}\n"
            f"Reason: {reason}{services_str}\n"
            f"Data Classification: {data_classification}\n"
            f"Proposer: {proposer}\n\n"
            "You have received analyses from:\n"
            "1. Standards Analyst - Tech radar, patterns, standards compliance\n"
            "2. DX Analyst - Team capability, adoption friction, community health\n"
            "3. Enterprise Architect - Strategic alignment, integration, duplication\n"
            "4. Security & Resilience Analyst - Threat surface, compliance, failure modes\n\n"
            "Your ruling must:\n"
            "1. Review each specialist's score and key findings\n"
            "2. Identify where specialists agree (strengthens confidence)\n"
            "3. Identify where specialists disagree (requires your judgment)\n"
            "4. Resolve conflicts with clear reasoning\n"
            "5. Weight evidence appropriately for the organization's priorities\n"
            "6. Deliver a ruling: APPROVED / CONDITIONAL / REJECTED / DEFERRED\n"
            "7. For CONDITIONAL: specify measurable conditions that must be met\n"
            "8. Record any dissenting opinions fairly\n"
            "9. Provide clear next steps\n\n"
            "Be decisive but transparent. Explain your reasoning so the proposer understands "
            "the decision, whether they agree with it or not."
        ),
        expected_output=(
            "You MUST format your response EXACTLY as the following markdown template.\n"
            "Fill in all sections. Use markdown tables where indicated.\n\n"
            "# Design Authority Ruling\n\n"
            "## Ruling\n\n"
            "| Metric | Value |\n"
            "|--------|-------|\n"
            "| **Ruling** | APPROVED / CONDITIONAL / REJECTED / DEFERRED |\n"
            "| **Confidence** | low / medium / high |\n\n"
            "## Specialist Scores\n\n"
            "| Analyst | Score | Rating | Key Finding |\n"
            "|---------|-------|--------|-------------|\n"
            "| Standards | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Developer Experience | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Enterprise Architecture | X/100 | GREEN/AMBER/RED | ... |\n"
            "| Security & Resilience | X/100 | GREEN/AMBER/RED | ... |\n\n"
            "## Key Agreements\n\n"
            "[Points where 2+ specialists agree — strengthens confidence]\n\n"
            "## Key Disagreements\n\n"
            "| Point | Position A | Position B | Resolution |\n"
            "|-------|-----------|-----------|------------|\n"
            "| ... | ... (Analyst) | ... (Analyst) | ... |\n\n"
            "## Conditions (if CONDITIONAL)\n\n"
            "| # | Condition | Owner | Deadline | Measurable Criteria |\n"
            "|---|-----------|-------|----------|--------------------|\n"
            "| 1 | ... | ... | ... | ... |\n\n"
            "**If APPROVED:** State this section is not applicable.\n"
            "**If REJECTED:** State the blocking reasons clearly.\n\n"
            "## Dissenting Opinions\n\n"
            "[Record any specialist dissent fairly, even if overruled]\n\n"
            "## Rationale\n\n"
            "[2-3 paragraphs explaining the ruling — why this decision, "
            "how evidence was weighted, what tipped the balance]\n\n"
            "## Next Steps\n\n"
            "| # | Action | Owner | Timeline |\n"
            "|---|--------|-------|----------|\n"
            "| 1 | ... | ... | ... |\n"
            "| 2 | ... | ... | ... |\n"
            "| 3 | ... | ... | ... |\n"
        ),
        agent=da_chair,
        context=[
            standards_task,
            dx_task,
            enterprise_task,
            security_task,
        ],
    )

    # Create the crew with sequential process
    # The 4 specialist tasks have async_execution=True, so they'll run in parallel
    # The ruling task has context dependencies, so it waits for all 4 to complete
    crew = Crew(
        agents=[
            da_chair,
            standards_analyst,
            dx_analyst,
            enterprise_architect,
            security_analyst,
        ],
        tasks=[
            standards_task,
            dx_task,
            enterprise_task,
            security_task,
            ruling_task,
        ],
        process=Process.sequential,  # Sequential with async tasks = parallel specialists + synthesis
        verbose=True,
        memory=False,  # Disable memory to avoid additional LLM calls that may hit Perplexity
        planning=False,  # Disable planning — tasks have detailed descriptions; planning routes through
                         # all agent LLMs which causes Perplexity 'empty content' errors
        task_callback=task_callback,
    )

    return crew


def run_evaluation(
    title: str,
    technology: str,
    reason: str,
    affected_services: list[str],
    data_classification: str,
    proposer: str,
) -> str:
    """
    Run a complete architecture evaluation for the given ADR proposal.

    Args:
        title: ADR title/summary
        technology: Technology or pattern being proposed
        reason: Justification for the proposal
        affected_services: Services affected by this decision
        data_classification: Data classification level
        proposer: Name or team proposing the decision

    Returns:
        The final architecture ruling as a string
    """
    crew = create_architecture_crew(
        title=title,
        technology=technology,
        reason=reason,
        affected_services=affected_services,
        data_classification=data_classification,
        proposer=proposer,
    )
    result = crew.kickoff(
        inputs={
            "title": title,
            "technology": technology,
            "reason": reason,
            "affected_services": affected_services,
            "data_classification": data_classification,
            "proposer": proposer,
        }
    )
    return result.raw
