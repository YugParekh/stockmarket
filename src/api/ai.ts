/**
 * Hugging Face Inference API integration for Sentiment Analysis
 * Model: finiteautomata/bertweet-base-sentiment-analysis
 */

const HF_MODEL = "finiteautomata/bertweet-base-sentiment-analysis";
const TOKEN = import.meta.env.VITE_HF_API_TOKEN;

export type AISentiment = "Bullish" | "Bearish" | "Neutral";

interface HFResponse {
  label: "POS" | "NEG" | "NEU";
  score: number;
}

/**
 * Maps HF model labels to dashboard sentiment types.
 */
const mapLabel = (label: string): AISentiment => {
  if (label === "POS") return "Bullish";
  if (label === "NEG") return "Bearish";
  return "Neutral";
};

/**
 * Analyzes news headline sentiment using Hugging Face.
 */
export async function analyzeSentiment(text: string): Promise<AISentiment | null> {
  if (!TOKEN) {
    console.warn("Hugging Face API token missing. Falling back to mock sentiment.");
    return null;
  }

  try {
    const response = await fetch(
      `https://api-inference.huggingface.co/models/${HF_MODEL}`,
      {
        headers: { Authorization: `Bearer ${TOKEN}` },
        method: "POST",
        body: JSON.stringify({ inputs: text }),
      }
    );

    if (!response.ok) {
      console.error(`HF Inference API error: ${response.status}`);
      return null;
    }

    const result = await response.json();
    
    // HF response is usually an array of arrays of objects for this model
    if (Array.isArray(result) && Array.isArray(result[0])) {
      const bestMatch = result[0].sort((a: HFResponse, b: HFResponse) => b.score - a.score)[0];
      return mapLabel(bestMatch.label);
    }

    return null;
  } catch (error) {
    console.error("Failed to fetch sentiment from Hugging Face:", error);
    return null;
  }
}
