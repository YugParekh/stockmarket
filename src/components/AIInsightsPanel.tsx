import type { InsightsPayload } from "../api/dashboard";

interface AIInsightsPanelProps {
  symbol: string;
  insights: InsightsPayload;
  loading?: boolean;
}

export const AIInsightsPanel = ({
  symbol,
  insights,
  loading
}: AIInsightsPanelProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-32 animate-pulse mb-1" />
    );
  }

  const { nextMove, risk, commentary } = insights;
  const isUp = nextMove.direction === "UP";

  return (
    <section className="glass-card-soft p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            AI Insights & Forward View
          </h2>
          <p className="text-[11px] text-slate-500">
            Short-horizon directional bias and risk snapshot for{" "}
            <span className="text-cyan-300 font-mono">{symbol.toUpperCase()}</span>.
          </p>
        </div>
        <div
          className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase tracking-wide ${
            isUp
              ? "border-emerald-400/60 text-emerald-300"
              : "border-red-400/60 text-red-300"
          }`}
        >
          {isUp ? "Upside bias" : "Downside bias"}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-[11px]">
        <div className="space-y-1">
          <div className="text-slate-400">Expected move</div>
          <div className="text-sm font-semibold text-sky-300">
            {nextMove.expectedReturnPct >= 0 ? "+" : ""}
            {nextMove.expectedReturnPct.toFixed(2)}%
          </div>
          <div className="text-slate-500">{nextMove.horizon}</div>
        </div>
        <div className="space-y-1">
          <div className="text-slate-400">Confidence</div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-cyan-300">
              {nextMove.confidence}%
            </span>
            <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-sky-400 to-emerald-400"
                style={{ width: `${nextMove.confidence}%` }}
              />
            </div>
          </div>
        </div>
        <div className="space-y-1">
          <div className="text-slate-400">Risk</div>
          <div className="text-sm font-semibold text-amber-300">
            {risk.level} • ±{risk.valueAtRiskPct.toFixed(2)}%
          </div>
          <div className="text-slate-500">One-day VaR band</div>
        </div>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
        {commentary}
      </p>
    </section>
  );
};

