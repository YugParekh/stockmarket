import { useEffect, useMemo, useRef, useState } from "react";
import { searchSymbols, type SymbolSearchItem } from "../api/search";

const tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"];
const ranges = ["1D", "5D", "1M", "3M", "6M", "1Y"];

interface TopbarProps {
  symbol: string;
  range: string;
  onSymbolChange: (symbol: string) => void;
  onRangeChange: (range: any) => void;
}

export const Topbar = ({
  symbol,
  range,
  onSymbolChange,
  onRangeChange
}: TopbarProps) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SymbolSearchItem[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const lastRequestId = useRef(0);

  const trimmedQuery = useMemo(() => query.trim(), [query]);

  useEffect(() => {
    if (!trimmedQuery || trimmedQuery.length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }

    const requestId = ++lastRequestId.current;
    setLoading(true);

    const t = window.setTimeout(async () => {
      try {
        const res = await searchSymbols(trimmedQuery);
        if (requestId !== lastRequestId.current) return;
        setResults(res);
        setActiveIndex(0);
        setOpen(true);
      } catch {
        if (requestId !== lastRequestId.current) return;
        setResults([]);
        setOpen(false);
      } finally {
        if (requestId === lastRequestId.current) setLoading(false);
      }
    }, 250);

    return () => window.clearTimeout(t);
  }, [trimmedQuery]);

  const choose = (item: SymbolSearchItem) => {
    onSymbolChange(item.symbol.toUpperCase());
    setQuery("");
    setOpen(false);
  };

  return (
    <header className="h-16 flex items-center px-4 sm:px-6 lg:px-8 border-b border-slate-800/80 bg-black/60 backdrop-blur-lg sticky top-0 z-20">
      <div className="flex-1 flex items-center gap-3">
        <div className="relative hidden sm:block w-56 lg:w-72">
          <input
            className="w-full rounded-lg bg-slate-900/80 border border-slate-700/80 px-3 py-2 text-xs sm:text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/70 focus:border-cyan-500/70 transition-colors"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search company (e.g. Apple) or symbol (AAPL)…"
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setOpen(false);
              }
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActiveIndex((i) => Math.min(i + 1, Math.max(0, results.length - 1)));
              }
              if (e.key === "ArrowUp") {
                e.preventDefault();
                setActiveIndex((i) => Math.max(i - 1, 0));
              }
              if (e.key === "Enter") {
                const value = (e.target as HTMLInputElement).value.trim();
                if (open && results[activeIndex]) {
                  choose(results[activeIndex]);
                  return;
                }
                if (value) {
                  onSymbolChange(value.toUpperCase());
                  setQuery("");
                  setOpen(false);
                }
              }
            }}
          />
          <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-500 text-xs">
            {loading ? "…" : "⌘K"}
          </span>

          {open && results.length > 0 && (
            <div className="absolute mt-2 w-full rounded-xl border border-cyan-500/20 bg-black/90 backdrop-blur-xl shadow-neon-cyan overflow-hidden z-30">
              <div className="max-h-72 overflow-y-auto">
                {results.map((r, idx) => {
                  const active = idx === activeIndex;
                  return (
                    <button
                      key={`${r.symbol}-${idx}`}
                      onMouseEnter={() => setActiveIndex(idx)}
                      onClick={() => choose(r)}
                      className={`w-full text-left px-3 py-2 transition-colors ${
                        active
                          ? "bg-cyan-500/15"
                          : "hover:bg-cyan-500/10"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-xs text-slate-100 truncate">
                            {r.description}
                          </div>
                          <div className="text-[10px] text-slate-500 truncate">
                            {r.type ?? "—"}
                          </div>
                        </div>
                        <div className="text-[11px] font-mono text-cyan-300">
                          {r.symbol}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="px-3 py-2 text-[10px] text-slate-500 border-t border-slate-800/80">
                Tip: type a company name and press Enter.
              </div>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <select
            value={symbol}
            onChange={(e) => onSymbolChange(e.target.value)}
            className="bg-slate-900/80 border border-slate-700/80 text-xs sm:text-sm rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500/70"
          >
            {tickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={range}
            onChange={(e) => onRangeChange(e.target.value)}
            className="bg-slate-900/80 border border-slate-700/80 text-xs sm:text-sm rounded-lg px-2.5 py-1.5 text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500/70"
          >
            {ranges.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs sm:text-sm text-slate-400">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-400" />
          </span>
          <span className="font-medium text-emerald-300">Live Market</span>
        </div>
        <button className="h-8 w-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-600/80 flex items-center justify-center text-xs font-semibold text-sky-300 shadow-md shadow-sky-500/30">
          YG
        </button>
      </div>
    </header>
  );
};

