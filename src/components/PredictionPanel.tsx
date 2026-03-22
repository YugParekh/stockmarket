import type { MarketDataPoint } from "../mockMarketData";

interface PredictionPanelProps {
  loading?: boolean;
  data: MarketDataPoint[];
}

export const PredictionPanel = ({ loading, data }: PredictionPanelProps) => {
  const latest = data[data.length - 1];

  if (!latest) {
    return null;
  }

  if (loading) {
    return (
      <section className="glass-card-soft h-40 animate-pulse" />
    );
  }

  const isUp = latest.prediction === "UP";
  const barWidth = `${latest.confidence}%`;

  return (
    <section className="glass-card-soft p-4 h-40 flex flex-col justify-between">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            AI Prediction Panel
          </h2>
          <p className="text-[11px] text-slate-500">
            Next session directional view and confidence
          </p>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
            isUp
              ? "border-emerald-400/60 text-emerald-300"
              : "border-red-400/60 text-red-300"
          }`}
        >
          {isUp ? "Bullish bias" : "Bearish bias"}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div
          className={`flex items-center justify-center rounded-lg h-16 w-20 text-lg font-semibold ${
            isUp
              ? "bg-emerald-500/15 text-emerald-300 border border-emerald-400/60 shadow-neon-green"
              : "bg-red-500/15 text-red-300 border border-red-400/60 shadow-neon-red"
          }`}
        >
          {isUp ? "UP" : "DOWN"}
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="text-slate-300">Confidence</span>
            <span className="text-sky-300 font-semibold">
              {latest.confidence}%
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
            <div
              className={`h-full rounded-full bg-gradient-to-r ${
                isUp
                  ? "from-emerald-400 via-cyan-400 to-sky-500"
                  : "from-red-400 via-orange-400 to-amber-300"
              } transition-all duration-700`}
              style={{ width: barWidth }}
            />
          </div>
          <p className="mt-1.5 text-[11px] text-slate-500">
            Confidence level inferred from combined price, volume, and news
            sentiment signals.
          </p>
        </div>
      </div>
    </section>
  );
};

