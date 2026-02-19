"""
Claims API Endpoints
Generate and manage insurance claims
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import structlog
from uuid import uuid4

from app.core.security import get_current_user, audit
from app.services.ehr import get_adapter
from app.services.claims.generator import ClaimGenerator

logger = structlog.get_logger(__name__)

router = APIRouter()

# Initialize claim generator
claim_generator = ClaimGenerator()


@router.post("/generate")
async def generate_claim(
    encounter_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate insurance claim from encounter.
    
    Fetches all encounter data, processes with local LLM,
    and returns structured claim output.
    """
    user_id = current_user.get("sub")
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    logger.info("Starting claim generation", 
                user_id=user_id,
                encounter_id=encounter_id)
    
    try:
        # Fetch encounter data from EHR
        adapter = get_adapter(provider)
        encounter_data = await adapter.fetch_all_encounter_data(
            patient_id,
            encounter_id,
            access_token
        )
        
        if not encounter_data.get("encounter"):
            raise HTTPException(status_code=404, detail="Encounter not found")
        
        audit.log_phi_access(
            user_id=user_id,
            resource_type="Encounter",
            resource_id=encounter_id,
            action="claim_generation",
        )
        
        # Generate claim using local LLM
        claim_data = await claim_generator.generate_claim(
            encounter_data=encounter_data,
            user_id=user_id,
        )
        
        audit.log_claim_generation(
            user_id=user_id,
            encounter_id=encounter_id,
            claim_id=claim_data.get("id"),
            success=True,
        )
        
        logger.info("Claim generated successfully", 
                   claim_id=claim_data.get("id"))
        
        return claim_data
        
    except Exception as e:
        logger.error("Claim generation failed", 
                    error=str(e),
                    encounter_id=encounter_id)
        
        audit.log_claim_generation(
            user_id=user_id,
            encounter_id=encounter_id,
            claim_id="failed",
            success=False,
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Claim generation failed: {str(e)}"
        )


@router.get("/{claim_id}")
async def get_claim(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve generated claim by ID.
    
    Returns full claim details with evidence citations.
    """
    # In production, fetch from database
    # For now, return placeholder
    
    user_id = current_user.get("sub")
    
    audit.log_phi_access(
        user_id=user_id,
        resource_type="Claim",
        resource_id=claim_id,
        action="read",
    )
    
    # TODO: Implement database retrieval
    return {
        "id": claim_id,
        "status": "draft",
        "message": "Claim retrieval not yet implemented - use /generate endpoint"
    }


@router.get("")
async def list_claims(
    status: str | None = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    List claims for current user.
    
    Supports filtering by status.
    """
    user_id = current_user.get("sub")
    
    # TODO: Implement database query
    return {
        "claims": [],
        "count": 0,
        "message": "Claim listing not yet implemented"
    }


@router.post("/{claim_id}/export")
async def export_claim(
    claim_id: str,
    format: str = "json",  # json, cms1500, x12
    current_user: dict = Depends(get_current_user)
):
    """
    Export claim in specified format.
    
    Supports JSON, CMS-1500, and X12 formats.
    """
    user_id = current_user.get("sub")
    
    audit.log_phi_access(
        user_id=user_id,
        resource_type="Claim",
        resource_id=claim_id,
        action="export",
    )
    
    # TODO: Implement export formats
    return {
        "claim_id": claim_id,
        "format": format,
        "message": "Export not yet implemented"
    }
