import React, { useState } from "react";
import type { NewsItem } from "../mockMarketData";
import { NewsCard } from "./NewsCard";
import { analyzeSentiment } from "../api/ai";

interface NewsFeedProps {
  loading?: boolean;
  items: NewsItem[];
}

export const NewsFeed = ({ loading, items }: NewsFeedProps) => {
  const [aiSentimentMap, setAiSentimentMap] = useState<Record<number, string | null>>({});
  const [scanningId, setScanningId] = useState<number | null>(null);

  const handleScan = async (id: number, text: string) => {
    if (aiSentimentMap[id] || scanningId === id) return;
    setScanningId(id);
    const result = await analyzeSentiment(text);
    if (result) {
      const mapped = result === "Bullish" ? "Positive" : result === "Bearish" ? "Negative" : "Neutral";
      setAiSentimentMap(prev => ({ ...prev, [id]: mapped }));
    }
    setScanningId(null);
  };

  // Auto-scan top 3 headlines on load
  React.useEffect(() => {
    if (items.length > 0) {
      const top3 = items.slice(0, 3);
      top3.forEach((item, index) => {
        // Stagger slightly to avoid burst limits
        setTimeout(() => {
          handleScan(item.id, item.headline);
        }, index * 1000);
      });
    }
  }, [items.length]); // Only trigger when items are loaded

  if (loading) {
    return (
      <section className="glass-card-soft h-[400px] animate-pulse rounded-2xl" />
    );
  }

  return (
    <section className="glass-card-soft p-5 h-[400px] flex flex-col rounded-2xl border border-slate-800/50">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-widest">
            News Feed
          </h2>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Real-time intelligence & sentiment analysis
          </p>
        </div>
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-800/50 border border-slate-700/50 text-slate-400">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10l4 4v10a2 2 0 01-2 2z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 2v6h6" />
          </svg>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
        {items.map((item) => {
          const effectiveSentiment = aiSentimentMap[item.id] || item.sentiment;
          const isScanning = scanningId === item.id;
          const hasAI = !!aiSentimentMap[item.id];

          return (
            <div key={item.id} className="relative group/news">
              <NewsCard item={{ ...item, sentiment: effectiveSentiment as any }} />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleScan(item.id, item.headline);
                }}
                disabled={isScanning || hasAI}
                className={`absolute top-2 right-2 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase transition-all shadow-sm ${
                  hasAI 
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30" 
                    : "bg-slate-800/80 text-slate-500 border border-slate-700 group-hover/news:border-cyan-500/50 group-hover/news:text-cyan-400"
                } ${isScanning ? "animate-pulse" : ""}`}
              >
                {isScanning ? "Scanning..." : hasAI ? "AI Verified" : "AI Scan"}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
};

