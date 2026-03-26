import type { MarketDataPoint, NewsItem } from "../mockMarketData";

/**
 * Utility to export market and sentiment data to CSV for Tableau/Power BI
 */
export function exportToCSV(
  symbol: string,
  marketData: MarketDataPoint[],
  news: NewsItem[]
) {
  const headers = ["Source", "Date/Time", "Value/Headline", "Sentiment", "Details"];
  const rows: string[][] = [];

  // Add Market Data Rows
  marketData.forEach((point) => {
    rows.push([
      "Market Data",
      point.date,
      point.price.toString(),
      point.sentiment_score.toString(),
      `Volume: ${point.volume}, Confidence: ${point.confidence}%`
    ]);
  });

  // Add News Data Rows
  news.forEach((item) => {
    rows.push([
      "News Intelligence",
      item.timestamp,
      item.headline.replace(/,/g, ";"), // Escape commas
      item.sentiment,
      `Impact: ${item.impact}`
    ]);
  });

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.join(","))
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  
  const filename = `${symbol}_MarketSentinel_Export_${new Date().toISOString().split('T')[0]}.csv`;
  
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
