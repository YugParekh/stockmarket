export type PredictionDirection = "UP" | "DOWN";

export interface MarketDataPoint {
  date: string;
  price: number;
  sentiment_score: number;
  volume: number;
  prediction: PredictionDirection;
  confidence: number;
}

// Local mock data used only as a fallback when the backend is unavailable.
export const mockMarketData: MarketDataPoint[] = [
  { date: "2026-02-05", price: 188.2, sentiment_score: 0.18, volume: 112_000_000, prediction: "UP", confidence: 68 },
  { date: "2026-02-06", price: 189.4, sentiment_score: 0.22, volume: 118_200_000, prediction: "UP", confidence: 70 },
  { date: "2026-02-09", price: 191.1, sentiment_score: 0.27, volume: 121_300_000, prediction: "UP", confidence: 72 },
  { date: "2026-02-10", price: 190.5, sentiment_score: 0.12, volume: 119_000_000, prediction: "DOWN", confidence: 61 },
  { date: "2026-02-11", price: 192.8, sentiment_score: 0.31, volume: 125_600_000, prediction: "UP", confidence: 74 },
  { date: "2026-02-12", price: 195.3, sentiment_score: 0.36, volume: 130_200_000, prediction: "UP", confidence: 76 },
  { date: "2026-02-13", price: 194.1, sentiment_score: 0.08, volume: 128_000_000, prediction: "DOWN", confidence: 59 },
  { date: "2026-02-16", price: 193.5, sentiment_score: -0.05, volume: 134_400_000, prediction: "DOWN", confidence: 57 },
  { date: "2026-02-17", price: 191.9, sentiment_score: -0.12, volume: 141_100_000, prediction: "DOWN", confidence: 55 },
  { date: "2026-02-18", price: 190.7, sentiment_score: -0.2, volume: 146_300_000, prediction: "DOWN", confidence: 58 },
  { date: "2026-02-19", price: 189.9, sentiment_score: -0.16, volume: 139_800_000, prediction: "DOWN", confidence: 60 },
  { date: "2026-02-20", price: 191.2, sentiment_score: -0.04, volume: 133_500_000, prediction: "UP", confidence: 62 },
  { date: "2026-02-23", price: 193.8, sentiment_score: 0.09, volume: 129_200_000, prediction: "UP", confidence: 66 },
  { date: "2026-02-24", price: 196.4, sentiment_score: 0.21, volume: 135_900_000, prediction: "UP", confidence: 71 },
  { date: "2026-02-25", price: 198.6, sentiment_score: 0.3, volume: 142_700_000, prediction: "UP", confidence: 75 },
  { date: "2026-02-26", price: 197.9, sentiment_score: 0.14, volume: 139_300_000, prediction: "DOWN", confidence: 63 },
  { date: "2026-02-27", price: 199.1, sentiment_score: 0.19, volume: 145_800_000, prediction: "UP", confidence: 69 },
  { date: "2026-03-02", price: 201.4, sentiment_score: 0.33, volume: 153_200_000, prediction: "UP", confidence: 78 },
  { date: "2026-03-03", price: 203.2, sentiment_score: 0.4, volume: 160_100_000, prediction: "UP", confidence: 81 },
  { date: "2026-03-04", price: 205.6, sentiment_score: 0.46, volume: 167_900_000, prediction: "UP", confidence: 84 },
  { date: "2026-03-05", price: 207.1, sentiment_score: 0.39, volume: 162_500_000, prediction: "UP", confidence: 80 },
  { date: "2026-03-06", price: 206.4, sentiment_score: 0.24, volume: 158_300_000, prediction: "DOWN", confidence: 71 },
  { date: "2026-03-07", price: 208.9, sentiment_score: 0.37, volume: 165_600_000, prediction: "UP", confidence: 82 },
  { date: "2026-03-08", price: 210.3, sentiment_score: 0.42, volume: 171_200_000, prediction: "UP", confidence: 85 },
  { date: "2026-03-09", price: 211.7, sentiment_score: 0.35, volume: 168_900_000, prediction: "UP", confidence: 79 },
  { date: "2026-03-10", price: 210.9, sentiment_score: 0.18, volume: 162_400_000, prediction: "DOWN", confidence: 69 },
  { date: "2026-03-11", price: 212.2, sentiment_score: 0.25, volume: 166_700_000, prediction: "UP", confidence: 73 },
  { date: "2026-03-12", price: 214.1, sentiment_score: 0.32, volume: 172_300_000, prediction: "UP", confidence: 77 },
  { date: "2026-03-13", price: 215.6, sentiment_score: 0.38, volume: 179_100_000, prediction: "UP", confidence: 83 }
];

export interface NewsItem {
  id: number;
  headline: string;
  sentiment: "Positive" | "Neutral" | "Negative";
  impact: "Low" | "Medium" | "High";
  timestamp: string;
}

export const newsFeed: NewsItem[] = [
  {
    id: 1,
    headline: "Apple unveils new AI chip boosting investor confidence",
    sentiment: "Positive",
    impact: "High",
    timestamp: "5 min ago"
  },
  {
    id: 2,
    headline: "Market weighs inflation data ahead of Fed decision",
    sentiment: "Neutral",
    impact: "Medium",
    timestamp: "17 min ago"
  },
  {
    id: 3,
    headline: "Analysts warn of stretched valuations in mega-cap tech",
    sentiment: "Negative",
    impact: "Medium",
    timestamp: "32 min ago"
  },
  {
    id: 4,
    headline: "Strong earnings from chipmakers signal resilient AI demand",
    sentiment: "Positive",
    impact: "High",
    timestamp: "49 min ago"
  },
  {
    id: 5,
    headline: "Geopolitical tensions spark brief risk-off move in equities",
    sentiment: "Negative",
    impact: "Low",
    timestamp: "1 hr ago"
  }
];

export interface AlertItem {
  id: number;
  message: string;
  severity: "Positive" | "Neutral" | "Negative";
  createdAt: string;
}

export const alerts: AlertItem[] = [
  {
    id: 1,
    message: "High negative sentiment detected in semiconductor sector",
    severity: "Negative",
    createdAt: "2 min ago"
  },
  {
    id: 2,
    message: "Unusual trading volume spike in NVDA vs 30-day average",
    severity: "Neutral",
    createdAt: "11 min ago"
  },
  {
    id: 3,
    message: "Positive earnings surprise for AAPL beating consensus EPS",
    severity: "Positive",
    createdAt: "28 min ago"
  },
  {
    id: 4,
    message: "Options market pricing elevated short-term volatility",
    severity: "Negative",
    createdAt: "43 min ago"
  }
];

export interface KeywordStat {
  keyword: string;
  frequency: number;
  sentiment: "Positive" | "Neutral" | "Negative";
}

export const keywordStats: KeywordStat[] = [
  { keyword: "inflation", frequency: 32, sentiment: "Negative" },
  { keyword: "earnings", frequency: 47, sentiment: "Positive" },
  { keyword: "AI", frequency: 65, sentiment: "Positive" },
  { keyword: "interest rates", frequency: 28, sentiment: "Negative" },
  { keyword: "product launch", frequency: 21, sentiment: "Positive" },
  { keyword: "guidance", frequency: 19, sentiment: "Neutral" },
  { keyword: "recession", frequency: 23, sentiment: "Negative" }
];

export interface SentimentBucket {
  label: string;
  value: number;
}

export const sentimentDistribution: SentimentBucket[] = [
  { label: "Positive", value: 56 },
  { label: "Neutral", value: 24 },
  { label: "Negative", value: 20 }
];

