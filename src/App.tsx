import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { Dashboard } from "./pages/Dashboard";
import type { UiRange } from "./api/dashboard";

const sections = [
  "Dashboard",
  "Market Overview",
  "Sentiment Analysis",
  "News Intelligence",
  "Predictions",
  "Alerts",
  "Settings"
];

function App() {
  const [symbol, setSymbol] = useState("AAPL");
  const [range, setRange] = useState<UiRange>("1M");
  const [section, setSection] = useState<string>("Dashboard");

  const currentSection = sections.includes(section) ? section : "Dashboard";

  return (
    <div className="min-h-screen flex bg-[#0b0b0b] text-slate-100">
      <Sidebar active={currentSection} onSelect={setSection} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar
          symbol={symbol}
          range={range}
          onSymbolChange={setSymbol}
          onRangeChange={setRange}
        />
        <main className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-6 bg-gradient-to-br from-black via-[#050816] to-black">
          <Dashboard symbol={symbol} range={range} view={currentSection} />
        </main>
      </div>
    </div>
  );
}

export default App;

