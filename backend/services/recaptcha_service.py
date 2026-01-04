"""
reCAPTCHA v3 Verification Service

Verifies reCAPTCHA tokens with Google's API.
"""

import httpx
import logging
from typing import Optional, Tuple

from config.settings import settings

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


async def verify_recaptcha(token: str, expected_action: str = None) -> Tuple[bool, float, str]:
    """
    Verify a reCAPTCHA v3 token with Google's API.

    Args:
        token: The reCAPTCHA token from the frontend
        expected_action: The expected action name (e.g., 'login', 'register')

    Returns:
        Tuple of (is_valid, score, error_message)
        - is_valid: True if verification passed
        - score: The risk score (0.0 to 1.0, higher = more likely human)
        - error_message: Error description if failed, empty string if success
    """
    # Skip verification if disabled or no secret key configured
    if not settings.RECAPTCHA_ENABLED:
        logger.debug("reCAPTCHA verification disabled")
        return True, 1.0, ""

    if not settings.RECAPTCHA_SECRET_KEY:
        logger.warning("reCAPTCHA secret key not configured - skipping verification")
        return True, 1.0, ""

    if not token:
        logger.warning("No reCAPTCHA token provided")
        return False, 0.0, "reCAPTCHA verification required"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": token,
                },
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"reCAPTCHA API error: HTTP {response.status_code}")
                # Allow request to proceed on API error (fail open)
                return True, 1.0, ""

            result = response.json()
            logger.debug(f"reCAPTCHA response: {result}")

            # Check if verification was successful
            if not result.get("success"):
                error_codes = result.get("error-codes", [])
                logger.warning(f"reCAPTCHA verification failed: {error_codes}")
                return False, 0.0, f"reCAPTCHA verification failed: {', '.join(error_codes)}"

            score = result.get("score", 0.0)
            action = result.get("action", "")

            # Verify action matches (if specified)
            if expected_action and action != expected_action:
                logger.warning(f"reCAPTCHA action mismatch: expected '{expected_action}', got '{action}'")
                # Don't fail on action mismatch, but log it
                pass

            # Check score against threshold
            if score < settings.RECAPTCHA_MIN_SCORE:
                logger.warning(f"reCAPTCHA score too low: {score} < {settings.RECAPTCHA_MIN_SCORE}")
                return False, score, f"Verification failed. Please try again."

            logger.info(f"reCAPTCHA verification passed: score={score}, action={action}")
            return True, score, ""

    except httpx.TimeoutException:
        logger.error("reCAPTCHA API timeout")
        # Allow request to proceed on timeout (fail open)
        return True, 1.0, ""
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {str(e)}")
        # Allow request to proceed on error (fail open for availability)
        return True, 1.0, ""


def get_recaptcha_token_from_request(request) -> Optional[str]:
    """
    Extract reCAPTCHA token from request headers.

    Args:
        request: FastAPI Request object

    Returns:
        The token string or None if not present
    """
    return request.headers.get("X-Recaptcha-Token")
