"""Pydantic request/response models shared across routers and services."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel

PredictionDirection = Literal["UP", "DOWN"]


class MarketDataPoint(BaseModel):
    date: str
    price: float
    sentiment_score: float
    volume: int
    prediction: PredictionDirection
    confidence: int


class NewsItem(BaseModel):
    id: int
    headline: str
    sentiment: Literal["Positive", "Neutral", "Negative"]
    impact: Literal["Low", "Medium", "High"]
    timestamp: str


class AlertItem(BaseModel):
    id: int
    message: str
    severity: Literal["Positive", "Neutral", "Negative"]
    createdAt: str


class KeywordStat(BaseModel):
    keyword: str
    frequency: int
    sentiment: Literal["Positive", "Neutral", "Negative"]


class SentimentBucket(BaseModel):
    label: str
    value: int


class PredictionSummary(BaseModel):
    direction: PredictionDirection
    confidence: int
    expectedReturnPct: float
    volatilityScore: float
    horizon: str


class RiskSummary(BaseModel):
    level: Literal["Low", "Medium", "High"]
    valueAtRiskPct: float


class Insights(BaseModel):
    nextMove: PredictionSummary
    risk: RiskSummary
    commentary: str


class DashboardResponse(BaseModel):
    symbol: str
    range: str
    marketData: List[MarketDataPoint]
    news: List[NewsItem]
    alerts: List[AlertItem]
    keywords: List[KeywordStat]
    sentimentDistribution: List[SentimentBucket]
    insights: Insights


class SymbolSearchResult(BaseModel):
    symbol: str
    description: str
    type: str | None = None


class SymbolSearchResponse(BaseModel):
    count: int
    result: list[SymbolSearchResult]


class QuoteItem(BaseModel):
    symbol: str
    price: float
    change: float
    changePercent: float
    volume: int


class AIChatRequest(BaseModel):
    symbol: str
    question: str
