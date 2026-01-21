from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime

from app.demo.synthetic_patients import get_all_demo_patients, get_demo_patient_data, DEMO_PATIENTS
from app.fhir.converter import ingest_fhir_data
from app.claims.generator import generate_claim as gen_claim
from app.evidence.atoms import get_evidence_atom

router = APIRouter()


@router.get("/patients")
async def list_demo_patients():
    """
    List all available demo patients.
    
    Returns rich synthetic patients with comprehensive clinical data
    suitable for testing complex claim scenarios.
    """
    patients = []
    for pid, info in DEMO_PATIENTS.items():
        # Generate data to get accurate counts
        data = info["generator"]()
        
        # Count resources
        conditions_count = len(data.get("conditions", {}).get("entry", []))
        procedures_count = len(data.get("procedures", {}).get("entry", []))
        medications_count = len(data.get("medications", {}).get("entry", []))
        observations_count = len(data.get("observations", {}).get("entry", []))
        
        patient_resource = data.get("patient", {})
        
        patients.append({
            "id": pid,
            "name": info["name"],
            "description": info["description"],
            "expected_atoms": info["expected_atoms"],
            "tags": info["tags"],
            "gender": patient_resource.get("gender", "unknown"),
            "birthDate": patient_resource.get("birthDate", ""),
            "conditions": conditions_count,
            "procedures": procedures_count,
            "medications": medications_count,
            "observations": observations_count,
        })
    
    return {"patients": patients}


@router.get("/patient/{patient_id}")
async def get_demo_patient(patient_id: str):
    """
    Get basic patient information for a demo patient.
    """
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient {patient_id} not found")
    
    data = get_demo_patient_data(patient_id)
    return data.get("patient", {})


@router.get("/patient/{patient_id}/all")
async def get_demo_patient_all_data(patient_id: str):
    """
    Get ALL FHIR data for a demo patient.
    
    Returns the complete clinical dataset including:
    - Patient demographics
    - Conditions/diagnoses
    - Procedures
    - Medications
    - Observations (labs & vitals)
    - Encounters
    - Allergies
    - Immunizations
    """
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient {patient_id} not found")
    
    return get_demo_patient_data(patient_id)


@router.post("/generate-claim/{patient_id}")
async def generate_demo_claim(patient_id: str):
    """
    Generate a complete claim from demo patient data.
    
    This runs the full pipeline:
    1. Converts FHIR data to EvidenceAtoms
    2. Generates claim with diagnoses and procedures
    3. Returns claim with full evidence traceability
    """
    if patient_id not in DEMO_PATIENTS:
        raise HTTPException(status_code=404, detail=f"Demo patient {patient_id} not found")
    
    try:
        # Get the demo patient's FHIR data
        fhir_data = get_demo_patient_data(patient_id)
        
        # Step 1: Convert FHIR to EvidenceAtoms
        atom_ids = ingest_fhir_data(fhir_data)
        
        if not atom_ids:
            raise HTTPException(
                status_code=500,
                detail="Failed to extract evidence from demo patient data"
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
        
        # Step 4: Format diagnoses with evidence linking
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
        
        # Step 5: Format lines with evidence linking
        formatted_lines = []
        for line in claim_dict.get("lines", []):
            evidence_ids = line.get("evidence_ids", [])
            has_evidence = len(evidence_ids) > 0
            formatted_lines.append({
                "line_number": line.get("lineNumber", line.get("line_number", 1)),
                "code": line.get("code", ""),
                "code_type": line.get("codeType", line.get("code_type", "CPT")),
                "description": line.get("description", ""),
                "charge_amount": line.get("chargeAmount", 150.0),
                "confidence": line.get("confidence", 0.8),
                "confidence_level": line.get("confidenceLevel", "medium"),
                "supporting_evidence": evidence_ids,
                "evidence_ids": evidence_ids,
                "evidence_status": "verified" if has_evidence else "unsupported",
                "has_evidence": has_evidence,
                "rationale": line.get("rationale", "Supported by clinical evidence" if has_evidence else "⚠️ No supporting evidence"),
                "requires_review": line.get("requiresReview", not has_evidence),
            })
        
        # Get patient info
        patient_resource = fhir_data.get("patient", {})
        patient_name = "Unknown"
        names = patient_resource.get("name", [])
        if names:
            patient_name = names[0].get("text", f"{' '.join(names[0].get('given', []))} {names[0].get('family', '')}")
        
        return {
            "id": claim_dict.get("id", f"CLM-DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "status": claim_dict.get("status", "DRAFT").upper(),
            "patient_id": patient_id,
            "patient_name": patient_name.strip(),
            "diagnoses": formatted_diagnoses,
            "lines": formatted_lines,
            "total_charges": claim_dict.get("totalCharges", claim_dict.get("total_charges", 0.0)),
            "evidence_atoms": evidence_atoms,
            "evidence_count": len(evidence_atoms),
            "review_reasons": claim_dict.get("complianceIssues", []),
            "requires_review": len(claim_dict.get("complianceIssues", [])) > 0,
            "demo_patient": {
                "name": DEMO_PATIENTS[patient_id]["name"],
                "description": DEMO_PATIENTS[patient_id]["description"],
                "expected_atoms": DEMO_PATIENTS[patient_id]["expected_atoms"],
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate demo claim: {str(e)}")
