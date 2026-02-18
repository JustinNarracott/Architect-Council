import { ADRRequest, AnalysisResponse, Agent } from "@/types";

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
