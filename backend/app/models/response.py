from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ComparisonItemResponse(BaseModel):
    name: str = Field(..., description="Name of candidate item or product evaluated")
    source_url: str = Field(default="", description="Original reference URL")
    values: Dict[str, str] = Field(default_factory=dict, description="Criterion key-value attribute pairs")
    pros: List[str] = Field(default_factory=list, description="Key advantages")
    cons: List[str] = Field(default_factory=list, description="Trade-offs and caveats")


class RecommendationResponse(BaseModel):
    winner: str = Field(..., description="Top recommended candidate")
    reasoning: str = Field(..., description="Detailed synthesis rationale")
    source_urls: List[str] = Field(default_factory=list, description="Referenced URLs backing the recommendation")


class SourceStatusResponse(BaseModel):
    url: str
    title: str = ""
    status: str = Field(default="ok", description="'ok' or 'failed'")
    error: Optional[str] = None


class ResearchResponse(BaseModel):
    query: str
    summary: str
    criteria: List[str] = Field(default_factory=list)
    items: List[ComparisonItemResponse] = Field(default_factory=list)
    recommendation: RecommendationResponse
    sources: List[SourceStatusResponse] = Field(default_factory=list)
    elapsed_ms: int = Field(default=0, description="Total execution time in milliseconds")


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str
    version: str
    fetcher: str
    analyzer: str
