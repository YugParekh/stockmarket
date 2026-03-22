import type { NewsItem } from "../mockMarketData";

interface NewsFeedProps {
  loading?: boolean;
  items: NewsItem[];
}

const sentimentColorClasses: Record<
  "Positive" | "Neutral" | "Negative",
  string
> = {
  Positive:
    "bg-emerald-500/10 text-emerald-300 border-emerald-400/40 shadow-neon-green",
  Neutral:
    "bg-amber-500/10 text-amber-200 border-amber-400/40 shadow-neon-orange",
  Negative:
    "bg-red-500/10 text-red-300 border-red-400/40 shadow-neon-red"
};

const impactColorClasses: Record<"Low" | "Medium" | "High", string> = {
  Low: "text-slate-400",
  Medium: "text-sky-300",
  High: "text-orange-300"
};

export const NewsFeed = ({ loading, items }: NewsFeedProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-72 animate-pulse" />
    );
  }

  return (
    <section className="glass-card-soft p-4 h-72 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Market News Intelligence
          </h2>
          <p className="text-[11px] text-slate-500">
            AI-curated headlines and sentiment tags
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-cyan-300">
          TODO: Connect sentiment analysis API
        </span>
      </div>
      <div className="mt-2 space-y-2 overflow-y-auto pr-1">
        {items.map((item) => (
          <article
            key={item.id}
            className="rounded-lg border border-slate-700/80 bg-slate-900/60 hover:border-cyan-400/60 hover:shadow-neon-cyan transition-all duration-200 px-3 py-2.5"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-xs sm:text-sm text-slate-100">
                {item.headline}
              </h3>
              <span
                className={`inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${sentimentColorClasses[item.sentiment]}`}
              >
                {item.sentiment}
              </span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px]">
              <span className={impactColorClasses[item.impact]}>
                Impact: {item.impact}
              </span>
              <span className="text-slate-500">{item.timestamp}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};

