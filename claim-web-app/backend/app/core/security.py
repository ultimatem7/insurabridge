"""
Security Middleware and Utilities
HIPAA-conscious security controls
"""

import secrets
import structlog
from typing import Callable
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for HIPAA compliance.
    
    Adds security headers and enforces security policies.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with security headers."""
        
        # Add security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Payload data
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=["HS256"]
        )
        return payload
    except JWTError as e:
        logger.warning("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        User data from token
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    # Extract user info
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return payload


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_state() -> str:
    """Generate secure random state for OAuth."""
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """Generate PKCE code challenge from verifier."""
    import hashlib
    import base64
    
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return challenge


class AuditLogger:
    """Audit logger for HIPAA compliance."""
    
    @staticmethod
    def log_phi_access(
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str | None = None,
    ) -> None:
        """Log PHI access event."""
        logger.info(
            "PHI_ACCESS",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    @staticmethod
    def log_auth_event(
        user_id: str | None,
        event_type: str,
        success: bool,
        ip_address: str | None = None,
    ) -> None:
        """Log authentication event."""
        logger.info(
            "AUTH_EVENT",
            user_id=user_id,
            event_type=event_type,
            success=success,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    @staticmethod
    def log_claim_generation(
        user_id: str,
        encounter_id: str,
        claim_id: str,
        success: bool,
    ) -> None:
        """Log claim generation event."""
        logger.info(
            "CLAIM_GENERATION",
            user_id=user_id,
            encounter_id=encounter_id,
            claim_id=claim_id,
            success=success,
            timestamp=datetime.utcnow().isoformat(),
        )


audit = AuditLogger()
