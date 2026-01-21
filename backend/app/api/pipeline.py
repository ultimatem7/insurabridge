from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.api.fhir_import import generate_claim_from_fhir, GenerateClaimFromFHIRRequest

router = APIRouter()

class PipelineRunRequest(BaseModel):
    """Request to run the pipeline with FHIR data."""
    fhir_data: Dict[str, Any]
    bridge_url: Optional[str] = None  # Optional: if provided, fetch from bridge instead

@router.post("/run")
async def run_pipeline(request: PipelineRunRequest):
    """
    Run the claim generation pipeline.
    
    If fhir_data is provided, use it directly.
    If bridge_url is provided and fhir_data is not, fetch from Epic Bridge.
    """
    try:
        # If FHIR data is provided, use it directly
        if request.fhir_data:
            claim_request = GenerateClaimFromFHIRRequest(
                fhir_data=request.fhir_data,
                claim_type="professional"
            )
            return await generate_claim_from_fhir(claim_request)
        
        # Otherwise, fetch from bridge (legacy behavior)
        if request.bridge_url:
            from app.api.fhir_import import run_full_pipeline
            return await run_full_pipeline(request.bridge_url)
        
        raise HTTPException(
            status_code=400,
            detail="Either fhir_data or bridge_url must be provided"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run pipeline: {str(e)}"
        )
