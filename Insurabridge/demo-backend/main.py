"""
Insurabridge Demo Backend
A simplified backend for demonstrating the FHIR-to-Claim pipeline
Works with Python 3.14+ without complex dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
import httpx

app = FastAPI(
    title="Insurabridge Demo API",
    description="FHIR-to-Claim Pipeline Demo",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Models ============

class EvidenceAtom(BaseModel):
    evidence_id: str
    evidence_type: str
    source_system: str
    document_name: str
    content_excerpt: str
    confidence: float = 1.0

class Diagnosis(BaseModel):
    sequence: int
    code: str
    description: str
    confidence: float
    supporting_evidence: List[str]

class ClaimLine(BaseModel):
    line_number: int
    code: str
    code_type: str
    description: str
    charge_amount: float
    confidence: float
    supporting_evidence: List[str]
    rationale: str

class ClaimResponse(BaseModel):
    id: str
    status: str
    patient_id: Optional[str]
    patient_name: Optional[str]
    total_charges: float
    diagnoses: List[Diagnosis]
    lines: List[ClaimLine]
    evidence_atoms: List[EvidenceAtom]
    created_at: str
    requires_review: bool
    review_reasons: List[str]

class PipelineRequest(BaseModel):
    bridge_url: str = "http://localhost:3000"

# ============ FHIR to EvidenceAtom Converter ============

def convert_patient_to_atoms(patient: Dict[str, Any]) -> List[EvidenceAtom]:
    """Convert FHIR Patient resource to EvidenceAtoms"""
    atoms = []
    
    # Full patient record
    atoms.append(EvidenceAtom(
        evidence_id=f"EV-{uuid4().hex[:8]}",
        evidence_type="fhir_patient",
        source_system="EPIC FHIR",
        document_name=f"Patient {patient.get('id', 'Unknown')}",
        content_excerpt=f"Patient ID: {patient.get('id')}, Active: {patient.get('active')}",
        confidence=1.0,
    ))
    
    # Patient name
    names = patient.get("name", [])
    if names:
        name_text = names[0].get("text", "")
        if name_text:
            atoms.append(EvidenceAtom(
                evidence_id=f"EV-{uuid4().hex[:8]}",
                evidence_type="patient_name",
                source_system="EPIC FHIR",
                document_name="Patient Demographics",
                content_excerpt=f"Patient Name: {name_text}",
                confidence=1.0,
            ))
    
    # Birth date
    birth_date = patient.get("birthDate")
    if birth_date:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_dob",
            source_system="EPIC FHIR",
            document_name="Patient Demographics",
            content_excerpt=f"Date of Birth: {birth_date}",
            confidence=1.0,
        ))
    
    # Gender
    gender = patient.get("gender")
    if gender:
        atoms.append(EvidenceAtom(
            evidence_id=f"EV-{uuid4().hex[:8]}",
            evidence_type="patient_gender",
            source_system="EPIC FHIR",
            document_name="Patient Demographics",
            content_excerpt=f"Gender: {gender}",
            confidence=1.0,
        ))
    
    # Extensions (race, ethnicity, etc.)
    extensions = patient.get("extension", [])
    for ext in extensions:
        url = ext.get("url", "")
        if "race" in url:
            race_ext = ext.get("extension", [{}])
            for r in race_ext:
                if r.get("url") == "text":
                    atoms.append(EvidenceAtom(
                        evidence_id=f"EV-{uuid4().hex[:8]}",
                        evidence_type="patient_race",
                        source_system="EPIC FHIR",
                        document_name="Patient Demographics",
                        content_excerpt=f"Race: {r.get('valueString', 'Unknown')}",
                        confidence=1.0,
                    ))
    
    return atoms

def generate_claim_from_atoms(
    atoms: List[EvidenceAtom],
    patient: Dict[str, Any]
) -> ClaimResponse:
    """Generate a claim from EvidenceAtoms using rule-based logic"""
    
    # Extract patient info
    patient_id = patient.get("id", "Unknown")
    patient_name = "Unknown"
    names = patient.get("name", [])
    if names:
        patient_name = names[0].get("text", "Unknown")
    
    # Demo: Generate diagnoses based on patient data
    # In production, this would use LLM + medical knowledge base
    diagnoses = []
    review_reasons = []
    
    # Check if we have enough evidence for a diagnosis
    dob_atoms = [a for a in atoms if a.evidence_type == "patient_dob"]
    if dob_atoms:
        # Demo: Add a routine checkup diagnosis
        diagnoses.append(Diagnosis(
            sequence=1,
            code="Z00.00",
            description="Encounter for general adult medical examination without abnormal findings",
            confidence=0.95,
            supporting_evidence=[a.evidence_id for a in dob_atoms],
        ))
    else:
        review_reasons.append("Missing date of birth - cannot verify patient age for age-specific codes")
    
    # Demo claim lines based on encounter type
    lines = []
    
    # Office visit - always included for demo
    lines.append(ClaimLine(
        line_number=1,
        code="99213",
        code_type="CPT",
        description="Office or other outpatient visit, established patient, low complexity",
        charge_amount=150.00,
        confidence=0.92,
        supporting_evidence=[atoms[0].evidence_id] if atoms else [],
        rationale="Standard office visit supported by patient encounter documentation",
    ))
    
    # If we have demographic data, add preventive medicine codes
    gender_atoms = [a for a in atoms if a.evidence_type == "patient_gender"]
    if gender_atoms:
        lines.append(ClaimLine(
            line_number=2,
            code="99395",
            code_type="CPT",
            description="Periodic comprehensive preventive medicine, 18-39 years",
            charge_amount=250.00,
            confidence=0.88,
            supporting_evidence=[a.evidence_id for a in gender_atoms],
            rationale="Preventive medicine visit appropriate based on patient demographics",
        ))
    
    total_charges = sum(line.charge_amount for line in lines)
    requires_review = len(review_reasons) > 0 or any(l.confidence < 0.9 for l in lines)
    
    if any(l.confidence < 0.9 for l in lines):
        review_reasons.append("One or more claim lines have confidence below 90%")
    
    return ClaimResponse(
        id=f"CLM-{uuid4().hex[:8].upper()}",
        status="DRAFT" if requires_review else "VALIDATED",
        patient_id=patient_id,
        patient_name=patient_name,
        total_charges=total_charges,
        diagnoses=diagnoses,
        lines=lines,
        evidence_atoms=atoms,
        created_at=datetime.now().isoformat(),
        requires_review=requires_review,
        review_reasons=review_reasons,
    )

# ============ API Endpoints ============

@app.get("/")
async def root():
    return {
        "service": "Insurabridge Demo API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "pipeline": "POST /pipeline/run",
            "patient": "GET /fhir/patient?bridge_url=...",
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/fhir/patient")
async def get_patient(bridge_url: str = "http://localhost:3000"):
    """Fetch patient data from the Epic FHIR Bridge"""
    try:
        async with httpx.AsyncClient() as client:
            # Check auth status
            status_resp = await client.get(f"{bridge_url}/auth/status")
            status_data = status_resp.json()
            
            if not status_data.get("authenticated"):
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated with Epic. Please login first at the bridge.",
                )
            
            # Fetch patient
            patient_resp = await client.get(f"{bridge_url}/fhir/patient")
            patient_resp.raise_for_status()
            return patient_resp.json()
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Epic FHIR Bridge at {bridge_url}: {str(e)}",
        )

@app.post("/pipeline/run", response_model=ClaimResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run the full FHIR-to-Claim pipeline:
    1. Fetch patient data from Epic FHIR Bridge
    2. Convert FHIR resources to EvidenceAtoms
    3. Generate claim using Evidence-Bound Generation
    """
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Check auth status
            status_resp = await client.get(f"{request.bridge_url}/auth/status")
            status_data = status_resp.json()
            
            if not status_data.get("authenticated"):
                raise HTTPException(
                    status_code=401,
                    detail="Not authenticated with Epic. Please visit the bridge and login first.",
                )
            
            # Step 2: Fetch patient data
            patient_resp = await client.get(f"{request.bridge_url}/fhir/patient")
            patient_resp.raise_for_status()
            patient_data = patient_resp.json()
            
            # Step 3: Convert to EvidenceAtoms
            atoms = convert_patient_to_atoms(patient_data)
            
            # Step 4: Generate claim
            claim = generate_claim_from_atoms(atoms, patient_data)
            
            return claim
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"FHIR API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Epic FHIR Bridge: {str(e)}",
        )

@app.get("/auth/status")
async def check_bridge_auth(bridge_url: str = "http://localhost:3000"):
    """Check if the Epic FHIR Bridge is authenticated"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{bridge_url}/auth/status")
            return resp.json()
    except httpx.RequestError as e:
        return {
            "authenticated": False,
            "error": f"Cannot connect to bridge: {str(e)}",
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

