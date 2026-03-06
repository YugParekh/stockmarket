import React from "react";
import type { NewsItem } from "../mockMarketData";

interface NewsCardProps {
  item: NewsItem;
}

const sentimentColorClasses: Record<"Positive" | "Neutral" | "Negative", string> = {
  Positive: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  Neutral: "bg-amber-500/10 text-amber-300 border-amber-500/20",
  Negative: "bg-rose-500/10 text-rose-400 border-rose-500/20",
};

const impactColorClasses: Record<"Low" | "Medium" | "High", string> = {
  Low: "text-slate-500",
  Medium: "text-sky-400",
  High: "text-amber-400",
};

export const NewsCard: React.FC<NewsCardProps> = ({ item }) => {
  return (
    <article className="group flex flex-col gap-2 p-3.5 rounded-xl border border-slate-800/50 bg-slate-900/40 hover:bg-slate-800/60 hover:border-slate-700/80 hover:translate-x-1 transition-all duration-300 cursor-pointer border-l-2 border-l-transparent hover:border-l-cyan-500/50 shadow-sm hover:shadow-md">
      <div className="flex justify-between items-start gap-4">
        <h3 className="text-xs font-medium text-slate-200 group-hover:text-white transition-colors leading-relaxed">
          {item.headline}
        </h3>
        <span
          className={`shrink-0 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
            sentimentColorClasses[item.sentiment]
          }`}
        >
          {item.sentiment}
        </span>
      </div>
      <div className="flex justify-between items-center mt-auto pt-2 border-t border-slate-800/50">
        <div className="flex items-center gap-2">
          <span className="h-1 w-1 rounded-full bg-slate-600" />
          <span className={`text-[10px] font-medium ${impactColorClasses[item.impact]}`}>
            {item.impact} Impact
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono tracking-tighter">
          {item.timestamp}
        </span>
      </div>
    </article>
  );
};
