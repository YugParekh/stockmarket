from __future__ import annotations

from fastapi import APIRouter, Query

import ai_insights
from schemas import AIChatRequest
from services.ai_context import build_ai_context

router = APIRouter()


@router.get("/api/ai-insights")
async def get_ai_insights(symbol: str = Query("AAPL", min_length=1, max_length=32)) -> dict:
    """Detailed AI-generated analysis and strategy considerations, grounded in
    real dashboard data (see ai_insights.py). Cached per symbol for 10 minutes
    to respect Gemini's free-tier rate limits — this is user-triggered from the
    frontend, not polled automatically."""
    if not ai_insights.is_configured():
        return {"symbol": symbol, "configured": False, "content": None, "disclaimer": ai_insights.DISCLAIMER}

    context = await build_ai_context(symbol)
    content = ai_insights.generate_deep_insight(symbol, context)
    return {"symbol": symbol, "configured": True, "content": content, "disclaimer": ai_insights.DISCLAIMER}


@router.post("/api/ai-chat")
async def post_ai_chat(body: AIChatRequest) -> dict:
    """Free-form Q&A grounded in the same real data block as /api/ai-insights."""
    if not ai_insights.is_configured():
        return {"configured": False, "answer": None, "disclaimer": ai_insights.DISCLAIMER}

    context = await build_ai_context(body.symbol)
    answer = ai_insights.answer_question(body.symbol, context, body.question)
    return {"configured": True, "answer": answer, "disclaimer": ai_insights.DISCLAIMER}
