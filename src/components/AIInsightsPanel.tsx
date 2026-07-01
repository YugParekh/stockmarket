import { useState } from "react";
import type { InsightsPayload } from "../api/dashboard";
import { askAIChat, fetchAIInsight } from "../api/aiInsights";

interface AIInsightsPanelProps {
  symbol: string;
  insights: InsightsPayload;
  loading?: boolean;
}

interface ChatTurn {
  question: string;
  answer: string;
}

export const AIInsightsPanel = ({
  symbol,
  insights,
  loading
}: AIInsightsPanelProps) => {
  const [deepAnalysis, setDeepAnalysis] = useState<string | null>(null);
  const [deepLoading, setDeepLoading] = useState(false);
  const [deepError, setDeepError] = useState<string | null>(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const [disclaimer, setDisclaimer] = useState<string | null>(null);

  const [question, setQuestion] = useState("");
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const handleGenerateAnalysis = async () => {
    setDeepLoading(true);
    setDeepError(null);
    try {
      const res = await fetchAIInsight(symbol);
      setDisclaimer(res.disclaimer);
      if (!res.configured) {
        setNotConfigured(true);
        setDeepAnalysis(null);
      } else {
        setNotConfigured(false);
        setDeepAnalysis(res.content ?? "No analysis returned — try again in a moment.");
      }
    } catch {
      setDeepError("Couldn't reach the AI insights service. Try again shortly.");
    } finally {
      setDeepLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    const trimmed = question.trim();
    if (!trimmed || chatLoading) return;
    setChatLoading(true);
    setChatError(null);
    try {
      const res = await askAIChat(symbol, trimmed);
      setDisclaimer(res.disclaimer);
      if (!res.configured) {
        setNotConfigured(true);
      } else {
        setChatTurns((prev) => [...prev, { question: trimmed, answer: res.answer ?? "No answer returned." }]);
        setQuestion("");
      }
    } catch {
      setChatError("Couldn't reach the AI chat service. Try again shortly.");
    } finally {
      setChatLoading(false);
    }
  };

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

      <div className="border-t border-slate-800/80 pt-3 flex flex-col gap-3">
        {!deepAnalysis && !notConfigured && (
          <button
            onClick={handleGenerateAnalysis}
            disabled={deepLoading}
            className="self-start px-3 py-1.5 rounded-lg border border-cyan-500/40 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-500/10 transition-colors disabled:opacity-50"
          >
            {deepLoading ? "Generating…" : "Get AI Deep Analysis"}
          </button>
        )}

        {notConfigured && (
          <p className="text-[11px] text-amber-300/90">
            AI deep-analysis isn't configured on this backend yet (no Gemini API key set). The
            rest of the dashboard works normally without it.
          </p>
        )}

        {deepError && <p className="text-[11px] text-red-300">{deepError}</p>}

        {deepAnalysis && (
          <div className="text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-900/60 rounded-lg p-3 border border-slate-800/80">
            {deepAnalysis}
          </div>
        )}

        {!notConfigured && (
          <div className="flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold text-slate-300">
              Ask about {symbol.toUpperCase()}
            </h3>

            {chatTurns.map((turn, idx) => (
              <div key={idx} className="flex flex-col gap-1 text-[11px]">
                <div className="text-cyan-300 font-medium">You: {turn.question}</div>
                <div className="text-slate-400 whitespace-pre-wrap">{turn.answer}</div>
              </div>
            ))}

            {chatError && <p className="text-[11px] text-red-300">{chatError}</p>}

            <div className="flex gap-2">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleAskQuestion();
                }}
                placeholder="e.g. What would change this view?"
                className="flex-1 rounded-lg bg-slate-900/80 border border-slate-700/80 px-2.5 py-1.5 text-[11px] text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/70"
              />
              <button
                onClick={handleAskQuestion}
                disabled={chatLoading || !question.trim()}
                className="px-3 py-1.5 rounded-lg border border-cyan-500/40 text-[11px] font-semibold text-cyan-300 hover:bg-cyan-500/10 transition-colors disabled:opacity-50"
              >
                {chatLoading ? "…" : "Ask"}
              </button>
            </div>
          </div>
        )}

        {disclaimer && (deepAnalysis || chatTurns.length > 0) && (
          <p className="text-[10px] text-slate-500 italic leading-relaxed">{disclaimer}</p>
        )}
      </div>
    </section>
  );
};

