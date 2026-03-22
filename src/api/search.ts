export interface SymbolSearchItem {
  symbol: string;
  description: string;
  type?: string | null;
}

export interface SymbolSearchResponse {
  count: number;
  result: SymbolSearchItem[];
}

const BASE_URL = "https://stockmarket-backend-sa4e.onrender.com";

export async function searchSymbols(q: string): Promise<SymbolSearchItem[]> {
  const params = new URLSearchParams({ q });

  const res = await fetch(
    `${BASE_URL}/api/search?${params.toString()}`
  );

  if (!res.ok) {
    throw new Error(`Search API error: ${res.status} ${res.statusText}`);
  }

  const json = (await res.json()) as SymbolSearchResponse;
  return json.result ?? [];
}