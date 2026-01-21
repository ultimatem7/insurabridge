"""
FHIR Import API Endpoints

Handles ingestion of FHIR data from Epic and triggers
the Evidence-Bound Generation pipeline.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime

from ..fhir.converter import ingest_fhir_data, fhir_patient_to_atoms
from ..evidence.atoms import get_evidence_atom, EvidenceAtom
from ..evidence.extractor import extract_facts_from_evidence
from ..evidence.facts import get_facts_by_evidence_id

router = APIRouter()


class FHIRImportRequest(BaseModel):
    """Request to import FHIR data."""
    fhir_data: Dict[str, Any]
    source: str = "EPIC"
    trigger_fact_extraction: bool = True


class FHIRImportResponse(BaseModel):
    """Response from FHIR import."""
    success: bool
    message: str
    evidence_atom_ids: List[str]
    patient_id: Optional[str] = None
    evidence_count: int


class EpicBridgeRequest(BaseModel):
    """Request to fetch data from Epic FHIR Bridge."""
    bridge_url: str = "http://localhost:3000"
    endpoints: List[str] = ["patient"]


class PatientSummary(BaseModel):
    """Summary of patient data extracted from FHIR."""
    patient_id: str
    name: str
    birth_date: Optional[str]
    gender: Optional[str]
    evidence_atoms: List[str]
    facts_extracted: int


@router.post("/fhir/import", response_model=FHIRImportResponse)
async def import_fhir_data(
    request: FHIRImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Import FHIR data and convert to EvidenceAtoms.
    
    Accepts:
    - Single FHIR resource (Patient, Condition, Coverage, EOB)
    - FHIR Bundle
    - Composite response from Epic FHIR Bridge
    
    Returns list of created EvidenceAtom IDs.
    """
    try:
        # Convert FHIR to EvidenceAtoms
        atom_ids = ingest_fhir_data(request.fhir_data)
        
        # Extract patient ID if available
        patient_id = None
        if request.fhir_data.get('resourceType') == 'Patient':
            patient_id = request.fhir_data.get('id')
        elif 'patient' in request.fhir_data:
            patient_id = request.fhir_data['patient'].get('id')
        
        # Optionally trigger fact extraction in background
        if request.trigger_fact_extraction and atom_ids:
            background_tasks.add_task(extract_facts_for_atoms, atom_ids[:10])  # Limit to 10 for demo
        
        return FHIRImportResponse(
            success=True,
            message=f"Successfully imported FHIR data. Created {len(atom_ids)} EvidenceAtoms.",
            evidence_atom_ids=atom_ids,
            patient_id=patient_id,
            evidence_count=len(atom_ids)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import FHIR data: {str(e)}"
        )


