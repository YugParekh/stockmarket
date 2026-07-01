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
import { fetchQuotes, type QuoteItem } from "../api/quotes";
import { formatCompactNumber } from "../utils/formatters";

// Maps the "glance" card's display symbol/name to the real ticker to quote —
// S&P 500 and Nasdaq are quoted via their most liquid tracking ETFs (SPY, QQQ)
// since Finnhub/yfinance quote individual securities, not raw index tickers.
const GLANCE_SYMBOLS: { quoteSymbol: string; displaySymbol: string; name: string }[] = [
  { quoteSymbol: "SPY", displaySymbol: "S&P 500", name: "Market Index (SPY)" },
  { quoteSymbol: "QQQ", displaySymbol: "NASDAQ", name: "Tech Index (QQQ)" },
  { quoteSymbol: "AAPL", displaySymbol: "AAPL", name: "Apple Inc." },
  { quoteSymbol: "NVDA", displaySymbol: "NVDA", name: "NVIDIA Corp." },
  { quoteSymbol: "MSFT", displaySymbol: "MSFT", name: "Microsoft" },
  { quoteSymbol: "GOOGL", displaySymbol: "GOOGL", name: "Alphabet Inc." },
  { quoteSymbol: "AMZN", displaySymbol: "AMZN", name: "Amazon.com" },
  { quoteSymbol: "TSLA", displaySymbol: "TSLA", name: "Tesla, Inc." }
];

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
  const [quotes, setQuotes] = useState<Record<string, QuoteItem>>({});
  const [quotesLoading, setQuotesLoading] = useState(true);
  const [quotesError, setQuotesError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadQuotes = async () => {
      try {
        const items = await fetchQuotes(GLANCE_SYMBOLS.map((g) => g.quoteSymbol));
        if (cancelled) return;
        const bySymbol: Record<string, QuoteItem> = {};
        for (const item of items) bySymbol[item.symbol] = item;
        setQuotes(bySymbol);
        setQuotesError(false);
      } catch {
        if (!cancelled) setQuotesError(true);
      } finally {
        if (!cancelled) setQuotesLoading(false);
      }
    };

    loadQuotes();
    // Quotes are a lightweight "glance" widget, not the main chart — refresh
    // far less often than the 20s main-data poll to stay conservative on the
    // free-tier Finnhub/yfinance call budget.
    const interval = window.setInterval(loadQuotes, 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const topStocks = GLANCE_SYMBOLS.map((g) => {
    const q = quotes[g.quoteSymbol];
    const isPositive = (q?.changePercent ?? 0) >= 0;
    return {
      symbol: g.displaySymbol,
      name: g.name,
      price: q?.price ?? 0,
      change: q?.change ?? 0,
      changePercent: q?.changePercent ?? 0,
      volume: q ? formatCompactNumber(q.volume) : "—",
      isPositive
    };
  });

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
          {quotesError && (
            <div className="glass-card-soft border border-amber-500/40 text-[11px] text-amber-200 px-3 py-2 mb-3">
              Couldn't reach the live quotes service — showing the last known values.
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {quotesLoading
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="glass-card-soft h-32 animate-pulse rounded-2xl" />
                ))
              : sortedStocks.map((stock) => (
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

