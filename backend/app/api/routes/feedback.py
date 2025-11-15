# app/api/routes/feedback.py
"""
Feedback Endpoint

Consumes STP feedback from behavioral service.
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.stp_bridge.stp_bridge_integration import get_stp_bridge
from app.ml.q_learning_updater import get_q_updater

logger = logging.getLogger(__name__)

feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


@feedback_router.post("")
async def receive_feedback(payload: Dict[str, Any]):
    """
    Receive STP feedback from behavioral service.
    
    Endpoint: POST /feedback
    
    Request body:
    {
        "karmic_weight": 0.34,
        "reward_value": 0.5,
        "context_tags": ["discipline", "consistency"],
        "stp_version": "stp-1"
    }
    
    Response:
    {
        "status": "accepted",
        "parsed_reward": 0.5,
        "context_tags": ["discipline", "consistency"]
    }
    """
    try:
        # Get STP bridge
        stp_bridge = get_stp_bridge(enable_feedback=True)
        
        # Parse feedback
        parsed_feedback = stp_bridge.parse_stp_feedback(payload)
        
        logger.info(
            f"Received STP feedback: reward={parsed_feedback.reward:.2f}, "
            f"tags={parsed_feedback.context_tags}"
        )
        
        # Trigger Q-learning update
        try:
            from app.core.config import settings
            
            if getattr(settings, 'ENABLE_Q_UPDATES', False):
                q_updater = get_q_updater()
                
                # Extract state and action from payload
                # (In real implementation, these would come from context)
                state = payload.get("state", "default")
                action = payload.get("action", "unknown")
                request_id = payload.get("request_id", "unknown")
                
                # Perform Q-update
                old_conf, new_conf = q_updater.q_update(
                    state=state,
                    action=action,
                    reward=parsed_feedback.reward,
                    request_id=request_id
                )
                
                logger.info(
                    f"Q-update performed: {old_conf:.3f} → {new_conf:.3f}"
                )
        
        except Exception as e:
            logger.error(f"Error in Q-update: {str(e)}")
        
        return {
            "status": "accepted",
            "parsed_reward": parsed_feedback.reward,
            "context_tags": parsed_feedback.context_tags,
            "weights": parsed_feedback.weights
        }
    
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process feedback: {str(e)}"
        )