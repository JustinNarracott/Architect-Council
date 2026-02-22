import { ADRRequest, AnalysisResponse, Agent, CodebaseRequest, CodebaseAnalysisResponse } from "@/types";

// ── Types ─────────────────────────────────────────────────────────────────────

type QueryEventCallback = (
  eventType: 'sources' | 'token' | 'error' | 'done',
  data: Record<string, unknown>
) => void;

// Call backend directly — CORS is configured to allow localhost:3011
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8011";

export async function getPanel(): Promise<Agent[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/panel`);
    if (!response.ok) {
      throw new Error("Failed to fetch panel members");
    }
    return response.json();
  } catch (error) {
    console.error("Error fetching panel:", error);
    return [];
  }
}

export async function submitReview(request: ADRRequest): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to submit review: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function getRulings(): Promise<unknown[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/rulings`);
    if (!response.ok) {
      throw new Error("Failed to fetch rulings");
    }
    return response.json();
  } catch (error) {
    console.error("Error fetching rulings:", error);
    return [];
  }
}

export async function getTechRadar(): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/api/tech-radar`);
  if (!response.ok) {
    throw new Error("Failed to fetch tech radar");
  }
  return response.json();
}

export async function submitCodebaseReview(request: CodebaseRequest): Promise<CodebaseAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/codebase/analyse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to submit codebase review: ${response.status} ${errorText}`);
  }

  return response.json();
}

/**
 * Stream a conversational query over the analysed codebase via SSE.
 *
 * Calls POST /api/codebase/{analysisId}/query and emits SSE events:
 *   sources  — list of code chunks used for context
 *   token    — streamed response tokens
 *   error    — error payload
 *   done     — stream completed
 */
export async function queryChatStream(
  analysisId: string,
  question: string,
  onEvent: QueryEventCallback,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/codebase/${analysisId}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "text/event-stream",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Query failed: ${response.status} ${errorText}`);
  }

  if (!response.body) {
    throw new Error("No response body from query endpoint");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    let eventType = "message";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        const raw = line.slice(5).trim();
        try {
          const data = JSON.parse(raw);
          onEvent(eventType as Parameters<QueryEventCallback>[0], data);
        } catch {
          // ignore malformed JSON
        }
        eventType = "message";
      }
    }
  }
}

/**
 * List available project directories from the /repos volume mount.
 */
export async function fetchLocalRepos(): Promise<string[]> {
  const res = await fetch(`${API_BASE_URL}/api/codebase/local-repos`);
  if (!res.ok) return [];
  return res.json();
}

/**
 * Delete an analysis session and its RAG index.
 */
export async function deleteAnalysis(analysisId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/codebase/${analysisId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete analysis: ${response.status} ${errorText}`);
  }
}

// ── Governance Config ─────────────────────────────────────────────────────────

export interface GovernanceFile {
  filename: string;
  content: Record<string, unknown>;
  raw_yaml: string;
}

export interface GovernanceOverview {
  files: GovernanceFile[];
  is_configured: boolean;
}

export async function fetchGovernanceConfig(): Promise<GovernanceOverview> {
  const res = await fetch(`${API_BASE_URL}/api/governance/config`);
  if (!res.ok) throw new Error('Failed to fetch governance config');
  return res.json();
}

export async function updateGovernanceFile(filename: string, rawYaml: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/governance/config/${filename}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw_yaml: rawYaml }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to save');
  }
}
