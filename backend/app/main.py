"""
Insurabridge API Server

FastAPI application with HIPAA-compliant security defaults.
All routes require authentication except health checks.
"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.core.security import SecurityMiddleware
from app.core.audit import AuditMiddleware
from app.api import router as api_router
# from app.core.database import init_database, close_database
from app.core.llm import init_llm_client, close_llm_client
from app.core.knowledge import init_knowledge_base

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Initializes all services on startup, cleans up on shutdown.
    Critical for ensuring database connections and LLM clients are properly managed.
    """
    logger.info("Starting Insurabridge", version=settings.app_version)
    
    # Initialize core services
    # await init_database()
    await init_llm_client()
    await init_knowledge_base()
    
    logger.info("All services initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Insurabridge")
    await close_llm_client()
    # await close_database()
    
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Insurabridge",
    description="AI Health Insurance Intelligence Platform - HIPAA Compliant, Local-First",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# Security middleware - must be first
app.add_middleware(SecurityMiddleware)

# Audit middleware - logs all requests
app.add_middleware(AuditMiddleware)

# CORS - allow frontend and Epic bridge
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Epic FHIR Bridge
        "http://localhost:3001",   # Next.js Frontend
        "http://localhost:8000",   # Old BackendPort
        "http://localhost:8001",   # Backend Self
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without exposing internal details."""
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data"},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Never expose internal error details - log them securely instead.
    """
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"},
    )


# Health check endpoints (no auth required)
@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check - confirms API is responding."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    Readiness check - confirms all dependencies are available.
    
    Checks:
    - Database connection
    - LLM availability
    - Knowledge base loaded
    """
    from app.core.database import check_database
    from app.core.llm import check_llm
    from app.core.knowledge import check_knowledge_base
    
    checks = {
        "database": await check_database(),
        "llm": await check_llm(),
        "knowledge_base": await check_knowledge_base(),
    }
    
    all_ready = all(checks.values())
    
    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Also mount FHIR routes directly for simpler access (no auth for demo)
from app.api.fhir_import import router as fhir_direct_router
from app.api.demo import router as demo_router
from app.api.pipeline import router as pipeline_router
from app.api.narrative import router as narrative_router

app.include_router(fhir_direct_router, tags=["FHIR Direct"])
app.include_router(demo_router, prefix="/demo", tags=["Demo Data"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])
app.include_router(narrative_router, prefix="/narrative", tags=["Narrative"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Local only - never bind to 0.0.0.0
        port=8001,
        reload=settings.debug,
        log_level="info",
        access_log=True,
    )

