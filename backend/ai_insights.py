"""
AI-generated deep insights and Q&A, powered by Google's Gemini API (free tier).

This is explicitly NOT a substitute for the calibrated signal engine's honest,
backtested confidence (see signal_engine/README.md) — it's a natural-language
layer that explains and contextualizes the REAL computed data already in the
dashboard (price, ML prediction, risk metrics, news) rather than inventing new
numbers. Every prompt is grounded in a context block built from real data; the
model is explicitly instructed not to fabricate figures, and every response is
paired with a disclaimer the API always returns alongside the content.

Setup: get a free API key at https://aistudio.google.com/apikey and set
GEMINI_API_KEY in backend/.env. Without a key, these endpoints return
{"configured": false, ...} rather than failing — the rest of the dashboard
works with or without this feature configured.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

DISCLAIMER = (
    "AI-generated commentary for educational purposes, not financial advice. "
    "It's grounded in the real data shown above, but the underlying prediction "
    "model does not reliably beat a simple buy-and-hold baseline (see the "
    "signal engine report) — treat any suggestion here as a starting point for "
    "your own research, not an instruction to act on."
)

GEMINI_MODEL = "gemini-3.5-flash"

_client = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai

        _client = genai.Client(api_key=api_key)
    except Exception as exc:  # noqa: BLE001 - any init failure means "not configured"
        print(f"[ai_insights] failed to init Gemini client: {exc}")
        _client = None
    return _client


def is_configured() -> bool:
    return _get_client() is not None


@dataclass
class _CacheEntry:
    content: str
    expires_at: float


_insight_cache: dict[str, _CacheEntry] = {}
_INSIGHT_TTL_SECONDS = 600  # 10 min — free-tier rate limits are tight, avoid regenerating per poll


def build_context_block(
    symbol: str,
    latest_price: float,
    direction: str,
    confidence: int,
    is_ml_backed: bool,
    risk_level: str,
    value_at_risk_pct: float,
    sentiment_label: str,
    news_headlines: list[str],
) -> str:
    """Formats REAL data already computed elsewhere in this app into a compact
    block for the model to reason over — it is instructed to use only this
    data, never invent new numbers."""
    news_block = "\n".join(f"- {h}" for h in news_headlines[:5]) or "- (no recent headlines available)"
    confidence_note = (
        "backtested historical-accuracy figure, not a guarantee"
        if is_ml_backed
        else "unvalidated heuristic fallback — low confidence in this number itself"
    )
    return f"""Symbol: {symbol}
Latest price: {latest_price}
Model direction: {direction} ({confidence}% confidence — {confidence_note})
Risk level: {risk_level} (1-day VaR ~{value_at_risk_pct:.2f}%)
News sentiment: {sentiment_label}
Recent headlines:
{news_block}"""


_SYSTEM_INSTRUCTION = """You are a markets analysis assistant embedded in a stock dashboard. You ONLY have access to the data block given to you in each request — never invent prices, percentages, or news that isn't in that block.

Give direct, actionable, well-organized suggestions (concrete things a trader might consider watching or doing), but ALWAYS pair every suggestion with an explicit statement of the risk/uncertainty involved, since the underlying model's historical accuracy is modest (roughly 50-58%, barely different from assuming the market just goes up). Never claim certainty. Never tell the user to definitely buy or sell — frame actions as "one approach worth weighing is X, with Y risk" style. Keep the tone professional and concise, not hedgy filler — be direct about what to consider and equally direct about what to be worried about. Use short sections/bullets, not long unstructured paragraphs. Do not repeat a generic disclaimer yourself — the application shows one separately."""


def generate_deep_insight(symbol: str, context_block: str) -> Optional[str]:
    """Returns a detailed, cached AI analysis, or None if Gemini isn't
    configured or the call failed — caller should show a clear fallback."""
    cached = _insight_cache.get(symbol)
    now = time.time()
    if cached and cached.expires_at > now:
        return cached.content

    client = _get_client()
    if client is None:
        return None

    prompt = f"""Here is the current real data for {symbol}:

{context_block}

Write a detailed analysis covering:
1. What the current technical/sentiment picture suggests, and what specifically a trader might watch for next (concrete levels, indicators, or events — only referencing what's in the data above).
2. 2-3 concrete strategic considerations (e.g. position sizing, stop-loss placement philosophy, what would invalidate the current view) — direct and actionable, but each paired with its risk.
3. What to study to get better at reading this kind of setup yourself (name specific concepts: e.g. RSI divergence, risk/reward ratios, position sizing frameworks — not vague "learn more" advice)."""

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            system_instruction=_SYSTEM_INSTRUCTION,
            input=prompt,
        )
        content = interaction.output_text
    except Exception as exc:  # noqa: BLE001 - a failed AI call must not break the dashboard
        print(f"[ai_insights] Gemini call failed for {symbol}: {exc}")
        return None

    _insight_cache[symbol] = _CacheEntry(content=content, expires_at=now + _INSIGHT_TTL_SECONDS)
    return content


def answer_question(symbol: str, context_block: str, question: str) -> Optional[str]:
    """Answers a free-form user question grounded in the same real data block.
    Not cached (each question differs) — the free tier's own rate limiting is
    the backstop against abuse for now."""
    client = _get_client()
    if client is None:
        return None

    prompt = f"""Here is the current real data for {symbol}:

{context_block}

A user is asking: "{question}"

Answer directly and specifically using only the data above. If the question asks about something not covered by this data (e.g. a different symbol, a longer historical period, fundamentals not shown here), say so plainly rather than guessing."""

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            system_instruction=_SYSTEM_INSTRUCTION,
            input=prompt,
        )
        return interaction.output_text
    except Exception as exc:  # noqa: BLE001
        print(f"[ai_insights] Gemini Q&A call failed for {symbol}: {exc}")
        return None
