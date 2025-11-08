# app/services/karma_service.py
"""
Karma Service Client

Pulls Karma scores from Siddhesh's Karma Tracker endpoint.
Adds behavioral weighting to routing decisions.
Includes caching, retry logic, and toggle flag for experiments.
"""

import logging
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class KarmaScore(BaseModel):
    """Karma score data model"""
    agent_id: str
    karma_score: float  # Range: -1.0 to 1.0 (negative=bad, positive=good)
    karma_trend: str  # "improving" | "stable" | "declining"
    last_updated: str
    feedback_count: int


class KarmaServiceClient:
    """
    Client for Karma Tracker service.
    
    Features:
    - Async Karma score retrieval
    - Score caching with TTL
    - Retry logic
    - Toggle ON/OFF for experiments
    - Graceful degradation
    """
    
    def __init__(
        self,
        karma_endpoint: str,
        cache_ttl: int = 60,
        timeout: int = 5,
        max_retries: int = 3,
        enabled: bool = True
    ):
        """
        Initialize Karma service client.
        
        Args:
            karma_endpoint: Karma Tracker API endpoint
            cache_ttl: Cache time-to-live in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            enabled: Enable/disable Karma weighting (toggle flag)
        """
        self.karma_endpoint = karma_endpoint
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = enabled
        
        # Karma score cache: {agent_id: (score, timestamp)}
        self._karma_cache: Dict[str, tuple] = {}
        
        # Metrics
        self.metrics = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "retries": 0,
        }
        
        logger.info(
            f"KarmaServiceClient initialized (enabled={enabled}, "
            f"endpoint={karma_endpoint})"
        )
    
    async def get_karma_score(self, agent_id: str) -> float:
        """
        Get Karma score for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Karma score (-1.0 to 1.0), or 0.0 if disabled/error
        """
        if not self.enabled:
            logger.debug("Karma weighting disabled, returning neutral score")
            return 0.0
        
        # Check cache first
        if self._is_cached(agent_id):
            self.metrics["cache_hits"] += 1
            cached_score, _ = self._karma_cache[agent_id]
            logger.debug(f"Cache hit for {agent_id}: karma={cached_score}")
            return cached_score
        
        self.metrics["cache_misses"] += 1
        
        # Fetch from Karma Tracker
        score = await self._fetch_karma_from_endpoint(agent_id)
        
        # Cache result
        self._karma_cache[agent_id] = (score, datetime.utcnow())
        
        return score
    
    async def get_karma_scores_batch(
        self,
        agent_ids: List[str]
    ) -> Dict[str, float]:
        """
        Get Karma scores for multiple agents.
        
        Args:
            agent_ids: List of agent IDs
        
        Returns:
            Dict mapping agent_id → karma_score
        """
        if not self.enabled:
            return {agent_id: 0.0 for agent_id in agent_ids}
        
        scores = {}
        
        # Fetch in parallel
        tasks = [self.get_karma_score(agent_id) for agent_id in agent_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                logger.warning(f"Error fetching Karma for {agent_id}: {result}")
                scores[agent_id] = 0.0  # Neutral score on error
            else:
                scores[agent_id] = result
        
        return scores
    
    async def get_karma_details(
        self,
        agent_id: str
    ) -> Optional[KarmaScore]:
        """
        Get detailed Karma information for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            KarmaScore object or None if unavailable
        """
        if not self.enabled:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.karma_endpoint}/agents/{agent_id}/details"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return KarmaScore(**data)
                    else:
                        logger.warning(
                            f"Failed to get Karma details: {response.status}"
                        )
                        return None
        
        except Exception as e:
            logger.error(f"Error fetching Karma details: {e}")
            return None
    
    async def _fetch_karma_from_endpoint(self, agent_id: str) -> float:
        """
        Fetch Karma score from Karma Tracker endpoint with retry logic.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            Karma score (-1.0 to 1.0), or 0.0 on error
        """
        self.metrics["requests"] += 1
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.karma_endpoint}/agents/{agent_id}/score"
                    
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            score = float(data.get("karma_score", 0.0))
                            
                            # Clamp to valid range
                            score = max(-1.0, min(1.0, score))
                            
                            logger.info(
                                f"Retrieved Karma for {agent_id}: {score}"
                            )
                            return score
                        else:
                            logger.warning(
                                f"Karma endpoint returned {response.status} "
                                f"for {agent_id}"
                            )
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{self.max_retries} "
                    f"for {agent_id}"
                )
                self.metrics["retries"] += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                logger.error(
                    f"Error fetching Karma on attempt {attempt + 1}: {e}"
                )
                self.metrics["retries"] += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries exhausted
        logger.error(
            f"Failed to retrieve Karma for {agent_id} after "
            f"{self.max_retries} attempts"
        )
        self.metrics["errors"] += 1
        return 0.0  # Neutral score on failure
    
    def _is_cached(self, agent_id: str) -> bool:
        """Check if Karma score is cached and not expired"""
        if agent_id not in self._karma_cache:
            return False
        
        _, timestamp = self._karma_cache[agent_id]
        age = (datetime.utcnow() - timestamp).total_seconds()
        
        return age < self.cache_ttl
    
    def clear_cache(self, agent_id: Optional[str] = None):
        """
        Clear Karma cache for specific agent or all agents.
        
        Args:
            agent_id: Agent to clear cache for, or None to clear all
        """
        if agent_id is None:
            self._karma_cache.clear()
            logger.info("Cleared all Karma caches")
        else:
            if agent_id in self._karma_cache:
                del self._karma_cache[agent_id]
                logger.debug(f"Cleared Karma cache for {agent_id}")
    
    def toggle_karma_weighting(self, enabled: bool):
        """
        Toggle Karma weighting ON/OFF.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        logger.info(f"Karma weighting {'enabled' if enabled else 'disabled'}")
    
    def get_metrics(self) -> Dict:
        """Get service metrics"""
        return {
            **self.metrics,
            "cache_size": len(self._karma_cache),
            "enabled": self.enabled,
        }


# Global Karma service instance
_karma_service: Optional[KarmaServiceClient] = None


def get_karma_service() -> KarmaServiceClient:
    """
    Get or create Karma service singleton.
    
    Returns:
        KarmaServiceClient instance
    """
    global _karma_service
    
    if _karma_service is None:
        from app.core.config import settings
        
        _karma_service = KarmaServiceClient(
            karma_endpoint=settings.KARMA_ENDPOINT,
            cache_ttl=settings.KARMA_CACHE_TTL,
            timeout=settings.KARMA_TIMEOUT,
            max_retries=3,  # Default value since KARMA_MAX_RETRIES not in config
            enabled=settings.KARMA_ENABLED
        )
    
    return _karma_service