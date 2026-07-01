const BASE_URL = "https://stockmarket-backend-sa4e.onrender.com";

export interface QuoteItem {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
}

export async function fetchQuotes(symbols: string[]): Promise<QuoteItem[]> {
  const params = new URLSearchParams({ symbols: symbols.join(",") });
  const res = await fetch(`${BASE_URL}/api/quotes?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Quotes API error: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as QuoteItem[];
}
