"""
Health Check Endpoints
System health monitoring
"""

from fastapi import APIRouter
from datetime import datetime
import structlog

from app.core.config import settings
from app.core.database import check_db_health

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check - API is responding."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/db")
async def database_health():
    """Check database connectivity."""
    db_healthy = await check_db_health()
    
    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/llm")
async def llm_health():
    """Check local LLM service connectivity."""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.LLM_SERVICE_URL}/health")
            llm_healthy = response.status_code == 200
    except Exception as e:
        logger.warning("LLM health check failed", error=str(e))
        llm_healthy = False
    
    return {
        "llm_service": "healthy" if llm_healthy else "unhealthy",
        "url": settings.LLM_SERVICE_URL,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Comprehensive readiness check.
    
    Checks all dependencies before accepting traffic.
    """
    checks = {
        "database": await check_db_health(),
    }
    
    # Check LLM service
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.LLM_SERVICE_URL}/health")
            checks["llm_service"] = response.status_code == 200
    except Exception:
        checks["llm_service"] = False
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
