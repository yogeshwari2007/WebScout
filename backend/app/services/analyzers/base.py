from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.models.fetch import FetchResult


class BaseAnalyzer(ABC):
    """
    Abstract interface for AI analysis and synthesis engines.
    """

    @abstractmethod
    async def analyze(
        self, query: str, contents: List[FetchResult]
    ) -> Dict[str, Any]:
        """
        Synthesizes extracted website contents against the research query.
        Returns a dictionary matching the frontend ResearchResponse structure.
        """
        pass
