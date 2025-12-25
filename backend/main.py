"""
Mathvidya API - Main Application Entry Point

This is the main FastAPI application file that initializes the API server,
configures middleware, and includes all route modules.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from database import engine
from routes import auth, exams, questions, evaluations, analytics, subscriptions, notifications

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events

    Startup: Initialize connections, start background tasks
    Shutdown: Clean up resources
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    description="CBSE Mathematics Practice Platform - Backend API",
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    # Convert body to string if it's bytes (e.g., from form-urlencoded requests)
    body = exc.body
    if isinstance(body, bytes):
        body = body.decode('utf-8', errors='replace')
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": body
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error for {request.url}: {str(exc)}", exc_info=True)

    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


# Include Routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(exams.router, prefix="/api/v1", tags=["Exams"])
app.include_router(questions.router, prefix="/api/v1", tags=["Questions"])
app.include_router(evaluations.router, prefix="/api/v1", tags=["Evaluations"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics & Reports"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["Subscriptions"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Mathvidya API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/health/db", tags=["Health"])
async def database_health():
    """Database connection health check"""
    try:
        from database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e) if settings.DEBUG else "Database connection failed"
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
