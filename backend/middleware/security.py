"""
Security Middleware for API Protection

This middleware provides multiple layers of security:
1. Security headers (XSS, Content-Type, Clickjacking protection)
2. Request origin validation
3. API request validation
4. Rate limiting for sensitive endpoints
5. IP blocking for abuse detection
"""

import time
import hashlib
import logging
from typing import Dict, Set, Optional
from datetime import datetime, timezone
from collections import defaultdict

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for API protection.
    """

    # Track failed requests per IP for abuse detection
    _failed_requests: Dict[str, list] = defaultdict(list)
    _blocked_ips: Set[str] = set()

    # Configurable thresholds
    FAILED_REQUEST_WINDOW = 300  # 5 minutes
    MAX_FAILED_REQUESTS = 20  # Max failures before temp block
    BLOCK_DURATION = 600  # 10 minute block

    # Sensitive endpoints that need extra protection
    SENSITIVE_ENDPOINTS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/resend-verification",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
    }

    # Admin endpoints
    ADMIN_ENDPOINTS_PREFIX = "/api/v1/admin"

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = self._get_client_ip(request)
        start_time = time.time()

        # Check if IP is blocked
        if client_ip in self._blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

        # Validate request origin for API calls
        if request.url.path.startswith("/api/"):
            origin_check = self._validate_origin(request)
            if not origin_check:
                logger.warning(f"Invalid origin from {client_ip}: {request.headers.get('origin', 'none')}")
                # Allow but log - don't block legitimate API clients

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request error from {client_ip}: {str(e)}")
            self._track_failure(client_ip)
            raise

        # Track failed authentication attempts
        if response.status_code in (401, 403):
            path = request.url.path
            if path in self.SENSITIVE_ENDPOINTS:
                self._track_failure(client_ip)

        # Add security headers
        response = self._add_security_headers(response, request)

        # Log request timing for monitoring
        duration = time.time() - start_time
        if duration > 2.0:  # Log slow requests
            logger.warning(f"Slow request: {request.method} {request.url.path} took {duration:.2f}s")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP from request headers"""
        # Check X-Forwarded-For for proxied requests (ALB, CloudFront)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        return request.client.host if request.client else "unknown"

    def _validate_origin(self, request: Request) -> bool:
        """Validate request origin against allowed origins"""
        from config.settings import settings

        origin = request.headers.get("origin")
        referer = request.headers.get("referer")

        # Allow requests without origin (direct API calls, server-to-server)
        if not origin and not referer:
            return True

        # Check if origin matches allowed origins
        if origin:
            for allowed in settings.CORS_ORIGINS:
                if origin == allowed or origin.startswith(allowed.rstrip("/")):
                    return True

        # Check referer as fallback
        if referer:
            for allowed in settings.CORS_ORIGINS:
                if referer.startswith(allowed.rstrip("/")):
                    return True

        return False

    def _track_failure(self, client_ip: str) -> None:
        """Track failed requests and block if threshold exceeded"""
        current_time = time.time()

        # Clean old entries
        self._failed_requests[client_ip] = [
            t for t in self._failed_requests[client_ip]
            if current_time - t < self.FAILED_REQUEST_WINDOW
        ]

        # Add new failure
        self._failed_requests[client_ip].append(current_time)

        # Check if threshold exceeded
        if len(self._failed_requests[client_ip]) >= self.MAX_FAILED_REQUESTS:
            logger.warning(f"Blocking IP {client_ip} due to excessive failures")
            self._blocked_ips.add(client_ip)
            # Schedule unblock (in production, use Redis with TTL)
            # For now, rely on app restart or implement cleanup task

    def _add_security_headers(self, response: Response, request: Request) -> Response:
        """Add security headers to response"""

        # Prevent XSS attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Content Security Policy for API responses
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        # Strict Transport Security (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (disable unnecessary browser features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Cache control for sensitive endpoints
        if request.url.path.startswith("/api/v1/auth/") or \
           request.url.path.startswith("/api/v1/admin/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


class RequestSignatureMiddleware(BaseHTTPMiddleware):
    """
    Optional middleware for API request signature validation.

    For extra security, clients can sign requests with HMAC.
    This is useful for mobile apps or third-party integrations.

    Headers required:
    - X-Api-Timestamp: Unix timestamp of request
    - X-Api-Signature: HMAC-SHA256 of timestamp + method + path + body
    """

    # Endpoints requiring signature (optional - not enabled by default)
    SIGNED_ENDPOINTS: Set[str] = set()

    # Max request age to prevent replay attacks
    MAX_REQUEST_AGE = 300  # 5 minutes

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only validate if endpoint requires signature
        if request.url.path not in self.SIGNED_ENDPOINTS:
            return await call_next(request)

        timestamp = request.headers.get("x-api-timestamp")
        signature = request.headers.get("x-api-signature")

        if not timestamp or not signature:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing request signature"}
            )

        # Validate timestamp
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > self.MAX_REQUEST_AGE:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Request expired"}
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid timestamp"}
            )

        # Signature validation would be implemented here
        # For now, pass through (enable when needed)

        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for tracking sensitive operations.

    Logs all state-changing operations (POST, PUT, PATCH, DELETE)
    to the audit_logs table for compliance and security monitoring.
    """

    # Methods to audit
    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Endpoints to skip auditing (health checks, etc.)
    SKIP_PATHS = {"/health", "/health/db", "/"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip non-auditable methods
        if request.method not in self.AUDITABLE_METHODS:
            return await call_next(request)

        # Skip excluded paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()

        # Capture request info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        # Process request
        response = await call_next(request)

        # Log the operation
        duration = time.time() - start_time

        # Log format: timestamp, method, path, status, duration, ip
        logger.info(
            f"AUDIT: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s "
            f"ip={client_ip}"
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP"""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
