import { useEffect, useState } from "react";
import { KPICards } from "../components/KPICards";
import { PriceSentimentChart } from "../components/PriceSentimentChart";
import { SentimentDonut } from "../components/SentimentDonut";
import { NewsFeed } from "../components/NewsFeed";
import { SentimentMomentum } from "../components/SentimentMomentum";
import { PredictionPanel } from "../components/PredictionPanel";
import { AlertsPanel } from "../components/AlertsPanel";
import { WordCloud } from "../components/WordCloud";
import { AIInsightsPanel } from "../components/AIInsightsPanel";
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

interface DashboardProps {
  symbol: string;
  range: UiRange;
}

export const Dashboard = ({ symbol, range, view = "Dashboard" }: DashboardProps & { view?: string }) => {
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState<MarketDataPoint[]>(mockMarketData);
  const [news, setNews] = useState<NewsItem[]>(mockNews);
  const [alerts, setAlerts] = useState<AlertItem[]>(mockAlerts);
  const [keywords, setKeywords] = useState<KeywordStat[]>(mockKeywords);
  const [distribution, setDistribution] =
    useState<SentimentBucket[]>(mockDistribution);
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
        console.error(e);
        setError("Falling back to local mock dataset (backend unreachable).");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    // initial load
    void load(true);

    // lightweight polling to keep graphs reasonably fresh
    const interval = window.setInterval(() => {
      void load(false);
    }, 20_000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [symbol, range]);

  const latest = marketData[marketData.length - 1];

  const showAll = view === "Dashboard";
  const showOverview = view === "Market Overview";
  const showSentiment = view === "Sentiment Analysis";
  const showNews = view === "News Intelligence";
  const showPredictions = view === "Predictions";
  const showAlertsOnly = view === "Alerts";
  const showSettings = view === "Settings";

  return (
    <div className="space-y-5 lg:space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-slate-100">
            AI Stock Market Sentiment
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Multi-layer view of price action, news intelligence, and AI-driven
            sentiment analytics.
          </p>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          {latest && (
            <span className="text-sky-300">
              {symbol.toUpperCase()} • Last tick {latest.date}
            </span>
          )}
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Python models online</span>
        </div>
      </header>

      {error && (
        <div className="glass-card-soft border border-amber-500/40 text-[11px] text-amber-200 px-3 py-2">
          {error}
        </div>
      )}

      {insights && (
        <AIInsightsPanel symbol={symbol} insights={insights} loading={loading} />
      )}

      {(showAll || showOverview || showSentiment || showPredictions) && (
        <KPICards loading={loading} data={marketData} />
      )}

      {(showAll || showOverview || showSentiment || showNews) && (
        <section className="grid lg:grid-cols-3 gap-4 lg:gap-5">
          <div className="lg:col-span-2 space-y-4">
            {(showAll || showOverview) && (
              <PriceSentimentChart loading={loading} data={marketData} />
            )}
            {(showAll || showSentiment) && (
              <SentimentMomentum loading={loading} data={marketData} />
            )}
          </div>
          <div className="space-y-4">
            {(showAll || showOverview || showSentiment) && (
              <SentimentDonut loading={loading} data={distribution} />
            )}
            {(showAll || showNews) && (
              <NewsFeed loading={loading} items={news} />
            )}
          </div>
        </section>
      )}

      {(showAll ||
        showPredictions ||
        showAlertsOnly ||
        showSentiment ||
        showNews) && (
        <section className="grid lg:grid-cols-3 gap-4 lg:gap-5">
          {(showAll || showPredictions) && (
            <PredictionPanel loading={loading} data={marketData} />
          )}
          {(showAll || showAlertsOnly || showNews) && (
            <AlertsPanel loading={loading} items={alerts} />
          )}
          {(showAll || showSentiment) && (
            <WordCloud loading={loading} items={keywords} />
          )}
        </section>
      )}

      {showSettings && (
        <section className="glass-card-soft p-4 mt-2 text-[11px] text-slate-400 space-y-2">
          <h2 className="text-sm font-semibold text-slate-100">
            Settings & Diagnostics
          </h2>
          <p>
            The dashboard currently refreshes data every{" "}
            <span className="text-cyan-300 font-mono">20s</span> for the active
            symbol and date range using your backend APIs.
          </p>
          <p>
            To adjust polling, open{" "}
            <span className="text-cyan-300 font-mono">
              src/pages/Dashboard.tsx
            </span>{" "}
            and change the interval used in{" "}
            <span className="text-cyan-300 font-mono">
              window.setInterval(...)
            </span>
            .
          </p>
        </section>
      )}
    </div>
  );
};

