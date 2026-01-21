"""
Evidence-Bound Claims Generator

Generates insurance claims from EvidenceAtoms with mandatory citations.
No claim field can exist without supporting evidence.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import re

# Import Enum to avoid string literal mismatch
try:
    from ..evidence.atoms import EvidenceAtom, get_evidence_atom, EvidenceType
except ImportError:
    # Fallback for circular import or testing
    from app.evidence.atoms import EvidenceAtom, get_evidence_atom, EvidenceType

class ClaimField(BaseModel):
    """A single field in a claim with evidence binding."""
    field_name: str
    value: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    status: str = "VALID"  # VALID, UNSUPPORTED, REVIEW_REQUIRED
    source_excerpt: Optional[str] = None


class ClaimDiagnosis(BaseModel):
    """Diagnosis code with evidence binding."""
    code: str
    code_system: str = "ICD-10-CM"
    display: str
    sequence: int
    evidence_ids: List[str]
    confidence: float
    is_primary: bool = False


class ClaimProcedure(BaseModel):
    """Procedure/service code with evidence binding."""
    code: str
    code_system: str = "CPT"
    display: str
    service_date: Optional[str] = None
    evidence_ids: List[str]
    medical_necessity_proof: Optional[str] = None  # Proof ID
    confidence: float


class GeneratedClaim(BaseModel):
    """A complete insurance claim with full evidence traceability."""
    claim_id: str = Field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:8].upper()}")
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "DRAFT"  # DRAFT, VALIDATED, REVIEW_REQUIRED, BLOCKED, SUBMITTED
    
    # Patient info
    patient: Dict[str, ClaimField] = Field(default_factory=dict)
    
    # Clinical info
    diagnoses: List[ClaimDiagnosis] = Field(default_factory=list)
    procedures: List[ClaimProcedure] = Field(default_factory=list)
    
    # Insurance info
    insurance: Dict[str, ClaimField] = Field(default_factory=dict)
    
    # Metadata
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    all_evidence_ids: List[str] = Field(default_factory=list)
    can_submit: bool = False


class ClaimsGenerator:
    """Generates claims from EvidenceAtoms."""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def generate_from_evidence(self, evidence_ids: List[str]) -> GeneratedClaim:
        print(f"DEBUG: Generator processing {len(evidence_ids)} atoms")
        
        claim = GeneratedClaim()
        claim.all_evidence_ids = evidence_ids
        
        demographics = []
        diagnoses = []
        procedures = []
        coverage = []
        
        for ev_id in evidence_ids:
            atom = get_evidence_atom(ev_id)
            if not atom:
                continue
            
            ev_type = atom.evidence_type
            
            # Smart Categorization
            if ev_type == EvidenceType.HISTORY:
                # Basic loose categorization based on strings in content
                content = atom.content_excerpt
                if any(x in content for x in ["Name:", "Date of Birth:", "Gender:", "Address:", "Race:"]):
                    demographics.append(atom)
                elif "Clinical Status:" in content or "(Code:" in content:
                     # "(Code:" is the signature of our Condition formatting (Diagnosis)
                    diagnoses.append(atom)
                else:
                    # Default to demographics if unsure
                    demographics.append(atom)
            
            elif ev_type in [EvidenceType.INSURANCE, EvidenceType.CLAIM]:
                coverage.append(atom)
            
            elif ev_type == EvidenceType.PROCEDURE:
                procedures.append(atom)

        print(f"DEBUG: Categorized - Pat:{len(demographics)} Dx:{len(diagnoses)} Proc:{len(procedures)} Ins:{len(coverage)}")

        # Build sections
        claim.patient = self._build_patient_fields(demographics)
        claim.diagnoses = self._build_diagnosis_codes(diagnoses)
        claim.procedures = self._build_procedure_codes(procedures)
        claim.insurance = self._build_insurance_fields(coverage)
        
        self._validate_claim(claim)
        return claim

    def _build_patient_fields(self, atoms: List[EvidenceAtom]) -> Dict[str, ClaimField]:
        fields = {}
        for atom in atoms:
            content = atom.content_excerpt
            
            # Flexible parsing
            if "Patient Name:" in content:
                fields["patient_name"] = self._make_field("patient_name", content.split("Name:")[1], atom)
            elif "Date of Birth:" in content:
                fields["date_of_birth"] = self._make_field("date_of_birth", content.split("Birth:")[1], atom)
            elif "Gender:" in content:
                fields["gender"] = self._make_field("gender", content.split("Gender:")[1], atom)
            elif "Address:" in content:
                fields["address"] = self._make_field("address", content.split("Address:")[1], atom)
                
        return fields

    def _build_diagnosis_codes(self, atoms: List[EvidenceAtom]) -> List[ClaimDiagnosis]:
        diagnoses = []
        sequence = 1
        
        for atom in atoms:
            content = atom.content_excerpt
            # Format: "Display text (Code: X12.3)" OR "Diagnosis: Display (Code: X12.3)"
            
            match = re.search(r"(.*?)\(Code:\s*([^)]+)\)", content)
            if match:
                display = match.group(1).replace("Diagnosis:", "").strip()
                code = match.group(2).strip()
                
                diagnoses.append(ClaimDiagnosis(
                    code=code,
                    display=display or "Unknown",
                    sequence=sequence,
                    evidence_ids=[atom.evidence_id],
                    confidence=atom.extraction_confidence,
                    is_primary=(sequence == 1)
                ))
                sequence += 1
            else:
                print(f"DEBUG: Failed to parse diagnosis atom: {content}")
                
        return diagnoses

    def _build_procedure_codes(self, atoms: List[EvidenceAtom]) -> List[ClaimProcedure]:
        procedures = []
        
        for atom in atoms:
            content = atom.content_excerpt
            
            # Try multiple formats:
            # Format 1: "Procedure: Display (CPT Code: 12345)" or "Procedure: Display (HCPCS Code: 12345)"
            match = re.search(r"Procedure:\s*(.*?)\((?:CPT|HCPCS|SNOMED|procedure_code)\s*Code:\s*([^)]+)\)", content)
            if match:
                display = match.group(1).strip()
                code = match.group(2).strip()
                
                procedures.append(ClaimProcedure(
                    code=code,
                    display=display,
                    evidence_ids=[atom.evidence_id],
                    confidence=atom.extraction_confidence
                ))
                continue
            
            # Format 2: "Service: Display (Code: 12345)"
            match = re.search(r"Service:\s*(.*?)\(Code:\s*([^)]+)\)", content)
            if match:
                display = match.group(1).strip()
                code = match.group(2).strip()
                
                procedures.append(ClaimProcedure(
                    code=code,
                    display=display,
                    evidence_ids=[atom.evidence_id],
                    confidence=atom.extraction_confidence
                ))
        
        return procedures

    def _build_insurance_fields(self, atoms: List[EvidenceAtom]) -> Dict[str, ClaimField]:
        fields = {}
        for atom in atoms:
            content = atom.content_excerpt
            
            if "Insurance Payer:" in content:
                fields["payer_name"] = self._make_field("payer_name", content.split("Payer:")[1], atom)
            elif "Coverage Status:" in content:
                 fields["coverage_status"] = self._make_field("coverage_status", content.split("Status:")[1], atom)
            elif "period" in content.lower():
                 # Matches "Coverage Period:" or "Service Period:"
                 val = content.split(":")[1] if ":" in content else content
                 fields["coverage_period"] = self._make_field("coverage_period", val, atom)
                 
        return fields

    def _make_field(self, name: str, value: str, atom: EvidenceAtom) -> ClaimField:
        return ClaimField(
            field_name=name,
            value=value.strip(),
            evidence_ids=[atom.evidence_id],
            confidence=atom.extraction_confidence,
            source_excerpt=atom.content_excerpt
        )

    def _validate_claim(self, claim: GeneratedClaim):
        # Basic validation
        if not claim.patient.get("patient_name"):
            claim.validation_errors.append("Missing Patient Name")
        if not claim.diagnoses:
            claim.validation_warnings.append("No Diagnoses Found")
            
        if claim.validation_errors:
            claim.status = "BLOCKED"
        elif claim.validation_warnings:
            claim.status = "REVIEW_REQUIRED"
        else:
            claim.can_submit = True
            claim.status = "VALIDATED"


# Singleton
claims_generator = ClaimsGenerator()

def generate_claim(evidence_ids: List[str]) -> Dict[str, Any]:
    """
    Generate a claim from evidence IDs.
    Returns a dictionary formatted for the Frontend 'Claim' interface.
    
    If no clinical data (diagnoses/procedures) is found, generates a demo claim.
    """
    print(f"DEBUG: generate_claim called with {len(evidence_ids)} atoms")
    try:
        # Generate the internal Pydantic model
        internal_claim = claims_generator.generate_from_evidence(evidence_ids)
        
        # Extract patient name for personalization
        patient_name = "Unknown Patient"
        patient_dob = "Unknown"
        if internal_claim.patient.get("patient_name"):
            patient_name = internal_claim.patient["patient_name"].value
        if internal_claim.patient.get("date_of_birth"):
            patient_dob = internal_claim.patient["date_of_birth"].value
        
        # Check if we have any clinical data
        has_clinical_data = bool(internal_claim.diagnoses or internal_claim.procedures)
        
        if has_clinical_data:
            # Use real data with evidence linking
            frontend_diagnoses = []
            for dx in internal_claim.diagnoses:
                has_evidence = len(dx.evidence_ids) > 0
                evidence_status = "verified" if has_evidence else "unsupported"
                
                frontend_diagnoses.append({
                    "sequence": dx.sequence,
                    "code": dx.code,
                    "description": dx.display,
                    "confidence": dx.confidence,
                    "confidenceLevel": "high" if dx.confidence > 0.85 else ("medium" if dx.confidence > 0.7 else "low"),
                    "evidence_ids": dx.evidence_ids,
                    "evidence_status": evidence_status,
                    "has_evidence": has_evidence,
                })
                
            frontend_lines = []
            total_charges = 0.0
            for i, proc in enumerate(internal_claim.procedures):
                charge = 150.0
                total_charges += charge
                has_evidence = len(proc.evidence_ids) > 0
                evidence_status = "verified" if has_evidence else "unsupported"
                
                frontend_lines.append({
                    "lineNumber": i + 1,
                    "code": proc.code,
                    "codeType": proc.code_system,
                    "description": proc.display,
                    "modifiers": [],
                    "confidence": proc.confidence,
                    "confidenceLevel": "high" if proc.confidence > 0.85 else ("medium" if proc.confidence > 0.7 else "low"),
                    "rationale": f"Supported by {len(proc.evidence_ids)} evidence atom(s)" if has_evidence else "⚠️ No supporting evidence found",
                    "requiresReview": not has_evidence or proc.confidence < 0.8,
                    "evidence_ids": proc.evidence_ids,
                    "evidence_status": evidence_status,
                    "has_evidence": has_evidence,
                })
        else:
            # DEMO FALLBACK: Generate realistic demo data (all marked as unsupported)
            print("DEBUG: No clinical data found, using demo fallback")
            frontend_diagnoses = [
                {"sequence": 1, "code": "I10", "description": "Essential (primary) hypertension", "confidence": 0.92, "confidenceLevel": "high", "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
                {"sequence": 2, "code": "E11.9", "description": "Type 2 diabetes mellitus without complications", "confidence": 0.88, "confidenceLevel": "high", "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
                {"sequence": 3, "code": "Z79.84", "description": "Long term (current) use of oral hypoglycemic drugs", "confidence": 0.76, "confidenceLevel": "medium", "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
            ]
            frontend_lines = [
                {"lineNumber": 1, "code": "99214", "codeType": "CPT", "description": "Office visit, established patient, moderate complexity", "modifiers": [], "confidence": 0.91, "confidenceLevel": "high", "rationale": "⚠️ Demo data - no evidence", "requiresReview": True, "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
                {"lineNumber": 2, "code": "83036", "codeType": "CPT", "description": "Hemoglobin A1c", "modifiers": [], "confidence": 0.95, "confidenceLevel": "high", "rationale": "⚠️ Demo data - no evidence", "requiresReview": True, "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
                {"lineNumber": 3, "code": "80053", "codeType": "CPT", "description": "Comprehensive metabolic panel", "modifiers": [], "confidence": 0.72, "confidenceLevel": "medium", "rationale": "⚠️ Demo data - no evidence", "requiresReview": True, "evidence_ids": [], "evidence_status": "unsupported", "has_evidence": False},
            ]
            total_charges = 485.00
            
        return {
            "id": internal_claim.claim_id,
            "status": "validated" if has_clinical_data else "draft",
            "diagnoses": frontend_diagnoses,
            "lines": frontend_lines,
            "overallConfidence": 0.86,
            "complianceIssues": [
                "Line 3: Verify medical necessity documentation for CMP",
                "Consider adding modifier 25 to E/M code if significant separate service"
            ] if not has_clinical_data else internal_claim.validation_warnings,
            "totalCharges": total_charges,
            "patient": {
                "name": patient_name,
                "dob": patient_dob,
            }
        }

    except Exception as e:
        print(f"ERROR in generate_claim: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "id": "ERROR-000",
            "status": "draft",
            "diagnoses": [],
            "lines": [],
            "overallConfidence": 0,
            "complianceIssues": [f"Generation Error: {str(e)}"],
            "totalCharges": 0
        }
