"""
Authentication API Endpoints
OAuth2 flow with multiple EHR providers
"""

from datetime import datetime, timedelta
from typing import Dict
from fastapi import APIRouter, HTTPException, Query, Depends, Response, Request
from fastapi.responses import RedirectResponse
import structlog

from app.core.config import settings
from app.core.security import create_access_token, generate_state, generate_code_verifier, generate_code_challenge, audit
from app.services.ehr import get_adapter

logger = structlog.get_logger(__name__)

router = APIRouter()


# In-memory state storage (use Redis in production)
_oauth_states: Dict[str, Dict] = {}


@router.get("/providers")
async def list_providers():
    """
    List available EHR providers for authentication.
    
    Returns list of provider configurations for frontend.
    """
    providers = []
    
    # Epic
    if settings.EPIC_CLIENT_ID or settings.ENABLE_MOCK_EHR:
        providers.append({
            "id": "epic",
            "name": "Epic",
            "display_name": "Epic MyChart",
            "logo": "/logos/epic.png",
            "enabled": bool(settings.EPIC_CLIENT_ID) or settings.ENABLE_MOCK_EHR,
        })
    
    # Cerner
    if settings.CERNER_CLIENT_ID or settings.ENABLE_MOCK_EHR:
        providers.append({
            "id": "cerner",
            "name": "Cerner",
            "display_name": "Cerner Health",
            "logo": "/logos/cerner.png",
            "enabled": bool(settings.CERNER_CLIENT_ID) or settings.ENABLE_MOCK_EHR,
        })
    
    # Mock (development)
    if settings.ENABLE_MOCK_EHR:
        providers.append({
            "id": "mock",
            "name": "Mock EHR",
            "display_name": "Mock EHR (Testing)",
            "logo": "/logos/mock.png",
            "enabled": True,
        })
    
    return {"providers": providers}


@router.get("/{provider}/login")
async def initiate_login(provider: str):
    """
    Initiate OAuth2 flow with EHR provider.
    
    Generates authorization URL and redirects user.
    """
    try:
        adapter = get_adapter(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate OAuth state
    state = generate_state()
    
    # Generate PKCE for Epic
    code_verifier = None
    code_challenge = None
    if provider == "epic":
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
    
    # Store state
    _oauth_states[state] = {
        "provider": provider,
        "code_verifier": code_verifier,
        "created_at": datetime.utcnow(),
    }
    
    # Generate authorization URL
    auth_url = adapter.get_authorization_url(
        state=state,
        code_challenge=code_challenge,
    )
    
    logger.info("Initiating OAuth login", provider=provider, state=state)
    audit.log_auth_event(None, "oauth_initiated", True)
    
    return RedirectResponse(url=auth_url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    request: Request = None,
):
    """
    OAuth2 callback endpoint.
    
    Exchanges authorization code for access token and creates session.
    """
    # Validate state
    stored_state = _oauth_states.get(state)
    if not stored_state:
        logger.warning("Invalid OAuth state", state=state)
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Check state expiration (10 minutes)
    if datetime.utcnow() - stored_state["created_at"] > timedelta(minutes=10):
        del _oauth_states[state]
        raise HTTPException(status_code=400, detail="State expired")
    
    # Verify provider matches
    if stored_state["provider"] != provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")
    
    try:
        adapter = get_adapter(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Exchange code for token
    try:
        token_data = await adapter.exchange_code_for_token(
            code=code,
            code_verifier=stored_state.get("code_verifier"),
        )
    except Exception as e:
        logger.error("Token exchange failed", provider=provider, error=str(e))
        audit.log_auth_event(None, "token_exchange_failed", False)
        raise HTTPException(status_code=400, detail="Token exchange failed")
    
    # Clean up state
    del _oauth_states[state]
    
    # Extract token info
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    patient_id = token_data.get("patient")
    expires_in = token_data.get("expires_in", 3600)
    
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")
    
    # Create JWT session token
    session_data = {
        "sub": patient_id or "unknown",
        "provider": provider,
        "patient_id": patient_id,
        "ehr_access_token": access_token,
        "ehr_refresh_token": refresh_token,
        "scope": token_data.get("scope"),
    }
    
    session_token = create_access_token(
        data=session_data,
        expires_delta=timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
    )
    
    logger.info("OAuth callback successful", 
                provider=provider, 
                patient_id=patient_id)
    audit.log_auth_event(patient_id, "oauth_success", True)
    
    # Redirect to frontend with token
    frontend_url = settings.CORS_ORIGINS.split(",")[0]
    redirect_url = f"{frontend_url}/auth/callback?token={session_token}&provider={provider}"
    
    return RedirectResponse(url=redirect_url)


@router.post("/logout")
async def logout():
    """
    End user session.
    
    Invalidates session token.
    """
    # In production, invalidate session in Redis/database
    logger.info("User logged out")
    audit.log_auth_event(None, "logout", True)
    
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(request: Request):
    """
    Check authentication status.
    
    Returns current session info if authenticated.
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False}
    
    token = auth_header.split(" ")[1]
    
    try:
        from app.core.security import verify_token
        payload = verify_token(token)
        
        return {
            "authenticated": True,
            "provider": payload.get("provider"),
            "patient_id": payload.get("patient_id"),
            "expires_at": payload.get("exp"),
        }
    except Exception:
        return {"authenticated": False}
