import type { KeywordStat } from "../mockMarketData";

interface WordCloudProps {
  loading?: boolean;
  items: KeywordStat[];
}

const sentimentColor: Record<
  "Positive" | "Neutral" | "Negative",
  string
> = {
  Positive:
    "bg-emerald-500/10 text-emerald-300 border-emerald-400/60",
  Neutral:
    "bg-sky-500/10 text-sky-300 border-sky-400/60",
  Negative:
    "bg-red-500/10 text-red-300 border-red-400/60"
};

const getSizeClass = (frequency: number) => {
  if (frequency > 55) return "text-xl";
  if (frequency > 35) return "text-base";
  if (frequency > 20) return "text-sm";
  return "text-xs";
};

export const WordCloud = ({ loading, items }: WordCloudProps) => {
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
            Keyword Frequency
          </h2>
          <p className="text-[11px] text-slate-500">
            Most common terms in recent news flow
          </p>
        </div>
      </div>
      <div className="flex-1 flex flex-wrap gap-2 items-start overflow-y-auto">
        {items.map((kw) => (
          <span
            key={kw.keyword}
            className={`inline-flex items-center border rounded-full px-2.5 py-1 ${sentimentColor[kw.sentiment]} ${getSizeClass(
              kw.frequency
            )} hover:bg-cyan-500/15 hover:border-cyan-400/70 hover:text-cyan-200 transition-colors duration-150`}
          >
            {kw.keyword}
            <span className="ml-1 text-[10px] text-slate-400">
              {kw.frequency}
            </span>
          </span>
        ))}
      </div>
    </section>
  );
};

