import React from "react";

export type SentimentType = "Positive" | "Neutral" | "Negative";

interface SentimentBadgeProps {
  sentiment: SentimentType;
  showIcon?: boolean;
}

const config: Record<SentimentType, { label: string; bg: string; text: string; border: string; icon: string }> = {
  Positive: {
    label: "Bullish",
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
    icon: "↗",
  },
  Neutral: {
    label: "Neutral",
    bg: "bg-slate-500/10",
    text: "text-slate-400",
    border: "border-slate-500/20",
    icon: "→",
  },
  Negative: {
    label: "Bearish",
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/20",
    icon: "↘",
  },
};

export const SentimentBadge: React.FC<SentimentBadgeProps> = ({ sentiment, showIcon = true }) => {
  const { label, bg, text, border, icon } = config[sentiment];

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border ${bg} ${text} ${border} text-[10px] font-bold uppercase tracking-wider`}
    >
      {showIcon && <span className="text-[12px] leading-none">{icon}</span>}
      <span>{label}</span>
    </div>
  );
};
