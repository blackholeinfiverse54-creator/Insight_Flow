from typing import Dict, List, Tuple, Optional
from app.services.agent_service import AgentService
from app.services.q_learning import q_learning_router
from app.core.dependencies import get_feedback_service
from app.ml.weighted_scoring import get_scoring_engine
from app.core.database import get_db
from app.services.stp_service import get_stp_service
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Core routing decision engine"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.feedback_score_service = get_feedback_service()
        self.scoring_engine = get_scoring_engine()
        self.stp_service = get_stp_service()
    
    async def route_request(
        self,
        input_data: Dict,
        input_type: str,
        context: Dict = None,
        strategy: str = "q_learning"
    ) -> Dict:
        """
        Route request to appropriate agent
        
        Args:
            input_data: Input data dictionary
            input_type: Type of input (text, audio, image, etc.)
            context: Additional context information
            strategy: Routing strategy (rule_based, semantic, q_learning)
            
        Returns:
            Routing decision dictionary
        """
        request_id = str(uuid.uuid4())
        context = context or {}
        context["input_type"] = input_type
        
        logger.info(f"Routing request {request_id} with strategy '{strategy}'")
        
        # Get available agents with feedback scores
        try:
            available_agents = await self.agent_service.get_active_agents(include_feedback_scores=True)
        except Exception as e:
            logger.error(f"Failed to get active agents: {e}")
            raise
        
        if not available_agents:
            raise ValueError("No active agents available for routing")
        
        # Select routing strategy
        if strategy == "rule_based":
            agent_id, confidence, reason = await self._route_rule_based(
                input_type, available_agents, context
            )
        elif strategy == "semantic":
            agent_id, confidence, reason = await self._route_semantic(
                input_data, available_agents, context
            )
        elif strategy == "q_learning":
            agent_id, confidence, reason = await self._route_q_learning(
                available_agents, context
            )
        else:
            # Default to rule-based
            agent_id, confidence, reason = await self._route_rule_based(
                input_type, available_agents, context
            )
        
        # Get agent details
        try:
            agent = await self.agent_service.get_agent_by_id(agent_id)
            if not agent:
                raise ValueError(f"Selected agent {agent_id} not found")
        except Exception as e:
            logger.error(f"Failed to get agent details: {e}")
            raise
        
        # Create routing log
        valid_statuses = ["pending", "processing", "completed", "failed"]
        try:
            routing_log = {
                "id": str(uuid.uuid4()),
                "request_id": request_id,
                "user_id": context.get("user_id"),
                "input_type": input_type,
                "input_data": input_data,
                "selected_agent_id": agent_id,
                "agent_name": agent.get("name"),
                "confidence_score": confidence,
                "routing_reason": reason,
                "routing_strategy": strategy,
                "status": "pending" if "pending" in valid_statuses else "failed",
                "context": context,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to create routing log: {e}")
            raise ValueError("Failed to create routing log with valid status")
        
        # Save to database
        try:
            db = get_db()
            db.table("routing_logs").insert(routing_log).execute()
        except Exception as e:
            logger.error(f"Failed to save routing log: {e}")
            raise
        
        logger.info(f"Routed request {request_id} to agent {agent_id} "
                   f"(confidence: {confidence:.3f})")
        
        # Log decision with routing decision logger
        from app.utils.routing_decision_logger import get_routing_logger
        
        routing_logger = get_routing_logger()
        routing_logger.log_decision(
            agent_selected=agent_id,
            confidence_score=confidence,
            request_id=request_id,
            context=context,
            reasoning=reason
        )
        
        # Create routing decision response
        routing_decision = {
            "request_id": request_id,
            "routing_log_id": routing_log["id"],
            "agent_id": agent_id,
            "agent_name": agent.get("name"),
            "agent_type": agent.get("type"),
            "confidence_score": confidence,
            "routing_reason": reason,
            "routing_strategy": strategy
        }
        
        # Wrap in STP format if enabled (maintains backward compatibility)
        try:
            wrapped_decision = await self.stp_service.wrap_routing_decision(
                routing_decision=routing_decision,
                requires_ack=context.get("requires_ack", False)
            )
            return wrapped_decision
        except Exception as e:
            logger.warning(f"STP wrapping failed, returning unwrapped: {e}")
            return routing_decision
    
    async def _route_rule_based(
        self,
        input_type: str,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Rule-based routing logic with feedback score integration"""
        
        # Map input types to agent types
        type_mapping = {
            "text": "nlp",
            "audio": "tts",
            "image": "computer_vision",
            "video": "computer_vision"
        }
        
        preferred_type = type_mapping.get(input_type, "general")
        
        # Get agent IDs for feedback score lookup
        agent_ids = [agent["id"] for agent in agents if agent.get("id")]
        
        # Fetch real-time feedback scores
        try:
            feedback_scores = await self.feedback_score_service.get_agent_scores(agent_ids)
            logger.info(f"Retrieved feedback scores for {len(feedback_scores)} agents")
        except Exception as e:
            logger.warning(f"Failed to get feedback scores: {e}")
            feedback_scores = {}
        
        # Score agents using weighted scoring engine
        scored_agents = []
        for agent in agents:
            if not agent.get("id"):
                continue
            
            agent_id = agent["id"]
            
            # Calculate rule-based score
            rule_score = 0.0
            if agent["type"] == preferred_type:
                rule_score += 0.5
            rule_score += agent.get("performance_score", 0.5) * 0.3
            rule_score += agent.get("success_rate", 0.5) * 0.2
            
            # Get feedback score
            feedback_score = feedback_scores.get(agent_id, 0.5)
            
            # Calculate availability score (based on agent status and health)
            availability_score = 1.0 if agent.get("status") == "active" else 0.3
            
            # Use weighted scoring engine for final confidence
            confidence_result = self.scoring_engine.calculate_confidence(
                agent_id=agent_id,
                rule_based_score=rule_score,
                feedback_score=feedback_score,
                availability_score=availability_score
            )
            
            scored_agents.append((agent_id, confidence_result))
        
        if not scored_agents:
            raise ValueError("No valid agents available for rule-based routing")
        
        # Select agent with highest confidence score
        best_agent_id, best_confidence = max(scored_agents, key=lambda x: x[1].final_score)
        
        reason = f"Weighted scoring: {input_type} match (confidence: {best_confidence.final_score:.2f})"
        
        return best_agent_id, best_confidence.final_score, reason
    
    async def _route_semantic(
        self,
        input_data: Dict,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Semantic routing using NLP embeddings"""
        
        # Simplified semantic routing
        # In production, use actual embeddings and similarity search
        
        text_content = input_data.get("text", "")
        
        # Score agents based on capability tags
        scored_agents = []
        for agent in agents:
            if not agent.get("id"):
                continue
            score = agent.get("performance_score", 0.5)
            
            # Check capability match (simplified)
            tags = agent.get("tags", [])
            for tag in tags:
                if tag.lower() in text_content.lower():
                    score += 0.2
            
            scored_agents.append((agent["id"], min(1.0, score)))
        
        if not scored_agents:
            raise ValueError("No valid agents available for semantic routing")
        
        best_agent_id, best_score = max(scored_agents, key=lambda x: x[1])
        
        reason = "Semantic: High capability match for input content"
        
        return best_agent_id, best_score, reason
    
    async def _route_q_learning(
        self,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Q-learning based routing"""
        
        agent_ids = [agent["id"] for agent in agents if agent.get("id")]
        
        if not agent_ids:
            raise ValueError("No valid agents available for Q-learning routing")
        
        # Use Q-learning router
        try:
            selected_agent_id, confidence = q_learning_router.select_agent(
                available_agents=agent_ids,
                context=context,
                explore=True
            )
        except Exception as e:
            logger.error(f"Q-learning routing failed: {e}")
            raise
        
        reason = "Q-Learning: Optimal agent based on learned policy"
        
        return selected_agent_id, confidence, reason
    
    async def process_feedback(
        self,
        routing_log_id: str,
        feedback_data: Dict
    ):
        """
        Process feedback for a routing decision
        
        Args:
            routing_log_id: ID of routing log
            feedback_data: Feedback data
        """
        db = get_db()
        
        try:
            # Get routing log
            routing_log = db.table("routing_logs").select("*").eq("id", routing_log_id).execute()
            
            if not routing_log.data:
                raise ValueError(f"Routing log {routing_log_id} not found")
            
            log_data = routing_log.data[0]
            
            # Update routing log status
            status = "success" if feedback_data.get("success") else "failed"
            db.table("routing_logs").update({
                "status": status,
                "execution_time_ms": feedback_data.get("latency_ms"),
                "response_data": feedback_data.get("response_data")
            }).eq("id", routing_log_id).execute()
            
            # Save feedback
            feedback_record = {
                "id": str(uuid.uuid4()),
                "routing_log_id": routing_log_id,
                "agent_id": log_data["selected_agent_id"],
                "feedback_type": "success" if feedback_data.get("success") else "failure",
                "success": feedback_data.get("success", False),
                "latency_ms": feedback_data.get("latency_ms", 0),
                "accuracy_score": feedback_data.get("accuracy_score"),
                "user_satisfaction": feedback_data.get("user_satisfaction"),
                "metadata": feedback_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            db.table("feedback_events").insert(feedback_record).execute()
            
            # Wrap feedback in STP format for external systems
            try:
                wrapped_feedback = await self.stp_service.wrap_feedback_packet(
                    feedback_data=feedback_record,
                    requires_ack=True
                )
                logger.debug(f"Feedback wrapped in STP format: {wrapped_feedback.get('stp_token')}")
            except Exception as stp_error:
                logger.warning(f"STP feedback wrapping failed: {stp_error}")
                
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
        
        # Update agent performance
        try:
            await self.agent_service.update_agent_performance(
                agent_id=log_data["selected_agent_id"],
                success=feedback_data.get("success", False),
                latency_ms=feedback_data.get("latency_ms", 0)
            )
        except Exception as e:
            logger.error(f"Failed to update agent performance: {e}")
        
        # Update Q-learning if strategy was q_learning
        if log_data.get("routing_strategy") == "q_learning":
            try:
                available_agents = await self.agent_service.get_active_agents()
                agent_ids = [agent["id"] for agent in available_agents]
                
                q_learning_router.process_feedback(
                    routing_log_id=routing_log_id,
                    feedback=feedback_record,
                    context=log_data.get("context", {}),
                    available_agents=agent_ids
                )
            except Exception as e:
                logger.error(f"Failed to update Q-learning: {e}")
        
        logger.info(f"Processed feedback for routing {routing_log_id}")


# Global decision engine instance
decision_engine = DecisionEngine()