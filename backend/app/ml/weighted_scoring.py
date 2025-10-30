# app/ml/weighted_scoring.py
"""
Weighted Scoring Engine: Combines multiple score sources.

Combines:
1. Rule-based score (traditional InsightFlow logic)
2. Feedback-based score (from Core feedback service)
3. Availability score (agent health/uptime)

Result: Single confidence score (0-1) for routing decisions.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import yaml
import os

logger = logging.getLogger(__name__)


@dataclass
class ScoreComponent:
    """Individual score component"""
    name: str
    score: float
    weight: float
    
    def weighted_value(self) -> float:
        """Get weighted score value"""
        return self.score * self.weight


@dataclass
class ConfidenceScore:
    """Final confidence score with breakdown"""
    final_score: float
    components: Dict[str, ScoreComponent]
    normalization_method: str
    
    def get_breakdown(self) -> Dict[str, Any]:
        """Get human-readable breakdown"""
        return {
            "final_score": self.final_score,
            "components": {
                name: {
                    "score": comp.score,
                    "weight": comp.weight,
                    "weighted_value": comp.weighted_value()
                }
                for name, comp in self.components.items()
            }
        }


class WeightedScoringEngine:
    """
    Engine for combining multiple scoring sources.
    
    Configuration (from scoring_config.yaml):
    ```yaml
    scoring_weights:
      rule_based: 0.4
      feedback_based: 0.4
      availability: 0.2
    ```
    """
    
    def __init__(self, config_path: str = "app/config/scoring_config.yaml"):
        """
        Initialize scoring engine.
        
        Args:
            config_path: Path to scoring configuration YAML
        """
        self.config = self._load_config(config_path)
        self.weights = self.config.get("scoring_weights", {})
        
        # Validate weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Scoring weights don't sum to 1.0: {total_weight}. "
                f"Normalizing..."
            )
            self.weights = self._normalize_weights(self.weights)
    
    def calculate_confidence(
        self,
        agent_id: str,
        rule_based_score: float,
        feedback_score: float,
        availability_score: float
    ) -> ConfidenceScore:
        """
        Calculate final confidence score from components.
        
        Args:
            agent_id: Agent identifier
            rule_based_score: Score from traditional rules (0-1)
            feedback_score: Score from Core feedback service (0-1)
            availability_score: Agent availability score (0-1)
        
        Returns:
            ConfidenceScore object
        """
        # Validate inputs
        for score in [rule_based_score, feedback_score, availability_score]:
            if not (0.0 <= score <= 1.0):
                logger.warning(
                    f"Score out of bounds [0-1]: {score}. Clamping..."
                )
        
        # Create score components
        components = {
            "rule_based": ScoreComponent(
                name="rule_based",
                score=self._clamp(rule_based_score),
                weight=self.weights.get("rule_based", 0.33)
            ),
            "feedback_based": ScoreComponent(
                name="feedback_based",
                score=self._clamp(feedback_score),
                weight=self.weights.get("feedback_based", 0.33)
            ),
            "availability": ScoreComponent(
                name="availability",
                score=self._clamp(availability_score),
                weight=self.weights.get("availability", 0.34)
            ),
        }
        
        # Calculate weighted sum
        total_weighted_score = sum(
            component.weighted_value()
            for component in components.values()
        )
        
        # Normalize
        final_score = self._normalize_score(total_weighted_score)
        
        # Log detailed breakdown if enabled
        if self.config.get("logging", {}).get("score_breakdown", False):
            logger.debug(
                f"Calculated confidence for {agent_id}: "
                f"{final_score:.2f} (breakdown: "
                f"rule={components['rule_based'].score:.2f}×{components['rule_based'].weight:.1f}={components['rule_based'].weighted_value():.3f}, "
                f"feedback={components['feedback_based'].score:.2f}×{components['feedback_based'].weight:.1f}={components['feedback_based'].weighted_value():.3f}, "
                f"avail={components['availability'].score:.2f}×{components['availability'].weight:.1f}={components['availability'].weighted_value():.3f})"
            )
        else:
            logger.debug(f"Calculated confidence for {agent_id}: {final_score:.2f}")
        
        return ConfidenceScore(
            final_score=final_score,
            components=components,
            normalization_method="min_max"
        )
    
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0"""
        total = sum(weights.values())
        if total == 0:
            return {k: 1.0 / len(weights) for k in weights}
        return {k: v / total for k, v in weights.items()}
    
    @staticmethod
    def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp value to range"""
        return max(min_val, min(value, max_val))
    
    def _normalize_score(self, score: float, min_conf: float = None) -> float:
        """
        Normalize score to valid range.
        
        Args:
            score: Raw score value
            min_conf: Minimum confidence floor (from config if None)
        
        Returns:
            Normalized score (0-1)
        """
        if min_conf is None:
            min_conf = self.config.get("normalization", {}).get("min_confidence", 0.1)
        
        max_conf = self.config.get("normalization", {}).get("max_confidence", 1.0)
        
        # Clamp to configured range
        clamped = self._clamp(score, 0.0, max_conf)
        
        # Apply minimum confidence floor
        floored = max(clamped, min_conf) if min_conf > 0 else clamped
        
        return self._clamp(floored, 0.0, max_conf)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Loaded scoring configuration from {config_path}")
                return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return self._default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}. Using defaults.")
            return self._default_config()
    
    @staticmethod
    def _default_config() -> Dict:
        """Get default configuration"""
        return {
            "scoring_weights": {
                "rule_based": 0.4,
                "feedback_based": 0.4,
                "availability": 0.2,
            },
            "score_sources": {
                "rule_based": {
                    "enabled": True,
                    "fallback_weight": 0.5
                },
                "feedback_based": {
                    "enabled": True,
                    "cache_ttl": 30,
                    "fallback_weight": 0.5
                },
                "availability": {
                    "enabled": True,
                    "timeout_threshold": 5.0
                }
            },
            "normalization": {
                "strategy": "min_max",
                "min_confidence": 0.1,
                "max_confidence": 1.0
            },
            "logging": {
                "level": "DEBUG",
                "score_breakdown": True
            }
        }


# Global scoring engine instance
_scoring_engine: Optional[WeightedScoringEngine] = None


def get_scoring_engine() -> WeightedScoringEngine:
    """Get or create scoring engine instance"""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = WeightedScoringEngine()
    return _scoring_engine