from typing import List
from pydantic import BaseModel, Field, field_validator
from app.config import settings


class ResearchRequest(BaseModel):
    """
    Payload for initiating a multi-website research session.
    """
    query: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The research query (10 to 500 characters)",
        examples=["Best laptops for engineering students under $1500 in 2026"]
    )
    urls: List[str] = Field(
        ...,
        min_length=1,
        description=f"List of 1 to {settings.MAX_URLS} valid public HTTP/HTTPS URLs",
        examples=[
            [
                "https://example.com/macbook-air-review",
                "https://example.org/dell-xps-13"
            ]
        ]
    )

    @field_validator("query")
    @classmethod
    def clean_query(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Query must be at least 10 characters long after trimming.")
        if len(cleaned) > 500:
            raise ValueError("Query cannot exceed 500 characters.")
        return cleaned

    @field_validator("urls")
    @classmethod
    def validate_urls_list(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one URL must be provided.")
        if len(v) > settings.MAX_URLS:
            raise ValueError(f"A maximum of {settings.MAX_URLS} URLs may be researched simultaneously.")

        # Strip whitespace
        cleaned_urls = [u.strip() for u in v if isinstance(u, str) and u.strip()]
        if not cleaned_urls:
            raise ValueError("At least one valid non-empty URL must be provided.")

        return cleaned_urls
