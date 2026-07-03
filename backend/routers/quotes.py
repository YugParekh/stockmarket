from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from schemas import QuoteItem
from services.quotes import fetch_quote

router = APIRouter()


@router.get("/api/quotes", response_model=List[QuoteItem])
async def get_quotes(symbols: str = Query(..., min_length=1, max_length=200)) -> List[QuoteItem]:
    """Real current price/change/volume for multiple symbols in one call — powers
    the 'Market At A Glance' summary cards, which previously showed hardcoded
    static numbers regardless of what the backend returned."""
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:20]
    if not symbol_list:
        raise HTTPException(status_code=422, detail="No valid symbols provided")

    results = [await fetch_quote(s) for s in symbol_list]
    return [q for q in results if q is not None]
