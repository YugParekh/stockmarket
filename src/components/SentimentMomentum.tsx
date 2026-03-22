import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { MarketDataPoint } from "../mockMarketData";

interface SentimentMomentumProps {
  loading?: boolean;
  data: MarketDataPoint[];
}

export const SentimentMomentum = ({ loading, data }: SentimentMomentumProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-60 animate-pulse" />
    );
  }

  return (
    <section className="glass-card-soft p-4 lg:p-5 h-60 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Sentiment Momentum Indicator
          </h2>
          <p className="text-[11px] text-slate-500">
            Gradient view of sentiment trend over time
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-slate-400">
          TODO: Integrate LLM-generated market insights
        </span>
      </div>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" stopOpacity={0.7} />
                <stop offset="50%" stopColor="#22c55e" stopOpacity={0.15} />
                <stop offset="50%" stopColor="#ef4444" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.7} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#111827" opacity={0.9} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              tickMargin={8}
            />
            <YAxis
              domain={[-1, 1]}
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              tickMargin={4}
              axisLine={{ stroke: "#374151" }}
              tickLine={{ stroke: "#374151" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                border: "1px solid rgba(148,163,184,0.4)",
                borderRadius: 10
              }}
              labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
            />
            <Area
              type="monotone"
              dataKey="sentiment_score"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#sentimentGradient)"
              isAnimationActive
              animationDuration={900}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

