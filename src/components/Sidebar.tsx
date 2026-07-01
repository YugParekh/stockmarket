const menuItems = [
  "Dashboard",
  "Market Overview",
  "Sentiment Analysis",
  "News Intelligence",
  "Predictions",
  "Alerts",
  "Settings"
];

interface SidebarProps {
  active: string;
  onSelect: (section: string) => void;
}

export const Sidebar = ({ active, onSelect }: SidebarProps) => {
  return (
    <aside className="hidden md:flex md:flex-col w-64 bg-black/90 border-r border-cyan-500/20 shadow-neon-cyan">
      <div className="h-16 flex items-center px-6 border-b border-cyan-500/20">
        <div className="flex flex-col">
          <span className="text-sm tracking-[0.25em] text-cyan-400 uppercase">
            Market
          </span>
          <span className="text-lg font-semibold bg-gradient-to-r from-cyan-400 via-emerald-400 to-sky-500 bg-clip-text text-transparent">
            Sentinel AI
          </span>
        </div>
      </div>
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const isActive = active === item;
          return (
            <button
              key={item}
              onClick={() => onSelect(item)}
              className={`group flex items-center w-full px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-300 ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500/20 to-transparent text-cyan-300 border-l-2 border-l-cyan-400 shadow-[4px_0_24px_-12px_rgba(34,211,238,0.3)]"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40"
              } relative overflow-hidden`}
            >
              <div
                className={`mr-3 h-8 w-8 flex items-center justify-center rounded-lg text-[10px] font-bold transition-all duration-300 ${
                  isActive
                    ? "bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/40"
                    : "bg-slate-800/50 text-slate-500 group-hover:bg-slate-700/50 group-hover:text-slate-300"
                }`}
              >
                {item
                  .split(" ")
                  .map((word) => word[0])
                  .join("")
                  .slice(0, 2)
                  .toUpperCase()}
              </div>
              <span className="truncate">{item}</span>
              {isActive && (
                <div className="absolute right-2 h-1 w-1 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
              )}
            </button>
          );
        })}
      </nav>
      <div className="px-4 py-4 border-t border-slate-800/80 text-xs text-slate-500">
        <div className="flex items-center justify-between">
          <span>AI Sentiment Engine</span>
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </div>
    </aside>
  );
};

