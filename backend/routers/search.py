from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query

from core.config import FINNHUB_BASE_URL, FINNHUB_TOKEN
from schemas import SymbolSearchResponse, SymbolSearchResult

router = APIRouter()


def _search_relevance_key(item: dict, query: str) -> tuple:
    """
    Ranks Finnhub search results the way a trading platform's search box does.

    US-primary common stock (no exchange suffix, e.g. "AAPL" not "APP.CN") is ranked
    ahead of foreign-exchange listings REGARDLESS of match quality — a plain-text query
    almost always means the well-known US ticker/company, and Finnhub's fuzzy symbol
    matching otherwise lets obscure foreign listings whose SYMBOL happens to start with
    the query (e.g. "APP.CN", "APP.MX") crowd out well-known companies whose NAME matches
    (e.g. "Apple Inc", "Applied Materials") but whose symbol doesn't share the prefix.
    Within that US/foreign split, results are ranked by match quality: exact symbol
    match, then symbol-starts-with, then name-starts-with, then substring matches.
    Lower tuples sort first (used directly as a `sorted(..., key=...)` key).
    """
    symbol = str(item.get("symbol", "")).upper()
    description = str(item.get("description", "")).upper()
    q = query.upper().strip()

    is_us_primary = "." not in symbol
    is_equity = (item.get("type") or "").upper() in {"COMMON STOCK", "EQUITY"}

    if symbol == q:
        match_tier = 0
    elif symbol.startswith(q):
        match_tier = 1
    elif description.startswith(q):
        match_tier = 2
    elif q in symbol:
        match_tier = 3
    elif q in description:
        match_tier = 4
    else:
        match_tier = 5

    return (
        0 if is_us_primary else 1,
        match_tier,
        0 if is_equity else 1,
        len(symbol),  # shorter symbols first as a final tiebreaker (AAPL over AAPL-derived variants)
    )


@router.get("/api/search", response_model=SymbolSearchResponse)
async def search_symbols(q: str = Query(..., min_length=1, max_length=64)) -> SymbolSearchResponse:
    if not FINNHUB_TOKEN:
        raise HTTPException(status_code=500, detail="FINNHUB_API_KEY is not configured")

    params = {"q": q, "token": FINNHUB_TOKEN}
    async with httpx.AsyncClient(base_url=FINNHUB_BASE_URL, timeout=10.0) as client:
        try:
            resp = await client.get("/search", params=params)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover
            raise HTTPException(status_code=502, detail=f"Finnhub search error: {exc}") from exc

    data = resp.json() or {}
    result = data.get("result", [])
    valid = [r for r in result if r.get("symbol") and r.get("description")]

    # Sort first, then dedupe by symbol alone (keeping the first/best-ranked record) —
    # Finnhub often lists the same ticker multiple times from different data-vendor
    # records with slightly different description text (e.g. "APPLOVIN CORP-CLASS A" vs
    # "Applovin Corp"), which a symbol+description dedupe key would miss entirely.
    ranked = sorted(valid, key=lambda r: _search_relevance_key(r, q))
    seen_symbols: set[str] = set()
    deduped = []
    for r in ranked:
        symbol = str(r["symbol"]).upper()
        if symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        deduped.append(r)

    ordered = deduped[:15]

    return SymbolSearchResponse(
        count=int(data.get("count", len(ordered)) or len(ordered)),
        result=[
            SymbolSearchResult(
                symbol=str(r.get("symbol", "")).upper(),
                description=str(r.get("description", "")),
                type=r.get("type"),
            )
            for r in ordered
        ],
    )
