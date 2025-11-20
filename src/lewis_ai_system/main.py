"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings
from .routers import creative_router, general_router, governance_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    from .instrumentation import get_logger
    logger = get_logger()
    logger.info(f"Starting Lewis AI System ({settings.environment})")
    
    # Initialize database if configured
    if settings.database_url:
        from .database import init_database
        try:
            await init_database()
            logger.info("Database initialized successfully")
            # Rebind creative repository to the database-backed implementation
            from .creative import repository as creative_repo_module
            creative_repo_module.creative_repository = creative_repo_module.DatabaseCreativeProjectRepository()
            from .creative import workflow as creative_workflow_module
            creative_workflow_module.creative_orchestrator = creative_workflow_module.CreativeOrchestrator(
                repository=creative_repo_module.creative_repository
            )
            from .routers import creative as creative_router_module
            creative_router_module.creative_repository = creative_repo_module.creative_repository
            creative_router_module.creative_orchestrator = creative_workflow_module.creative_orchestrator
            logger.info("Creative repository switched to database backend")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    # Initialize Redis cache
    if settings.redis_enabled:
        from .redis_cache import cache_manager
        try:
            await cache_manager.initialize()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
    
    # Initialize vector database
    try:
        from .vector_db import vector_db
        vector_db.initialize()
        logger.info("Vector database initialized")
    except Exception as e:
        logger.warning(f"Vector DB initialization failed: {e}")
    
    # Initialize S3 storage
    from .s3_storage import s3_storage
    if s3_storage.is_available():
        logger.info("S3 storage configured")
    else:
        logger.warning("S3 storage not configured, using local fallback")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lewis AI System")
    if settings.database_url:
        from .database import db_manager
        await db_manager.close()
    
    # Close Redis cache
    if settings.redis_enabled:
        from .redis_cache import cache_manager
        await cache_manager.close()
    
    # Close vector database
    from .vector_db import vector_db
    await vector_db.close()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware (production security)
if settings.environment == "production":
    hosts = [host.strip() for host in settings.trusted_hosts]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=hosts or ["*"],
    )

# Include routers
app.include_router(creative_router)
app.include_router(general_router)
app.include_router(governance_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure JSON responses."""
    from fastapi.responses import JSONResponse
    from .instrumentation import get_logger
    import traceback
    
    logger = get_logger()
    logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}", exc_info=True)
    
    # Always include traceback in development, and error details in production
    import os
    env = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))
    if env != "production":
        traceback_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "traceback": traceback_str,
                "path": str(request.url.path),
            },
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "error_type": type(exc).__name__,
        },
    )


@app.get("/")
async def root():
    """Basic service metadata."""
    return {
        "message": "Lewis AI System API",
        "version": settings.api_version,
        "docs": "/docs",
    }


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/readyz")
async def readiness_check() -> dict[str, str]:
    """Readiness check for container orchestration."""
    checks = {
        "status": "ready",
        "database": "not_configured",
        "s3": "not_configured",
    }
    
    # Check database
    if settings.database_url:
        try:
            from .database import db_manager
            if db_manager.engine:
                checks["database"] = "connected"
            else:
                checks["database"] = "not_initialized"
        except Exception:
            checks["database"] = "error"
    
    # Check S3
    from .s3_storage import s3_storage
    if s3_storage.is_available():
        checks["s3"] = "configured"
    
    return checks
