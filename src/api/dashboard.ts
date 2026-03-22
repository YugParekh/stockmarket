import type {
  AlertItem,
  KeywordStat,
  MarketDataPoint,
  NewsItem,
  PredictionDirection,
  SentimentBucket
} from "../mockMarketData";

export interface InsightsPayload {
  nextMove: {
    direction: PredictionDirection;
    confidence: number;
    expectedReturnPct: number;
    volatilityScore: number;
    horizon: string;
  };
  risk: {
    level: "Low" | "Medium" | "High";
    valueAtRiskPct: number;
  };
  commentary: string;
}

export interface DashboardPayload {
  symbol: string;
  range: string;
  marketData: MarketDataPoint[];
  news: NewsItem[];
  alerts: AlertItem[];
  keywords: KeywordStat[];
  sentimentDistribution: SentimentBucket[];
  insights: InsightsPayload;
}

export type UiRange = "1D" | "5D" | "1M" | "3M" | "6M" | "1Y";

export async function fetchDashboardData(
  symbol: string,
  range: UiRange
): Promise<DashboardPayload> {
  const params = new URLSearchParams({ symbol, range });
  const res = await fetch(`/api/dashboard?${params.toString()}`);

  if (!res.ok) {
    throw new Error(`Dashboard API error: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as DashboardPayload;
  return json;
}

