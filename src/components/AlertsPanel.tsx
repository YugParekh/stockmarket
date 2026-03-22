import type { AlertItem } from "../mockMarketData";

interface AlertsPanelProps {
  loading?: boolean;
  items: AlertItem[];
}

const severityBadgeClasses: Record<
  "Positive" | "Neutral" | "Negative",
  string
> = {
  Positive:
    "bg-emerald-500/10 text-emerald-300 border-emerald-400/50",
  Neutral:
    "bg-sky-500/10 text-sky-300 border-sky-400/50",
  Negative:
    "bg-red-500/10 text-red-300 border-red-400/50"
};

export const AlertsPanel = ({ loading, items }: AlertsPanelProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-48 animate-pulse" />
    );
  }

  return (
    <section className="glass-card-soft p-4 h-48 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Market Alerts
          </h2>
          <p className="text-[11px] text-slate-500">
            Real-time flags on unusual sentiment and flow
          </p>
        </div>
      </div>
      <div className="mt-1 space-y-2 overflow-y-auto pr-1">
        {items.map((alert) => (
          <div
            key={alert.id}
            className="alert-glow rounded-lg border border-slate-700/80 bg-slate-900/70 hover:border-cyan-400/70 hover:shadow-neon-cyan transition-all duration-200 px-3 py-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-orange-400 animate-pulse" />
                <p className="text-xs sm:text-[13px] text-slate-100">
                  {alert.message}
                </p>
              </div>
              <span
                className={`inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${severityBadgeClasses[alert.severity]}`}
              >
                {alert.severity}
              </span>
            </div>
            <div className="mt-0.5 text-[11px] text-slate-500">
              {alert.createdAt}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

