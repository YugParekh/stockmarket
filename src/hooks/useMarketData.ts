import { useEffect, useState } from "react";
import { fetchDashboardData, type InsightsPayload, type UiRange } from "../api/dashboard";
import type {
  AlertItem,
  KeywordStat,
  MarketDataPoint,
  NewsItem,
  SentimentBucket
} from "../mockMarketData";
import {
  alerts as mockAlerts,
  keywordStats as mockKeywords,
  mockMarketData,
  newsFeed as mockNews,
  sentimentDistribution as mockDistribution
} from "../mockMarketData";

export const useMarketData = (symbol: string, range: UiRange) => {
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState<MarketDataPoint[]>(mockMarketData);
  const [news, setNews] = useState<NewsItem[]>(mockNews);
  const [alerts, setAlerts] = useState<AlertItem[]>(mockAlerts);
  const [keywords, setKeywords] = useState<KeywordStat[]>(mockKeywords);
  const [distribution, setDistribution] = useState<SentimentBucket[]>(mockDistribution);
  const [insights, setInsights] = useState<InsightsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load(firstLoad: boolean) {
      if (firstLoad) {
        setLoading(true);
      }
      try {
        const data = await fetchDashboardData(symbol, range);
        if (cancelled) return;
        setMarketData(data.marketData);
        setNews(data.news);
        setAlerts(data.alerts);
        setKeywords(data.keywords);
        setDistribution(data.sentimentDistribution);
        setInsights(data.insights);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        console.error("API Error - falling back to mocks", e);
        setError("Falling back to local mock dataset (backend unreachable).");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load(true);

    const interval = window.setInterval(() => {
      void load(false);
    }, 30_000); // Polling every 30s

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [symbol, range]);

  return {
    loading,
    marketData,
    news,
    alerts,
    keywords,
    distribution,
    insights,
    error,
    latest: marketData[marketData.length - 1]
  };
};
