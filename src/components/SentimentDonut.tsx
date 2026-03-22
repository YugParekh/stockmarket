import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { SentimentBucket } from "../mockMarketData";

interface SentimentDonutProps {
  loading?: boolean;
  data: SentimentBucket[];
}

const COLORS = ["#22c55e", "#eab308", "#f97373"];

export const SentimentDonut = ({ loading, data }: SentimentDonutProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-60 animate-pulse" />
    );
  }

  return (
    <section className="glass-card-soft p-4 h-60 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Sentiment Distribution
          </h2>
          <p className="text-[11px] text-slate-500">
            Share of positive, neutral, and negative signals
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-slate-400">
          Last 30 sessions
        </span>
      </div>
      <div className="flex-1 flex items-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                border: "1px solid rgba(148,163,184,0.4)",
                borderRadius: 10
              }}
              labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
            />
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius="55%"
              outerRadius="80%"
              paddingAngle={4}
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.label}
                  fill={COLORS[index % COLORS.length]}
                  stroke="#020617"
                  strokeWidth={1}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

