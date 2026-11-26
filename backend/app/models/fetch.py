from typing import Optional
from pydantic import BaseModel, Field


class FetchResult(BaseModel):
    """
    Structured outcome of fetching and extracting content from a single URL.
    """
    url: str
    title: str = ""
    extracted_text: str = ""
    status: str = Field(default="ok", description="'ok' or 'failed'")
    error: Optional[str] = None
    elapsed_ms: int = 0

    @property
    def is_success(self) -> bool:
        return self.status == "ok" and bool(self.extracted_text.strip())
