"""
WebScout Backend Configuration.
Manages application settings and environment variables centrally via Pydantic Settings.
"""

from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WebScout API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Engine Selection
    FETCHER: str = "playwright"  # "playwright" or "mock"
    ANALYZER: str = "mock"       # "mock" (Gemini in next step)
    MAX_URLS: int = 5
    USE_MOCK: bool = False       # If True, overrides FETCHER to "mock"

    # Gemini API Key (optional for Step 7)
    GEMINI_API_KEY: Optional[str] = None

    # Fetching constraints
    NAVIGATION_TIMEOUT_MS: int = 20000  # 20 seconds maximum per URL
    MAX_EXTRACTED_CHARS: int = 12000    # 12,000 characters limit per URL
    MAX_CONCURRENT_FETCHES: int = 5     # Maximum concurrent browser fetches

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return ["http://localhost:3000"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    @property
    def active_fetcher(self) -> str:
        """Returns the actual fetcher to use taking USE_MOCK flag into account."""
        if self.USE_MOCK or self.FETCHER.lower() == "mock":
            return "mock"
        return "playwright"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
