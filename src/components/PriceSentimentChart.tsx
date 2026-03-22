import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { MarketDataPoint } from "../mockMarketData";

interface PriceSentimentChartProps {
  loading?: boolean;
  data: MarketDataPoint[];
}

export const PriceSentimentChart = ({
  loading,
  data
}: PriceSentimentChartProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-72 lg:h-80 w-full animate-pulse" />
    );
  }

  return (
    <section className="glass-card-soft p-4 lg:p-5 h-72 lg:h-80 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            Stock Price vs News Sentiment
          </h2>
          <p className="text-[11px] text-slate-500">
            Dual-axis view of price action and AI news sentiment
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-emerald-300 border border-emerald-400/40 rounded-full px-2 py-0.5">
          Live feed via market API
        </span>
      </div>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <defs>
              <filter id="shadow-cyan" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow
                  dx="0"
                  dy="0"
                  stdDeviation="3"
                  floodColor="#22d3ee"
                  floodOpacity="0.5"
                />
              </filter>
              <filter id="shadow-orange" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow
                  dx="0"
                  dy="0"
                  stdDeviation="3"
                  floodColor="#fb923c"
                  floodOpacity="0.5"
                />
              </filter>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" opacity={0.7} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              tickMargin={8}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              tickMargin={4}
              axisLine={{ stroke: "#374151" }}
              tickLine={{ stroke: "#374151" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 10, fill: "#9ca3af" }}
              tickMargin={4}
              axisLine={{ stroke: "#374151" }}
              tickLine={{ stroke: "#374151" }}
              domain={[-1, 1]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#020617",
                border: "1px solid rgba(34,211,238,0.35)",
                borderRadius: 10,
                boxShadow: "0 0 25px rgba(34,211,238,0.35)"
              }}
              labelStyle={{ color: "#e5e7eb", fontSize: 11 }}
            />
            <Legend
              wrapperStyle={{ fontSize: 10, paddingTop: 6 }}
              iconSize={10}
              iconType="circle"
            />
            <Line
              type="monotone"
              yAxisId="left"
              dataKey="price"
              name="Price"
              stroke="#22d3ee"
              strokeWidth={2.5}
              dot={false}
              activeDot={{
                r: 4,
                strokeWidth: 0,
                fill: "#22d3ee",
                stroke: "#0891b2"
              }}
              isAnimationActive
              animationDuration={900}
              style={{ filter: "url(#shadow-cyan)" }}
            />
            <Line
              type="monotone"
              yAxisId="right"
              dataKey="sentiment_score"
              name="Sentiment score"
              stroke="#fb923c"
              strokeWidth={2}
              strokeDasharray="4 3"
              dot={false}
              activeDot={{
                r: 4,
                strokeWidth: 0,
                fill: "#fb923c",
                stroke: "#c2410c"
              }}
              isAnimationActive
              animationDuration={900}
              animationBegin={150}
              style={{ filter: "url(#shadow-orange)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

