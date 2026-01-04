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
from routes import auth, exams, questions, evaluations, analytics, subscriptions, notifications, admin, teacher, promo, site_feedback, chatbot
from middleware.security import SecurityMiddleware, AuditLogMiddleware

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

# Security Middleware (must be added first to wrap all requests)
# Add security headers and abuse protection
app.add_middleware(SecurityMiddleware)

# Audit logging for state-changing operations
app.add_middleware(AuditLogMiddleware)

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

    # Recursively sanitize - convert any bytes to strings for JSON serialization
    def sanitize(obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(item) for item in obj]
        if isinstance(obj, tuple):
            return tuple(sanitize(item) for item in obj)
        return obj

    errors = sanitize(exc.errors())
    body = sanitize(exc.body) if exc.body else None

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
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
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(teacher.router, prefix="/api/v1/teacher", tags=["Teacher"])
app.include_router(promo.router, prefix="/api/v1", tags=["Promo Codes"])
app.include_router(site_feedback.router, prefix="/api/v1", tags=["Site Feedback"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["Chatbot"])


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
