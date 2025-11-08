# app/services/stp_service.py
"""
STP Service Integration

Integrates STP middleware with InsightFlow routing and feedback systems.
Provides high-level STP operations for routing decisions and feedback packets.
"""

import logging
from typing import Dict, Any, Optional
from app.middleware.stp_middleware import get_stp_middleware, STPPacketType, STPPriority
from app.core.config import settings

logger = logging.getLogger(__name__)


class STPService:
    """
    Service layer for STP operations.
    
    Provides high-level methods for wrapping routing decisions and feedback
    packets in STP format while maintaining backward compatibility.
    """
    
    def __init__(self):
        """Initialize STP service with configuration from settings"""
        self.stp_middleware = get_stp_middleware(enable_stp=settings.STP_ENABLED)
        self.default_destination = settings.STP_DESTINATION
        self.default_priority = settings.STP_DEFAULT_PRIORITY
        self.default_require_ack = settings.STP_REQUIRE_ACK
        
        logger.info(
            f"STPService initialized (enabled={settings.STP_ENABLED}, "
            f"destination={self.default_destination}, require_ack={self.default_require_ack})"
        )
    
    async def wrap_routing_decision(
        self,
        routing_decision: Dict[str, Any],
        priority: str = None,
        destination: str = None,
        requires_ack: bool = None
    ) -> Dict[str, Any]:
        """
        Wrap routing decision in STP format.
        
        Args:
            routing_decision: Original routing decision data
            priority: STP priority (normal/high/critical)
            destination: Target system
            requires_ack: Whether acknowledgment is required
        
        Returns:
            STP-wrapped routing decision
        """
        try:
            # Determine priority based on confidence score
            if priority is None:
                confidence = routing_decision.get("confidence_score", 0.5)
                if confidence >= 0.9:
                    priority = STPPriority.HIGH.value
                elif confidence <= 0.3:
                    priority = STPPriority.CRITICAL.value
                else:
                    priority = self.default_priority
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=routing_decision,
                packet_type=STPPacketType.ROUTING_DECISION.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=requires_ack if requires_ack is not None else self.default_require_ack
            )
            
            logger.debug(
                f"Wrapped routing decision: {routing_decision.get('request_id')} "
                f"-> {wrapped_packet.get('stp_token')}"
            )
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap routing decision: {str(e)}")
            # Return original data on failure to maintain compatibility
            return routing_decision
    
    async def wrap_feedback_packet(
        self,
        feedback_data: Dict[str, Any],
        priority: str = None,
        destination: str = None,
        requires_ack: bool = None
    ) -> Dict[str, Any]:
        """
        Wrap feedback data in STP format.
        
        Args:
            feedback_data: Original feedback data
            priority: STP priority (normal/high/critical)
            destination: Target system
            requires_ack: Whether acknowledgment is required (default True for feedback)
        
        Returns:
            STP-wrapped feedback packet
        """
        try:
            # Determine priority based on feedback success and metrics
            if priority is None:
                success = feedback_data.get("success", True)
                latency = feedback_data.get("latency_ms", 0)
                
                if not success or latency > 5000:  # Failed or very slow
                    priority = STPPriority.CRITICAL.value
                elif latency > 1000:  # Slow response
                    priority = STPPriority.HIGH.value
                else:
                    priority = self.default_priority
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=feedback_data,
                packet_type=STPPacketType.FEEDBACK_PACKET.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=requires_ack if requires_ack is not None else True  # Feedback typically requires ACK
            )
            
            logger.debug(
                f"Wrapped feedback packet: {feedback_data.get('routing_log_id')} "
                f"-> {wrapped_packet.get('stp_token')}"
            )
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap feedback packet: {str(e)}")
            # Return original data on failure to maintain compatibility
            return feedback_data
    
    async def wrap_health_check(
        self,
        health_data: Dict[str, Any],
        priority: str = STPPriority.NORMAL.value,
        destination: str = None
    ) -> Dict[str, Any]:
        """
        Wrap health check data in STP format.
        
        Args:
            health_data: Health check data
            priority: STP priority
            destination: Target system
        
        Returns:
            STP-wrapped health check packet
        """
        try:
            # Adjust priority based on health status
            if health_data.get("status") == "unhealthy":
                priority = STPPriority.CRITICAL.value
            elif health_data.get("status") == "degraded":
                priority = STPPriority.HIGH.value
            
            wrapped_packet = await self.stp_middleware.wrap_async(
                payload=health_data,
                packet_type=STPPacketType.HEALTH_CHECK.value,
                destination=destination or self.default_destination,
                priority=priority,
                requires_ack=False
            )
            
            logger.debug(f"Wrapped health check -> {wrapped_packet.get('stp_token')}")
            
            return wrapped_packet
        
        except Exception as e:
            logger.error(f"Failed to wrap health check: {str(e)}")
            return health_data
    
    async def unwrap_packet(
        self,
        stp_packet: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Unwrap STP packet to extract payload and metadata.
        
        Args:
            stp_packet: STP-wrapped packet
        
        Returns:
            Tuple of (payload, metadata)
        """
        try:
            payload, metadata = await self.stp_middleware.unwrap_async(stp_packet)
            
            logger.debug(
                f"Unwrapped STP packet: {metadata.get('stp_token')} "
                f"(type={metadata.get('stp_type')})"
            )
            
            return payload, metadata
        
        except Exception as e:
            logger.error(f"Failed to unwrap STP packet: {str(e)}")
            # Return original packet as payload with empty metadata on failure
            return stp_packet, {}
    
    def is_stp_packet(self, data: Dict[str, Any]) -> bool:
        """
        Check if data is an STP packet.
        
        Args:
            data: Data to check
        
        Returns:
            True if STP packet, False otherwise
        """
        return self.stp_middleware.validate_stp_packet(data)
    
    def get_stp_metrics(self) -> Dict[str, Any]:
        """
        Get STP middleware metrics.
        
        Returns:
            STP metrics dictionary
        """
        return self.stp_middleware.get_metrics()
    
    def reset_stp_metrics(self):
        """Reset STP metrics counters"""
        self.stp_middleware.reset_metrics()


# Global STP service instance
_stp_service: Optional[STPService] = None


def get_stp_service() -> STPService:
    """
    Get or create STP service singleton.
    
    Returns:
        STPService instance
    """
    global _stp_service
    
    if _stp_service is None:
        _stp_service = STPService()
    
    return _stp_service