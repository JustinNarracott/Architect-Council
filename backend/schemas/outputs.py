"""Pydantic schemas for agent outputs and API contracts."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RulingOutcome(str, Enum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class AgentOutput(BaseModel):
    """Base output schema for all specialist agents."""

    score: int = Field(..., ge=0, le=100, description="Numerical score (0-100 scale)")
    confidence: ConfidenceLevel = Field(
        ..., description="Confidence level of the analysis"
    )
    evidence: list[str] = Field(
        ..., description="Key supporting evidence (specific data points)"
    )
    concerns: list[str] = Field(
        default_factory=list, description="Primary concerns or caveats"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StandardsAnalystOutput(AgentOutput):
    """Output from the Standards Analyst agent."""

    agent_type: Literal["standards_analyst"] = "standards_analyst"
    tech_radar_status: str | None = Field(
        None, description="Technology status on radar (adopt/trial/assess/hold)"
    )
    pattern_compliance: str = Field(
        ..., description="Assessment of design pattern compliance"
    )
    anti_patterns_identified: list[str] = Field(
        default_factory=list, description="Anti-patterns detected"
    )
    standards_violations: list[str] = Field(
        default_factory=list, description="Standards violations found"
    )
    naming_structure_assessment: str | None = Field(
        None, description="Naming and structure compliance assessment"
    )


class DXAnalystOutput(AgentOutput):
    """Output from the DX Analyst agent."""

    agent_type: Literal["dx_analyst"] = "dx_analyst"
    adoption_friction_summary: str = Field(
        ..., description="Summary of adoption friction assessment"
    )
    learning_curve_estimate: str | None = Field(
        None, description="Estimated learning curve (time to productivity)"
    )
    documentation_quality: str | None = Field(
        None, description="Documentation quality assessment"
    )
    community_health: str | None = Field(
        None, description="Community health indicators"
    )
    hiring_market_assessment: str | None = Field(
        None, description="Talent availability assessment"
    )
    team_capability_gaps: list[str] = Field(
        default_factory=list, description="Identified team capability gaps"
    )


class EnterpriseArchitectOutput(AgentOutput):
    """Output from the Enterprise Architect agent."""

    agent_type: Literal["enterprise_architect"] = "enterprise_architect"
    strategic_alignment_summary: str = Field(
        ..., description="Strategic alignment assessment"
    )
    integration_impact: str = Field(
        ..., description="Impact on existing service integration"
    )
    duplication_concerns: list[str] = Field(
        default_factory=list, description="Identified capability duplication"
    )
    dependency_graph_impact: str | None = Field(
        None, description="Impact on dependency graph"
    )
    roadmap_alignment: str | None = Field(
        None, description="Alignment with platform roadmap"
    )


class SecurityAnalystOutput(AgentOutput):
    """Output from the Security & Resilience Analyst agent."""

    agent_type: Literal["security_analyst"] = "security_analyst"
    threat_surface_assessment: str = Field(
        ..., description="Threat surface change assessment"
    )
    data_classification: str = Field(
        ..., description="Data classification level (Public/Internal/Confidential/Restricted)"
    )
    compliance_implications: list[str] = Field(
        default_factory=list, description="Regulatory compliance implications"
    )
    failure_modes: list[str] = Field(
        default_factory=list, description="Identified failure modes"
    )
    blast_radius_assessment: str | None = Field(
        None, description="Blast radius and containment assessment"
    )
    rollback_capability: str | None = Field(
        None, description="Rollback capability assessment"
    )
    security_controls_required: list[str] = Field(
        default_factory=list, description="Required security controls"
    )


class AgentScore(BaseModel):
    """Individual agent score for the consensus report."""

    agent_name: str
    score: int = Field(..., ge=0, le=100)
    rationale: str


class ArchitectureRuling(BaseModel):
    """Final architecture ruling from the Design Authority Chair."""

    title: str
    technology: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ruling: RulingOutcome
    confidence: ConfidenceLevel
    agent_scores: list[AgentScore]
    key_agreements: list[str] = Field(..., description="Points where agents agree")
    key_disagreements: list[str] = Field(
        default_factory=list, description="Points of contention"
    )
    disagreement_resolution: str | None = Field(
        None, description="How disagreements were resolved"
    )
    conditions: list[str] = Field(
        default_factory=list,
        description="Conditions for approval (if ruling is CONDITIONAL)",
    )
    rationale: str = Field(..., description="Detailed reasoning for the ruling")
    dissenting_opinions: list[str] = Field(
        default_factory=list, description="Recorded dissenting opinions"
    )
    next_steps: list[str] = Field(
        default_factory=list, description="Recommended next steps"
    )


# API Contracts


class ADRRequest(BaseModel):
    """Request to evaluate an architecture decision."""

    title: str = Field(..., min_length=1, description="ADR title/summary")
    technology: str = Field(..., min_length=1, description="Technology or pattern being proposed")
    reason: str = Field(..., min_length=1, description="Justification for the proposal")
    affected_services: list[str] = Field(
        default_factory=list, description="Services affected by this decision"
    )
    data_classification: str = Field(
        ..., description="Data classification level (Public/Internal/Confidential/Restricted)"
    )
    proposer: str = Field(..., min_length=1, description="Name or team proposing the decision")


class AnalysisResponse(BaseModel):
    """Response containing review/analysis ID for streaming."""

    analysis_id: str
    stream_url: str
    status: str = "started"


# Type alias for clarity in architecture domain
ReviewResponse = AnalysisResponse


class AgentMessageType(str, Enum):
    THINKING = "thinking"
    ANALYSIS = "analysis"
    CHALLENGE = "challenge"
    RULING = "ruling"
    ERROR = "error"


class AgentMessage(BaseModel):
    """A message from an agent during deliberation (for SSE streaming)."""

    analysis_id: str
    agent_id: str
    agent_name: str
    message_type: AgentMessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict | None = None


class AgentInfo(BaseModel):
    """Information about an available agent."""

    id: str
    name: str
    role: str
    description: str
    focus_areas: list[str]
    llm_provider: str = Field(..., description="LLM provider powering this agent")


class RulingHistoryItem(BaseModel):
    """A past ruling record."""

    ruling_id: str
    title: str
    technology: str
    ruling: RulingOutcome
    confidence: ConfidenceLevel
    timestamp: datetime
