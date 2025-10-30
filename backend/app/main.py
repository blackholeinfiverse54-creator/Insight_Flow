from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.database import init_database
from app.routers import routing, agents, analytics, websocket, auth, migration
from app.api.v1 import routing as routing_v1
from app.api.v2 import routing as routing_v2
from app.api.routes import admin
from app.api.routes import dashboard as dashboard_routes
from app.api.middleware.version_detector import detect_api_version, add_version_headers
from app.middleware.migration_middleware import MigrationMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    await init_database()
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Adaptive Decision Intelligence Engine for AI Agent Routing",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add migration middleware
app.add_middleware(MigrationMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(migration.router)  # Migration management
app.include_router(routing.router)  # Legacy routing (will be deprecated)
app.include_router(routing_v1.router)  # API v1 - Legacy format
app.include_router(routing_v2.router)  # API v2 - Enhanced with migration features
app.include_router(agents.router)
app.include_router(analytics.router)
app.include_router(websocket.router)
app.include_router(admin.router)  # Admin endpoints for logging and monitoring
app.include_router(dashboard_routes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.core.dependencies import get_feedback_service
    
    # Check feedback service health
    feedback_service = get_feedback_service()
    feedback_healthy = await feedback_service.health_check()
    
    return {
        "status": "healthy" if feedback_healthy else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "feedback_service": "healthy" if feedback_healthy else "unhealthy"
        }
    }


@app.get("/health/ksml")
async def ksml_health_check():
    """KSML-formatted health check endpoint"""
    from app.services.ksml_service import ksml_service
    
    health_data = {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "ksml_adapter": "active",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return ksml_service.create_health_check(health_data)


@app.get("/api/version")
async def get_api_version_info():
    """Get API version information and migration details"""
    from app.services.migration_service import migration_service
    
    version_info = {
        "app_version": settings.APP_VERSION,
        "supported_versions": ["v1", "v2"],
        "default_version": "v1",
        "recommended_version": "v2",
        "migration_timeline": {
            "deprecation_date": migration_service.deprecation_date.isoformat(),
            "removal_date": migration_service.removal_date.isoformat(),
            "days_until_removal": (migration_service.removal_date - datetime.utcnow()).days
        },
        "endpoints": {
            "v1": {
                "routing": "/api/v1/routing/route",
                "feedback": "/api/v1/routing/feedback",
                "status": "deprecated"
            },
            "v2": {
                "routing": "/api/v2/routing/route",
                "batch_routing": "/api/v2/routing/batch",
                "ksml_routing": "/api/v2/routing/ksml/route",
                "feedback": "/api/v2/routing/feedback",
                "status": "active"
            },
            "migration": {
                "status": "/api/migration/status",
                "guide": "/api/migration/guide",
                "analytics": "/api/migration/analytics"
            },
            "admin": {
                "routing_logs": "/admin/routing-logs",
                "routing_statistics": "/admin/routing-statistics",
                "cleanup_logs": "/admin/cleanup-logs",
                "system_health": "/admin/system-health",
                "status": "active"
            },
            "dashboard": {
                "performance": "/dashboard/metrics/performance",
                "accuracy": "/dashboard/metrics/accuracy",
                "agents": "/dashboard/metrics/agents",
                "status": "active"
            }
        },
        "migration_resources": {
            "guide": "/docs/MIGRATION_GUIDE.md",
            "api_docs": "/docs",
            "support": "support@insightflow.ai"
        }
    }
    
    return version_info


@app.get("/test")
async def test_endpoint():
    """Simple test endpoint without authentication"""
    return {
        "message": "Test endpoint working!",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/feedback/metrics")
async def get_feedback_metrics():
    """Get feedback service metrics"""
    from app.core.dependencies import get_feedback_service
    
    feedback_service = get_feedback_service()
    metrics = feedback_service.get_metrics()
    
    return {
        "feedback_service_metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/scoring/weights")
async def get_scoring_weights():
    """Get current scoring weights configuration"""
    from app.ml.weighted_scoring import get_scoring_engine
    
    scoring_engine = get_scoring_engine()
    
    return {
        "scoring_weights": scoring_engine.weights,
        "config": scoring_engine.config,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/route-agent/test")
async def test_route_agent():
    """Test endpoint for route-agent functionality"""
    return {
        "message": "Route-agent endpoint available",
        "endpoint": "/api/v1/routing/route-agent",
        "methods": ["POST"],
        "features": [
            "Weighted scoring engine",
            "v1/v2 format support",
            "Confidence thresholds",
            "Alternative agents",
            "Score breakdown",
            "Decision logging"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/routing/decisions")
async def get_routing_decisions(
    agent_id: str = None,
    limit: int = 50
):
    """Get routing decision logs"""
    from app.utils.routing_decision_logger import get_routing_logger
    
    routing_logger = get_routing_logger()
    decisions = routing_logger.query_decisions(
        agent_id=agent_id,
        limit=limit
    )
    
    return {
        "decisions": decisions,
        "count": len(decisions),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/routing/statistics")
async def get_routing_statistics(
    agent_id: str = None
):
    """Get routing decision statistics"""
    from app.utils.routing_decision_logger import get_routing_logger
    
    routing_logger = get_routing_logger()
    stats = routing_logger.get_statistics(agent_id=agent_id)
    
    return {
        "statistics": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )