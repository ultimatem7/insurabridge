"""
FHIR API Endpoints
Access to EHR FHIR resources
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog

from app.core.security import get_current_user, audit
from app.services.ehr import get_adapter

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/patients")
async def list_patients(current_user: dict = Depends(get_current_user)):
    """
    Get current patient info.
    
    Returns FHIR Patient resource for authenticated patient.
    """
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    if not all([provider, patient_id, access_token]):
        raise HTTPException(status_code=400, detail="Invalid session")
    
    try:
        adapter = get_adapter(provider)
        patient = await adapter.fetch_patient(patient_id, access_token)
        
        audit.log_phi_access(
            user_id=current_user.get("sub"),
            resource_type="Patient",
            resource_id=patient_id,
            action="read",
        )
        
        return patient
    except Exception as e:
        logger.error("Failed to fetch patient", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch patient data")


@router.get("/encounters")
async def list_encounters(
    status: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    List patient encounters.
    
    Returns list of FHIR Encounter resources.
    """
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    try:
        adapter = get_adapter(provider)
        encounters = await adapter.fetch_encounters(
            patient_id,
            access_token,
            status=status
        )
        
        audit.log_phi_access(
            user_id=current_user.get("sub"),
            resource_type="Encounter",
            resource_id="multiple",
            action="read",
        )
        
        return {"encounters": encounters, "count": len(encounters)}
    except Exception as e:
        logger.error("Failed to fetch encounters", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch encounters")


@router.get("/encounters/{encounter_id}")
async def get_encounter_detail(
    encounter_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full encounter details with all related resources.
    
    Fetches encounter, conditions, procedures, observations, etc.
    """
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    try:
        adapter = get_adapter(provider)
        
        # Fetch all encounter data
        encounter_data = await adapter.fetch_all_encounter_data(
            patient_id,
            encounter_id,
            access_token
        )
        
        audit.log_phi_access(
            user_id=current_user.get("sub"),
            resource_type="Encounter",
            resource_id=encounter_id,
            action="read_detailed",
        )
        
        return encounter_data
    except Exception as e:
        logger.error("Failed to fetch encounter details", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch encounter details")


@router.get("/conditions")
async def list_conditions(current_user: dict = Depends(get_current_user)):
    """List patient conditions (diagnoses)."""
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    try:
        adapter = get_adapter(provider)
        conditions = await adapter.fetch_conditions(patient_id, access_token)
        return {"conditions": conditions, "count": len(conditions)}
    except Exception as e:
        logger.error("Failed to fetch conditions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch conditions")


@router.get("/procedures")
async def list_procedures(current_user: dict = Depends(get_current_user)):
    """List patient procedures."""
    provider = current_user.get("provider")
    patient_id = current_user.get("patient_id")
    access_token = current_user.get("ehr_access_token")
    
    try:
        adapter = get_adapter(provider)
        procedures = await adapter.fetch_procedures(patient_id, access_token)
        return {"procedures": procedures, "count": len(procedures)}
    except Exception as e:
        logger.error("Failed to fetch procedures", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch procedures")
