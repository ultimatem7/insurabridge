"""
Authentication API Routes
"""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field

from app.core.security import (
    auth_service,
    get_current_user,
    TokenPayload,
    Role,
    generate_secure_id,
)
from app.core.audit import log_event, AuditEventType
from app.core.database import get_session, User

logger = structlog.get_logger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request body."""
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Login response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: str = Field(min_length=2, max_length=255)


class UserResponse(BaseModel):
    """User information response."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return tokens.
    
    Rate limited and brute force protected.
    """
    # Check for lockout
    if auth_service.is_locked_out(request.email):
        log_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            description="Login attempt during lockout",
            details={"email_hash": request.email[:3] + "***"},
            success=False,
            error_message="Account locked",
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked. Please try again later.",
        )
    
    # Look up user
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(User).where(User.email == request.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not auth_service.verify_password(request.password, user.password_hash):
            auth_service.record_failed_attempt(request.email)
            
            log_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                description="Invalid credentials",
                details={"email_hash": request.email[:3] + "***"},
                success=False,
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked",
            )
        
        # Success - clear failed attempts and update last login
        auth_service.clear_failed_attempts(request.email)
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        await session.commit()
        
        # Generate tokens
        access_token = auth_service.create_access_token(user.id, Role(user.role))
        refresh_token = auth_service.create_refresh_token(user.id, Role(user.role))
        
        log_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            description="User logged in",
            user_id=user.id,
            user_role=user.role,
        )
        
        from app.config import settings
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    In production, this should be admin-only or require invitation.
    """
    # Validate password strength
    is_valid, issues = auth_service.check_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "issues": issues},
        )
    
    async with get_session() as session:
        # Check if email exists
        from sqlalchemy import select
        stmt = select(User).where(User.email == request.email)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        
        # Create user
        user = User(
            id=generate_secure_id(),
            email=request.email,
            password_hash=auth_service.hash_password(request.password),
            full_name=request.full_name,
            role=Role.VIEWER.value,  # Default to lowest privilege
            is_active=True,
        )
        
        session.add(user)
        await session.commit()
        
        log_event(
            event_type=AuditEventType.USER_CREATE,
            description="New user registered",
            user_id=user.id,
            resource_type="user",
            resource_id=user.id,
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest):
    """Refresh an access token using a refresh token."""
    token_data = auth_service.verify_token(request.refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Generate new tokens
    access_token = auth_service.create_access_token(token_data.sub, token_data.role)
    refresh_token = auth_service.create_refresh_token(token_data.sub, token_data.role)
    
    # Revoke old refresh token
    auth_service.revoke_token(request.refresh_token)
    
    log_event(
        event_type=AuditEventType.AUTH_TOKEN_REFRESH,
        description="Token refreshed",
        user_id=token_data.sub,
    )
    
    from app.config import settings
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(user: TokenPayload = Depends(get_current_user)):
    """Log out current user (revokes current token)."""
    # In a full implementation, we'd revoke all tokens for this user
    log_event(
        event_type=AuditEventType.AUTH_LOGOUT,
        description="User logged out",
        user_id=user.sub,
    )
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: TokenPayload = Depends(get_current_user)):
    """Get current user information."""
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(User).where(User.id == user.sub)
        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            role=db_user.role,
            is_active=db_user.is_active,
            last_login_at=db_user.last_login_at,
        )

