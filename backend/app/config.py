"""
WebScout Backend Configuration.
Manages application settings and environment variables centrally via Pydantic Settings.
"""

from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_KEYS = {"", "your_gemini_api_key_here"}


class Settings(BaseSettings):
    PROJECT_NAME: str = "WebScout API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Engine Selection ("auto" uses Gemini when GEMINI_API_KEY is configured, else mock)
    FETCHER: str = "playwright"  # "playwright" or "mock"
    ANALYZER: str = "auto"       # "auto", "gemini", or "mock"
    MAX_URLS: int = 5
    USE_MOCK: bool = False       # If True, forces mock fetcher and mock analyzer

    # Google Gemini API Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

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
    def cleaned_gemini_api_key(self) -> str:
        """Returns trimmed Gemini API key or empty string when missing/placeholder."""
        key = (self.GEMINI_API_KEY or "").strip()
        return "" if key in _PLACEHOLDER_KEYS else key

    @property
    def has_valid_gemini_key(self) -> bool:
        """True when a non-placeholder GEMINI_API_KEY is configured."""
        return bool(self.cleaned_gemini_api_key)

    @property
    def active_fetcher(self) -> str:
        """Returns the actual fetcher to use taking USE_MOCK flag into account."""
        if self.USE_MOCK or self.FETCHER.lower() == "mock":
            return "mock"
        return "playwright"

    @property
    def active_analyzer(self) -> str:
        """Returns 'gemini' when enabled and GEMINI_API_KEY is valid, otherwise 'mock'."""
        mode = (self.ANALYZER or "auto").strip().lower()
        if self.USE_MOCK or mode == "mock":
            return "mock"
        if mode in ("auto", "gemini") and self.has_valid_gemini_key:
            return "gemini"
        return "mock"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
