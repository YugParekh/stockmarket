import { useEffect, useRef, useState } from "react";
import type { MarketDataPoint } from "../mockMarketData";

interface KPICardsProps {
  loading?: boolean;
  data: MarketDataPoint[];
}

type Trend = "positive" | "neutral" | "negative";

const useAnimatedNumber = (value: number, duration = 1000) => {
  const [display, setDisplay] = useState(0);
  const startRef = useRef<number | null>(null);
  const fromRef = useRef(0);
  const toRef = useRef(value);

  useEffect(() => {
    fromRef.current = display;
    toRef.current = value;
    startRef.current = null;

    let frameId: number;

    const step = (timestamp: number) => {
      if (startRef.current === null) {
        startRef.current = timestamp;
      }
      const progress = Math.min((timestamp - startRef.current) / duration, 1);
      const next =
        fromRef.current + (toRef.current - fromRef.current) * progress;
      setDisplay(next);
      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      }
    };

    frameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameId);
  }, [value, duration]);

  return display;
};

const getTrend = (value: number): Trend => {
  if (value > 0.15) return "positive";
  if (value < -0.15) return "negative";
  return "neutral";
};

const trendClasses: Record<Trend, string> = {
  positive: "text-emerald-400",
  neutral: "text-amber-300",
  negative: "text-red-400"
};

const trendBadgeClasses: Record<Trend, string> = {
  positive: "bg-emerald-500/10 text-emerald-300 border-emerald-500/40",
  neutral: "bg-amber-500/10 text-amber-200 border-amber-500/40",
  negative: "bg-red-500/10 text-red-300 border-red-500/40"
};

export const KPICards = ({ loading, data }: KPICardsProps) => {
  const latest = data[data.length - 1];
  const prev = data[data.length - 2] ?? latest;

  if (!latest) {
    return null;
  }

  const priceChange = latest.price - prev.price;
  const priceTrend: Trend =
    priceChange > 0.3 ? "positive" : priceChange < -0.3 ? "negative" : "neutral";

  const sentimentTrend = getTrend(latest.sentiment_score);
  const sentimentScore = Math.round((latest.sentiment_score + 1) * 50);

  const predictionTrend: Trend =
    latest.prediction === "UP"
      ? latest.confidence > 65
        ? "positive"
        : "neutral"
      : latest.confidence > 65
      ? "negative"
      : "neutral";

  const fearIndexRaw = 100 - sentimentScore;
  const fearTrend: Trend =
    fearIndexRaw > 65 ? "negative" : fearIndexRaw < 35 ? "positive" : "neutral";

  const animatedPrice = useAnimatedNumber(latest.price);
  const animatedSentiment = useAnimatedNumber(sentimentScore);
  const animatedConfidence = useAnimatedNumber(latest.confidence);
  const animatedFear = useAnimatedNumber(fearIndexRaw);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div
            key={idx}
            className="glass-card kpi-glow animate-pulse h-28 flex flex-col justify-center px-5"
          >
            <div className="h-3 w-24 bg-slate-700/70 rounded mb-3" />
            <div className="h-6 w-32 bg-slate-700/80 rounded mb-2" />
            <div className="h-3 w-20 bg-slate-800/80 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      <KpiCard
        label="Current Stock Price"
        value={`$${animatedPrice.toFixed(2)}`}
        hint={`${priceChange >= 0 ? "+" : ""}${priceChange.toFixed(2)} today`}
        trend={priceTrend}
      />
      <KpiCard
        label="Sentiment Score"
        value={`${animatedSentiment.toFixed(0)} / 100`}
        hint={sentimentTrend === "positive" ? "Bullish" : sentimentTrend === "negative" ? "Bearish" : "Neutral"}
        trend={sentimentTrend}
      />
      <KpiCard
        label="Prediction Confidence"
        value={`${animatedConfidence.toFixed(0)} %`}
        hint={latest.prediction === "UP" ? "AI expects upside" : "AI expects downside"}
        trend={predictionTrend}
      />
      <KpiCard
        label="Market Fear Index"
        value={`${animatedFear.toFixed(0)} / 100`}
        hint={
          fearTrend === "positive"
            ? "Low systemic risk"
            : fearTrend === "negative"
            ? "Elevated risk-off"
            : "Balanced risk appetite"
        }
        trend={fearTrend}
      />
    </section>
  );
};

interface KpiCardProps {
  label: string;
  value: string;
  hint: string;
  trend: Trend;
}

const KpiCard = ({ label, value, hint, trend }: KpiCardProps) => {
  return (
    <div className="glass-card kpi-glow p-4 flex flex-col justify-between hover:translate-y-0.5 hover:shadow-neon-cyan transition-all duration-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
          {label}
        </span>
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${trendBadgeClasses[trend]}`}
        >
          {trend === "positive"
            ? "Positive"
            : trend === "negative"
            ? "Negative"
            : "Neutral"}
        </span>
      </div>
      <div className={`text-xl sm:text-2xl font-semibold ${trendClasses[trend]} mb-1`}>
        {value}
      </div>
      <div className="text-[11px] text-slate-400">{hint}</div>
    </div>
  );
};

