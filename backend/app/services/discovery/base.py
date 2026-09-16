import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

import structlog

logger = structlog.get_logger()


class BaseDiscoveryEngine(ABC):
    """Base class for all discovery engines in Pulse."""

    def __init__(self):
        self.logger = logger.bind(engine=self.__class__.__name__)
        self.start_time = None
        self.discovered_assets = []

    @abstractmethod
    async def discover(self, target: str, **kwargs) -> dict:
        """Execute discovery for a given target."""
        pass

    @abstractmethod
    async def validate_target(self, target: str) -> bool:
        """Validate that the target is suitable for this engine."""
        pass

    async def run(self, target: str, **kwargs) -> dict:
        """Run discovery with timing and error handling."""
        self.start_time = datetime.utcnow()
        self.logger.info("discovery_started", target=target)

        try:
            if not await self.validate_target(target):
                return {"error": f"Invalid target: {target}", "status": "failed"}

            result = await self.discover(target, **kwargs)
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()

            self.logger.info(
                "discovery_completed",
                target=target,
                assets_found=len(self.discovered_assets),
                duration=f"{elapsed:.2f}s",
            )

            return {
                "status": "completed",
                "target": target,
                "engine": self.__class__.__name__,
                "assets_found": len(self.discovered_assets),
                "duration_seconds": elapsed,
                "results": result,
                "assets": self.discovered_assets,
            }

        except Exception as e:
            self.logger.error("discovery_failed", target=target, error=str(e))
            return {
                "status": "failed",
                "target": target,
                "engine": self.__class__.__name__,
                "error": str(e),
            }

    def add_asset(self, asset_data: dict) -> None:
        """Add a discovered asset to the results."""
        asset_data.setdefault("discovered_at", datetime.utcnow().isoformat())
        asset_data.setdefault("engine", self.__class__.__name__)
        self.discovered_assets.append(asset_data)

    async def _rate_limit(self, delay: float = 1.0) -> None:
        """Apply rate limiting between API calls."""
        await asyncio.sleep(delay)

    async def _retry(self, func, max_retries: int = 3, delay: float = 2.0):
        """Retry a function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    error=str(e),
                )
                await asyncio.sleep(delay * (2**attempt))
