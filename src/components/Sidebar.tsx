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
              className={`group flex items-center w-full px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-cyan-500/15 text-cyan-300 border border-cyan-400/60 shadow-neon-cyan"
                  : "text-slate-300/80 hover:text-cyan-300 hover:bg-cyan-500/10 hover:border-cyan-400/40"
              } border border-transparent`}
            >
              <span
                className={`mr-3 h-7 w-7 flex items-center justify-center rounded-md text-xs font-semibold tracking-widest ${
                  isActive
                    ? "bg-cyan-500/20 text-cyan-300"
                    : "bg-slate-800/80 text-slate-300 group-hover:bg-cyan-500/20 group-hover:text-cyan-300"
                }`}
              >
                {item
                  .split(" ")
                  .map((word) => word[0])
                  .join("")
                  .slice(0, 3)
                  .toUpperCase()}
              </span>
              <span>{item}</span>
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