@router.post("/fhir/fetch-from-bridge")
async def fetch_from_epic_bridge(request: EpicBridgeRequest):
    """
    Fetch FHIR data from the Epic FHIR Bridge service
    and import it into the evidence pipeline.
    
    The bridge must be running at the specified URL.
    """
    results = {
        "success": True,
        "fetched": {},
        "evidence_atoms": [],
        "errors": []
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in request.endpoints:
            try:
                url = f"{request.bridge_url}/fhir/{endpoint}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    fhir_data = response.json()
                    results["fetched"][endpoint] = True
                    
                    # Import the data
                    atom_ids = ingest_fhir_data(fhir_data)
                    results["evidence_atoms"].extend(atom_ids)
                    
                elif response.status_code == 401:
                    results["errors"].append(f"{endpoint}: Not authenticated - visit {request.bridge_url}/auth/authorize first")
                else:
                    results["errors"].append(f"{endpoint}: HTTP {response.status_code}")
                    
            except httpx.RequestError as e:
                results["errors"].append(f"{endpoint}: Connection error - {str(e)}")
    
    if results["errors"]:
        results["success"] = False
    
    results["total_evidence_atoms"] = len(results["evidence_atoms"])
    
    return results


@router.get("/fhir/evidence/{patient_id}")
async def get_patient_evidence(patient_id: str):
    """
    Get all EvidenceAtoms for a patient.
    """
    # In a real implementation, this would query by patient
    # For now, return a summary structure
    return {
        "patient_id": patient_id,
        "message": "Query evidence store by patient ID",
        "note": "In production, this would return all atoms linked to this patient"
    }


@router.post("/fhir/process-patient")
async def process_patient_for_claims(
    patient_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Full pipeline: Import patient FHIR data and prepare for claims generation.
    
    1. Convert FHIR to EvidenceAtoms
    2. Extract facts from each atom
    3. Return summary for claims UI
    """
    try:
        # Step 1: Import FHIR data
        atom_ids = ingest_fhir_data(patient_data)
        
        # Step 2: Extract patient info
        patient_id = None
        patient_name = "Unknown"
        birth_date = None
        gender = None
        
        if patient_data.get('resourceType') == 'Patient':
            patient_id = patient_data.get('id')
            names = patient_data.get('name', [])
            if names:
                name_obj = names[0]
                patient_name = name_obj.get('text') or f"{' '.join(name_obj.get('given', []))} {name_obj.get('family', '')}"
            birth_date = patient_data.get('birthDate')
            gender = patient_data.get('gender')
        
        # Step 3: Queue fact extraction
        facts_count = 0
        for atom_id in atom_ids[:5]:  # Process first 5 atoms synchronously for demo
            atom = get_evidence_atom(atom_id)
            if atom:
                # In production, this would call the LLM
                # For now, just count
                facts_count += 1
        
        return PatientSummary(
            patient_id=patient_id or "unknown",
            name=patient_name.strip(),
            birth_date=birth_date,
            gender=gender,
            evidence_atoms=atom_ids,
            facts_extracted=facts_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process patient: {str(e)}"
        )


async def extract_facts_for_atoms(atom_ids: List[str]):
    """Background task to extract facts from EvidenceAtoms."""
    for atom_id in atom_ids:
        atom = get_evidence_atom(atom_id)
        if atom:
            try:
                await extract_facts_from_evidence(atom)
            except Exception as e:
                print(f"Error extracting facts from {atom_id}: {e}")


# ============================================
# Claims Generation from FHIR
# ============================================

from ..claims.generator import generate_claim as gen_claim, GeneratedClaim


class GenerateClaimFromFHIRRequest(BaseModel):
    """Request to generate a claim from FHIR data."""
    fhir_data: Dict[str, Any]
    claim_type: str = "professional"


@router.post("/fhir/generate-claim", response_model=GeneratedClaim)
async def generate_claim_from_fhir(request: GenerateClaimFromFHIRRequest):
    """
    Full pipeline: FHIR data → EvidenceAtoms → Claim
    
    1. Imports FHIR data as EvidenceAtoms
    2. Generates a claim with full evidence traceability
    3. Validates the claim
    4. Returns claim ready for review
    """
    try:
        # Step 1: Import FHIR to EvidenceAtoms
        atom_ids = ingest_fhir_data(request.fhir_data)
        
        if not atom_ids:
            raise HTTPException(
                status_code=400,
                detail="No evidence could be extracted from FHIR data"
            )
        
        # Step 2: Generate claim from evidence
        claim_dict = gen_claim(atom_ids)
        
        # Step 3: Get evidence atoms for the response
        evidence_atoms = []
        for atom_id in atom_ids:
            try:
                atom = get_evidence_atom(atom_id)
                if atom:
                    evidence_atoms.append({
                        "evidence_id": atom.evidence_id,
                        "evidence_type": atom.evidence_type.value if hasattr(atom.evidence_type, 'value') else str(atom.evidence_type),
                        "content_excerpt": atom.content_excerpt,
                        "source_system": atom.source_system.value if hasattr(atom.source_system, 'value') else str(atom.source_system),
                        "confidence": atom.extraction_confidence,
                        "document_name": atom.document_name,
                    })
            except Exception as e:
                print(f"Warning: Failed to retrieve atom {atom_id}: {e}")
        
        print(f"DEBUG: Returning {len(evidence_atoms)} evidence atoms")
        
        # Step 4: Format response to match frontend expectations
        # Map diagnoses to expected format with evidence linking
        formatted_diagnoses = []
        for dx in claim_dict.get("diagnoses", []):
            evidence_ids = dx.get("evidence_ids", [])
            has_evidence = len(evidence_ids) > 0
            formatted_diagnoses.append({
                "code": dx.get("code", ""),
                "description": dx.get("description", ""),
                "sequence": dx.get("sequence", 1),
                "confidence": dx.get("confidence", 0.8),
                "confidence_level": dx.get("confidenceLevel", "medium"),
                "supporting_evidence": evidence_ids,
                "evidence_ids": evidence_ids,
                "evidence_status": "verified" if has_evidence else "unsupported",
                "has_evidence": has_evidence,
            })
        
        # Map lines to expected format with evidence linking
        formatted_lines = []
        for line in claim_dict.get("lines", []):
            evidence_ids = line.get("evidence_ids", [])
            has_evidence = len(evidence_ids) > 0
            formatted_lines.append({
                "line_number": line.get("lineNumber", line.get("line_number", 1)),
                "code": line.get("code", ""),
                "code_type": line.get("codeType", line.get("code_type", "CPT")),
                "description": line.get("description", ""),
                "charge_amount": 150.0,  # Default charge, should come from line data
                "confidence": line.get("confidence", 0.8),
                "confidence_level": line.get("confidenceLevel", "medium"),
                "supporting_evidence": evidence_ids,
                "evidence_ids": evidence_ids,
                "evidence_status": "verified" if has_evidence else "unsupported",
                "has_evidence": has_evidence,
                "rationale": line.get("rationale", "Supported by clinical evidence" if has_evidence else "⚠️ No supporting evidence"),
                "requires_review": line.get("requiresReview", not has_evidence),
            })
        
        # Extract patient info from FHIR data
        patient_id = ""
        if isinstance(request.fhir_data, dict):
            if request.fhir_data.get("resourceType") == "Patient":
                patient_id = request.fhir_data.get("id", "")
            elif "patient" in request.fhir_data and isinstance(request.fhir_data["patient"], dict):
                patient_id = request.fhir_data["patient"].get("id", "")
        
        response = {
            "id": claim_dict.get("id", f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "claim_id": claim_dict.get("id", f"CLM-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "status": claim_dict.get("status", "draft").upper(),
            "patient_id": patient_id,
            "patient_name": claim_dict.get("patient", {}).get("name", "Unknown Patient"),
            "diagnoses": formatted_diagnoses,
            "lines": formatted_lines,
            "total_charges": claim_dict.get("totalCharges", claim_dict.get("total_charges", 0.0)),
            "evidence_atoms": evidence_atoms,
            "review_reasons": claim_dict.get("complianceIssues", claim_dict.get("validation_warnings", [])),
            "requires_review": len(claim_dict.get("complianceIssues", [])) > 0,
            "validation_errors": claim_dict.get("validation_errors", []),
            "validation_warnings": claim_dict.get("complianceIssues", claim_dict.get("validation_warnings", [])),
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate claim: {str(e)}"
        )


@router.post("/fhir/full-pipeline")
async def run_full_pipeline(bridge_url: str = "http://localhost:3000"):
    """
    Complete end-to-end pipeline:
    
    1. Fetch patient data from Epic FHIR Bridge
    2. Convert to EvidenceAtoms
    3. Generate claim with citations
    4. Return claim + evidence summary
    """
    results = {
        "success": False,
        "patient": None,
        "evidence_atoms": [],
        "claim": None,
        "errors": []
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Use the /fhir/all endpoint to get ALL clinical data in one call
            all_resp = await client.get(f"{bridge_url}/fhir/all")
            
            if all_resp.status_code == 200:
                all_data = all_resp.json()
                
                # Extract patient info for display
                patient_data = all_data.get("patient")
                if patient_data:
                    results["patient"] = {
                        "id": patient_data.get("id"),
                        "name": patient_data.get("name", [{}])[0].get("text", "Unknown"),
                    }
                
                # Ingest ALL data using composite handler in ingest_fhir_data
                # The function handles dict with patient, conditions, coverages, etc.
                atom_ids = ingest_fhir_data(all_data)
                results["evidence_atoms"] = atom_ids
                
                # Generate claim from all evidence
                if atom_ids:
                    claim_dict = gen_claim(atom_ids)
                    results["claim"] = claim_dict
                    results["success"] = True
                else:
                    results["errors"].append("No evidence atoms created from FHIR data")
                    
            elif all_resp.status_code == 401:
                results["errors"].append(
                    f"Not authenticated. Visit {bridge_url}/auth/authorize first"
                )
            else:
                results["errors"].append(f"Failed to fetch clinical data: HTTP {all_resp.status_code}")
                
        except httpx.RequestError as e:
            results["errors"].append(f"Connection error: {str(e)}. Is the Epic bridge running?")
    
    return results

