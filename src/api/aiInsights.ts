const BASE_URL = "https://stockmarket-backend-sa4e.onrender.com";

export interface AIInsightResponse {
  symbol: string;
  configured: boolean;
  content: string | null;
  disclaimer: string;
}

export interface AIChatResponse {
  configured: boolean;
  answer: string | null;
  disclaimer: string;
}

export async function fetchAIInsight(symbol: string): Promise<AIInsightResponse> {
  const params = new URLSearchParams({ symbol });
  const res = await fetch(`${BASE_URL}/api/ai-insights?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`AI insight API error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as AIInsightResponse;
}

export async function askAIChat(symbol: string, question: string): Promise<AIChatResponse> {
  const res = await fetch(`${BASE_URL}/api/ai-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol, question })
  });
  if (!res.ok) {
    throw new Error(`AI chat API error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as AIChatResponse;
}
