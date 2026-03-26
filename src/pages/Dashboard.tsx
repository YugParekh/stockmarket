import { useEffect, useState } from "react";
import { KPICards } from "../components/KPICards";
import { PriceSentimentChart } from "../components/PriceSentimentChart";
import { SentimentDonut } from "../components/SentimentDonut";
import { NewsFeed } from "../components/NewsFeed";
import { SentimentMomentum } from "../components/SentimentMomentum";
import { PredictionPanel } from "../components/PredictionPanel";
import { AlertsPanel } from "../components/AlertsPanel";
import { WordCloud } from "../components/WordCloud";
import { useMarketData } from "../hooks/useMarketData";
import { AIInsightsPanel } from "../components/AIInsightsPanel";
import { type UiRange } from "../api/dashboard";
import { StockCard } from "../components/StockCard";
import { exportToCSV } from "../utils/exportCSV";

interface DashboardProps {
  symbol: string;
  range: UiRange;
}

export const Dashboard = ({ symbol, range, view = "Dashboard" }: DashboardProps & { view?: string }) => {
  const {
    loading,
    marketData,
    news,
    alerts,
    keywords,
    distribution,
    insights,
    error,
    latest
  } = useMarketData(symbol, range);

  const [sortBy, setSortBy] = useState<"name" | "price" | "change">("name");

  const topStocks = [
    { symbol: "S&P 500", name: "Market Index", price: 5123.42, change: 12.5, changePercent: 0.24, volume: "4.1B", isPositive: true },
    { symbol: "NASDAQ", name: "Tech Index", price: 16384.15, change: -84.2, changePercent: -0.51, volume: "2.8B", isPositive: false },
    { symbol: "AAPL", name: "Apple Inc.", price: 192.25, change: 2.15, changePercent: 1.13, volume: "52M", isPositive: true },
    { symbol: "NVDA", name: "NVIDIA Corp.", price: 875.32, change: 15.42, changePercent: 1.79, volume: "84M", isPositive: true },
    { symbol: "MSFT", name: "Microsoft", price: 415.65, change: 3.21, changePercent: 0.78, volume: "22M", isPositive: true },
    { symbol: "GOOGL", name: "Alphabet Inc.", price: 154.85, change: -1.45, changePercent: -0.93, volume: "18M", isPositive: false },
    { symbol: "AMZN", name: "Amazon.com", price: 178.22, change: 0.95, changePercent: 0.54, volume: "31M", isPositive: true },
    { symbol: "TSLA", name: "Tesla, Inc.", price: 175.45, change: -5.32, changePercent: -2.94, volume: "105M", isPositive: false },
  ];

  const sortedStocks = [...topStocks].sort((a, b) => {
    if (sortBy === "price") return b.price - a.price;
    if (sortBy === "change") return b.changePercent - a.changePercent;
    return a.name.localeCompare(b.name);
  }).slice(0, 4);

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
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-semibold text-slate-100">
              AI Stock Market Sentiment
            </h1>
            <div className="group relative">
              <button className="h-5 w-5 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 hover:text-sky-300 hover:bg-slate-700 transition-all text-xs border border-slate-700">
                ?
              </button>
              <div className="absolute left-0 top-full mt-2 w-64 p-3 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-300 z-50 text-[11px] leading-relaxed text-slate-400">
                <p className="font-semibold text-sky-400 mb-1">How it works</p>
                Our AI engine analyzes real-time price action, news sentiment from 50+ sources, and social momentum to provide a multi-layered market perspective.
              </div>
            </div>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Multi-layer view of price action, news intelligence, and AI-driven
            sentiment analytics.
          </p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            {latest && (
              <span className="text-sky-300">
                {symbol.toUpperCase()} • Last tick {latest.date}
              </span>
            )}
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Python models online</span>
          </div>
          <button
            onClick={() => exportToCSV(symbol, marketData, news)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/50 text-[10px] font-semibold text-slate-300 hover:text-cyan-400 hover:border-cyan-500/50 hover:bg-slate-700/80 transition-all shadow-lg active:scale-95"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download Dataset (.csv)
          </button>
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

      {(showAll || showOverview) && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
              Market At A Glance
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-slate-500 uppercase">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-transparent text-[10px] text-sky-400 font-medium uppercase focus:outline-none cursor-pointer"
              >
                <option value="name">Name</option>
                <option value="price">Price</option>
                <option value="change">Change</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {sortedStocks.map((stock) => (
              <StockCard key={stock.symbol} {...stock} />
            ))}
          </div>
        </section>
      )}

      {(showAll || showOverview || showSentiment || showPredictions) && (
        <KPICards loading={loading} data={marketData} />
      )}

      {(showAll || showOverview || showSentiment || showNews) && (
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          <div className="md:col-span-2 space-y-4 lg:space-y-6">
            {(showAll || showOverview) && (
              <PriceSentimentChart loading={loading} data={marketData} />
            )}
            {(showAll || showSentiment) && (
              <SentimentMomentum loading={loading} data={marketData} />
            )}
          </div>
          <div className="space-y-4 lg:space-y-6">
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
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {(showAll || showPredictions) && (
            <div className="sm:col-span-2 lg:col-span-1">
              <PredictionPanel loading={loading} data={marketData} />
            </div>
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

