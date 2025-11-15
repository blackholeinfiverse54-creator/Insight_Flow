# app/telemetry_bus/service.py
"""
Telemetry Bus Service

Core service for managing telemetry packet queue and broadcasting.
Implements bounded queue with backpressure and overflow handling.
"""

import asyncio
import logging
import time
from typing import Set, Optional
from collections import deque
from datetime import datetime
from fastapi import WebSocket

from app.telemetry_bus.models import TelemetryPacket, HealthResponse, DecisionPayload, TracePayload, LegacyTelemetryPacket, LegacyDecisionPayload
from app.core.config import settings

logger = logging.getLogger(__name__)


class TelemetryBusService:
    """
    Telemetry bus service for real-time packet streaming.
    
    Features:
    - Bounded queue with configurable size
    - Backpressure handling (drop oldest on overflow)
    - WebSocket connection management
    - Broadcasting to multiple clients
    - Health metrics tracking
    """
    
    def __init__(
        self,
        max_queue_size: int = 1000,
        max_connections: int = 100
    ):
        """
        Initialize telemetry bus service.
        
        Args:
            max_queue_size: Maximum packets in queue before dropping
            max_connections: Maximum concurrent WebSocket connections
        """
        self.max_queue_size = max_queue_size
        self.max_connections = max_connections
        
        # Packet queue (bounded)
        self._packet_queue: deque = deque(maxlen=max_queue_size)
        
        # Active WebSocket connections
        self._active_connections: Set[WebSocket] = set()
        
        # Metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_dropped": 0,
            "total_connections": 0,
        }
        
        # Start time for uptime calculation
        self._start_time = time.time()
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        logger.info(
            f"TelemetryBusService initialized "
            f"(max_queue={max_queue_size}, max_conn={max_connections})"
        )
    
    async def emit_packet(self, packet: TelemetryPacket):
        """
        Emit telemetry packet to queue and broadcast to clients.
        
        Args:
            packet: Telemetry packet to emit
        """
        async with self._lock:
            # Check if queue is full
            if len(self._packet_queue) >= self.max_queue_size:
                # Drop oldest packet (backpressure)
                dropped = self._packet_queue.popleft()
                self.metrics["messages_dropped"] += 1
                logger.warning(
                    f"Queue full, dropped packet: {dropped.request_id}"
                )
            
            # Add packet to queue
            self._packet_queue.append(packet)
            
            # Broadcast to all connected clients
            await self._broadcast_packet(packet)
    
    async def _broadcast_packet(self, packet: TelemetryPacket):
        """
        Broadcast packet to all connected WebSocket clients.
        
        Args:
            packet: Packet to broadcast
        """
        if not self._active_connections:
            return
        
        # Convert packet to JSON
        packet_json = packet.model_dump_json()
        
        # Send to all clients (remove failed connections)
        disconnected = set()
        
        for websocket in self._active_connections:
            try:
                await websocket.send_text(packet_json)
                self.metrics["messages_sent"] += 1
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        self._active_connections -= disconnected
    
    async def register_connection(self, websocket: WebSocket) -> bool:
        """
        Register new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
        
        Returns:
            True if registered, False if max connections reached
        """
        async with self._lock:
            if len(self._active_connections) >= self.max_connections:
                logger.warning("Max connections reached, rejecting new connection")
                return False
            
            self._active_connections.add(websocket)
            self.metrics["total_connections"] += 1
            
            logger.info(
                f"WebSocket registered (active: {len(self._active_connections)})"
            )
            return True
    
    async def unregister_connection(self, websocket: WebSocket):
        """
        Unregister WebSocket connection.
        
        Args:
            websocket: WebSocket connection to unregister
        """
        async with self._lock:
            self._active_connections.discard(websocket)
            logger.info(
                f"WebSocket unregistered (active: {len(self._active_connections)})"
            )
    
    def get_health(self) -> HealthResponse:
        """
        Get health status and metrics.
        
        Returns:
            HealthResponse with current status
        """
        uptime = time.time() - self._start_time
        
        return HealthResponse(
            status="ok",
            queue_size=len(self._packet_queue),
            max_queue_size=self.max_queue_size,
            active_connections=len(self._active_connections),
            messages_sent=self.metrics["messages_sent"],
            messages_dropped=self.metrics["messages_dropped"],
            uptime_seconds=uptime
        )
    
    async def get_recent_packets(self, limit: int = 100) -> list:
        """
        Get recent packets from queue.
        
        Args:
            limit: Maximum number of packets to return
        
        Returns:
            List of recent packets
        """
        async with self._lock:
            recent = list(self._packet_queue)[-limit:]
            return [p.model_dump() for p in recent]
    
    # Legacy compatibility methods
    async def connect(self, websocket: WebSocket):
        """Legacy method for backward compatibility"""
        await websocket.accept()
        success = await self.register_connection(websocket)
        if not success:
            await websocket.close(code=1013, reason="Max connections reached")
    
    def disconnect(self, websocket: WebSocket):
        """Legacy method for backward compatibility"""
        asyncio.create_task(self.unregister_connection(websocket))
    
    async def broadcast_decision(self, decision_data: dict):
        """Legacy broadcast method for backward compatibility"""
        try:
            # Create enhanced telemetry packet
            decision_payload = DecisionPayload(
                selected_agent=decision_data.get("agent_id", "unknown"),
                alternatives=decision_data.get("alternatives", []),
                confidence=min(1.0, max(0.0, decision_data.get("confidence_score", 0.0))),
                latency_ms=max(0.0, decision_data.get("execution_time_ms", 0.0)),
                strategy=decision_data.get("routing_strategy", "weighted_scoring")
            )
            
            trace_payload = TracePayload(
                version=settings.APP_VERSION,
                node="insightflow-router",
                ts=datetime.utcnow().isoformat() + "Z"
            )
            
            packet = TelemetryPacket(
                request_id=decision_data.get("request_id", f"req-{int(datetime.utcnow().timestamp())}"),
                decision=decision_payload,
                trace=trace_payload
            )
            
            await self.emit_packet(packet)
            
        except Exception as e:
            logger.error(f"Legacy broadcast error: {e}")
    
    def get_metrics(self) -> dict:
        """Legacy metrics method for backward compatibility"""
        return {
            "active_connections": len(self._active_connections),
            "total_connections": self.metrics["total_connections"],
            "packets_sent": self.metrics["messages_sent"],
            "messages_dropped": self.metrics["messages_dropped"]
        }


# Global telemetry service instance
_telemetry_service: Optional[TelemetryBusService] = None


def get_telemetry_service() -> TelemetryBusService:
    """
    Get or create global telemetry service instance.
    
    Returns:
        TelemetryBusService instance
    """
    global _telemetry_service
    
    if _telemetry_service is None:
        _telemetry_service = TelemetryBusService(
            max_queue_size=getattr(settings, 'TELEMETRY_BUFFER_SIZE', 1000),
            max_connections=100
        )
    
    return _telemetry_service


# Legacy compatibility - maintain old service instance
telemetry_service = get_telemetry_service()