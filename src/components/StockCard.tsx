import React from "react";
import { formatCurrency, formatPercentage } from "../utils/formatters";

interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  isPositive: boolean;
}

export const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  changePercent,
  volume,
  isPositive,
}) => {
  return (
    <div className="glass-card p-4 flex flex-col gap-3 hover:border-slate-700 transition-all duration-300 group cursor-pointer">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-bold text-slate-100 group-hover:text-sky-400 transition-colors">
            {symbol}
          </h3>
          <p className="text-xs text-slate-500">{name}</p>
        </div>
        <div
          className={`px-2 py-0.5 rounded text-[10px] font-medium ${
            isPositive
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
          }`}
        >
          {isPositive ? "▲" : "▼"} {Math.abs(changePercent).toFixed(2)}%
        </div>
      </div>

      <div className="mt-1">
        <div className="text-2xl font-mono font-medium text-slate-100">
          {formatCurrency(price)}
        </div>
        <div
          className={`text-xs mt-0.5 ${
            isPositive ? "text-emerald-500" : "text-rose-500"
          }`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)} Today
        </div>
      </div>

      <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-800/50">
        <div className="text-[10px] text-slate-500">
          Vol: <span className="text-slate-400 font-mono">{volume}</span>
        </div>
        <div className="h-6 w-16 opacity-50 group-hover:opacity-100 transition-opacity">
          {/* Sparkline placeholder for now */}
          <div className="flex items-end gap-0.5 h-full">
            {[40, 60, 45, 70, 55, 80, 65].map((h, i) => (
              <div
                key={i}
                className={`w-1 rounded-t-sm ${
                  isPositive ? "bg-emerald-500/40" : "bg-rose-500/40"
                }`}
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
