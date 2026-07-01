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

/**
 * 🔥 BASE URL (PRODUCTION)
 * Change this if backend URL changes
 */
const BASE_URL = "https://stockmarket-backend-sa4e.onrender.com";

const rangeToDays = (range: UiRange): number => {
  const map: Record<UiRange, number> = {
    "1D": 1,
    "5D": 5,
    "1M": 30,
    "3M": 90,
    "6M": 180,
    "1Y": 365,
  };
  return map[range] || 1;
};

export async function fetchDashboardData(
  symbol: string,
  range: UiRange
): Promise<DashboardPayload> {
  const days = rangeToDays(range);
  const params = new URLSearchParams({ symbol, days: days.toString() });

  const res = await fetch(
    `${BASE_URL}/api/dashboard?${params.toString()}`
  );

  if (!res.ok) {
    throw new Error(
      `Dashboard API error: ${res.status} ${res.statusText}`
    );
  }

  const json = (await res.json()) as DashboardPayload;
  return json;
}