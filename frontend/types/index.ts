// Architecture domain types
export type AgentMessageType = 'thinking' | 'analysis' | 'challenge' | 'ruling' | 'error';

export interface AgentMessage {
  analysis_id: string;
  agent_id: string;
  agent_name: string;
  message_type: AgentMessageType;
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

// API contract — matches backend ADRRequest schema exactly
export interface ADRRequest {
  title: string;
  technology: string;
  reason: string;
  affected_services: string[];
  data_classification: string;
  proposer: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  stream_url: string;
  status: string;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  focus_areas?: string[];
  llm_provider?: string;
}

export interface AgentState {
  id: string;
  name: string;
  status: 'idle' | 'thinking' | 'done';
}

// Ruling outcomes
export type RulingOutcome = "approved" | "conditional" | "rejected" | "deferred";
export type ConfidenceLevel = "low" | "medium" | "high";

export interface AgentScore {
  agent_name: string;
  score: number;
  rationale: string;
}

export interface ArchitectureRuling {
  title: string;
  technology: string;
  timestamp: string;
  ruling: RulingOutcome;
  confidence: ConfidenceLevel;
  agent_scores: AgentScore[];
  key_agreements: string[];
  key_disagreements: string[];
  disagreement_resolution?: string;
  conditions?: string[];
  rationale: string;
  dissenting_opinions?: string[];
  next_steps?: string[];
}

// Backward compat alias — remove once ResultsPanel is updated
export type ConsensusReport = ArchitectureRuling;
