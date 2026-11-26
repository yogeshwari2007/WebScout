from abc import ABC, abstractmethod
from app.models.fetch import FetchResult


class PageFetcher(ABC):
    """
    Abstract interface for website fetching engines.
    """

    @abstractmethod
    async def fetch(self, url: str) -> FetchResult:
        """
        Asynchronously visits a URL and extracts cleaned, readable content.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Cleans up any allocated browser or network resources.
        """
        pass
