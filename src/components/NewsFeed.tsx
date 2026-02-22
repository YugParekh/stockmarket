import { NewsCard } from "./NewsCard";

interface NewsFeedProps {
  loading?: boolean;
  items: NewsItem[];
}

export const NewsFeed = ({ loading, items }: NewsFeedProps) => {
  if (loading) {
    return (
      <section className="glass-card-soft h-[400px] animate-pulse rounded-2xl" />
    );
  }

  return (
    <section className="glass-card-soft p-5 h-[400px] flex flex-col rounded-2xl border border-slate-800/50">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-100 uppercase tracking-widest">
            News Feed
          </h2>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Real-time intelligence & sentiment analysis
          </p>
        </div>
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-800/50 border border-slate-700/50 text-slate-400">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10l4 4v10a2 2 0 01-2 2z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 2v6h6" />
          </svg>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
        {items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  );
};
  );
};

