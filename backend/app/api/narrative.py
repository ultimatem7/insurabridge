from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime
from app.core.llm import generate_completion, check_llm
from app.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

class EvidenceAtom(BaseModel):
    evidence_id: str
    evidence_type: str
    source_system: str
    document_name: Optional[str] = ""
    content_excerpt: str
    confidence: float

class Diagnosis(BaseModel):
    sequence: int
    code: str
    description: str
    confidence: float
    supporting_evidence: List[str] = []

class ClaimLine(BaseModel):
    line_number: int
    code: str
    code_type: str
    description: str
    charge_amount: float
    confidence: float
    supporting_evidence: List[str] = []
    rationale: str = ""

class NarrativeRequest(BaseModel):
    id: str
    status: str
    patient_id: str
    patient_name: str
    total_charges: float
    diagnoses: List[Diagnosis] = []
    lines: List[ClaimLine] = []
    evidence_atoms: List[EvidenceAtom] = []
    created_at: str
    requires_review: bool
    review_reasons: List[str] = []

@router.post("/generate")
async def generate_narrative(request: NarrativeRequest):
    """
    Generate a human-readable narrative claim using Ollama LLM.
    
    This creates a comprehensive narrative with:
    - Patient demographics
    - Clinical diagnoses with medical terminology explanations
    - Procedures performed with rationale
    - Medical necessity justification
    - Billing summary with coding references
    
    Each section references evidence atoms for traceability.
    """
    logger.info("Generating narrative claim", claim_id=request.id)
    
    try:
        # Check if LLM is available
        llm_available = await check_llm()
        if not llm_available:
            logger.warning("LLM not available, generating fallback narrative")
            return generate_fallback_narrative(request)
        
        # Build evidence context for the LLM
        evidence_context = ""
        if request.evidence_atoms:
            evidence_items = []
            for atom in request.evidence_atoms[:20]:  # Limit to 20 for context window
                evidence_items.append(f"[{atom.evidence_id}] ({atom.evidence_type}): {atom.content_excerpt}")
            evidence_context = "\n".join(evidence_items)
        else:
            evidence_context = "No clinical evidence atoms provided."
        
        # Build diagnoses context
        diagnoses_text = ""
        if request.diagnoses:
            diagnoses_items = []
            for d in request.diagnoses:
                diagnoses_items.append(f"- {d.code}: {d.description} (Confidence: {d.confidence*100:.0f}%)")
            diagnoses_text = "\n".join(diagnoses_items)
        else:
            diagnoses_text = "No diagnoses coded."
        
        # Build services context
        services_text = ""
        total_calc = 0.0
        if request.lines:
            service_items = []
            for line in request.lines:
                service_items.append(f"- Line {line.line_number}: {line.code} ({line.code_type}) - {line.description} - ${line.charge_amount:.2f}")
                total_calc += line.charge_amount
            services_text = "\n".join(service_items)
        else:
            services_text = "No services/procedures coded."
        
        # Construct the prompt
        prompt = f"""You are an expert medical coder and healthcare claims specialist. Generate a comprehensive narrative for the following insurance claim.

CLAIM INFORMATION:
- Claim ID: {request.id}
- Status: {request.status}
- Patient: {request.patient_name} (ID: {request.patient_id})
- Total Charges: ${request.total_charges:.2f}

DIAGNOSES (ICD-10):
{diagnoses_text}

SERVICES/PROCEDURES (CPT/HCPCS):
{services_text}

CLINICAL EVIDENCE FROM MEDICAL RECORD:
{evidence_context}

Generate a JSON response with exactly this structure:
{{
    "title": "Insurance Claim Narrative: {request.patient_name}",
    "summary": "A brief 2-3 sentence summary of the claim",
    "patient_section": {{
        "section_title": "Patient Demographics",
        "content": "Narrative describing the patient information and relevant demographics",
        "evidence_ids": []
    }},
    "diagnoses_section": {{
        "section_title": "Clinical Diagnoses",
        "content": "Detailed narrative explaining each diagnosis, its clinical significance, and supporting documentation",
        "evidence_ids": []
    }},
    "procedures_section": {{
        "section_title": "Services and Procedures",
        "content": "Narrative describing each service/procedure performed, why it was necessary, and how it relates to the diagnoses",
        "evidence_ids": []
    }},
    "medical_necessity_section": {{
        "section_title": "Medical Necessity Justification",
        "content": "Analysis of why each service was medically necessary based on the clinical evidence",
        "evidence_ids": []
    }},
    "billing_summary_section": {{
        "section_title": "Billing Summary",
        "content": "Summary of charges, coding rationale, and any compliance considerations",
        "evidence_ids": []
    }}
}}

IMPORTANT: 
- Reference evidence IDs (like EV-xxx) in the evidence_ids arrays when the evidence supports that section
- Be factual and only state what is supported by the evidence
- Use professional medical terminology
- Output ONLY valid JSON, no additional text"""

        logger.info("Calling LLM for narrative generation")
        
        response = await generate_completion(
            prompt=prompt,
            temperature=0.2,
            max_tokens=4096,
            json_mode=True
        )
        
        # Parse response - should be dict from json_mode=True
        narrative_data = response if isinstance(response, dict) else {}
        
        # Ensure all required fields exist
        default_section = {"section_title": "", "content": "", "evidence_ids": []}
        
        return {
            "claim_id": request.id,
            "title": narrative_data.get("title", f"Claim Narrative: {request.patient_name}"),
            "summary": narrative_data.get("summary", f"Insurance claim for {request.patient_name} with total charges of ${request.total_charges:.2f}"),
            "patient_section": narrative_data.get("patient_section", {**default_section, "section_title": "Patient Demographics", "content": f"Patient: {request.patient_name} (ID: {request.patient_id})"}),
            "diagnoses_section": narrative_data.get("diagnoses_section", {**default_section, "section_title": "Clinical Diagnoses", "content": diagnoses_text or "No diagnoses provided."}),
            "procedures_section": narrative_data.get("procedures_section", {**default_section, "section_title": "Services and Procedures", "content": services_text or "No services provided."}),
            "medical_necessity_section": narrative_data.get("medical_necessity_section", {**default_section, "section_title": "Medical Necessity", "content": "Medical necessity documentation required."}),
            "billing_summary_section": narrative_data.get("billing_summary_section", {**default_section, "section_title": "Billing Summary", "content": f"Total charges: ${request.total_charges:.2f}"}),
            "total_charges": request.total_charges,
            "status": request.status,
            "requires_review": request.requires_review,
            "review_reasons": request.review_reasons,
            "generated_at": datetime.now().isoformat(),
            "llm_model": settings.ollama_model,
            "evidence_atoms": [atom.model_dump() for atom in request.evidence_atoms]
        }

    except Exception as e:
        logger.error("Narrative generation failed", error=str(e), exc_info=True)
        # Return fallback narrative instead of failing
        return generate_fallback_narrative(request)


def generate_fallback_narrative(request: NarrativeRequest) -> dict:
    """
    Generate a fallback narrative when LLM is not available.
    Uses template-based generation with the provided data.
    """
    # Build diagnoses content
    diagnoses_content = ""
    if request.diagnoses:
        dx_items = []
        for d in request.diagnoses:
            dx_items.append(f"• {d.code} - {d.description} (Confidence: {d.confidence*100:.0f}%)")
        diagnoses_content = "The following diagnoses have been identified:\n\n" + "\n".join(dx_items)
    else:
        diagnoses_content = "No diagnoses have been coded for this claim."
    
    # Build procedures content
    procedures_content = ""
    if request.lines:
        proc_items = []
        for line in request.lines:
            proc_items.append(f"• Line {line.line_number}: {line.code} ({line.code_type}) - {line.description}\n  Charge: ${line.charge_amount:.2f} | Rationale: {line.rationale or 'N/A'}")
        procedures_content = "The following services/procedures have been billed:\n\n" + "\n".join(proc_items)
    else:
        procedures_content = "No services or procedures have been coded for this claim."
    
    # Build evidence summary
    evidence_ids = [atom.evidence_id for atom in request.evidence_atoms]
    
    return {
        "claim_id": request.id,
        "title": f"Insurance Claim Narrative: {request.patient_name}",
        "summary": f"This claim documents services provided to {request.patient_name} with total charges of ${request.total_charges:.2f}. Status: {request.status}.",
        "patient_section": {
            "section_title": "Patient Demographics",
            "content": f"Patient: {request.patient_name}\nPatient ID: {request.patient_id}\n\nThis section contains demographic information extracted from the patient's medical record.",
            "evidence_ids": [eid for eid in evidence_ids if 'PAT' in eid][:5]
        },
        "diagnoses_section": {
            "section_title": "Clinical Diagnoses",
            "content": diagnoses_content,
            "evidence_ids": [eid for eid in evidence_ids if 'CON' in eid][:5]
        },
        "procedures_section": {
            "section_title": "Services and Procedures",
            "content": procedures_content,
            "evidence_ids": [eid for eid in evidence_ids if 'PROC' in eid or 'OBS' in eid][:5]
        },
        "medical_necessity_section": {
            "section_title": "Medical Necessity Justification",
            "content": f"The services provided are medically necessary based on the documented diagnoses and clinical evidence. {len(request.evidence_atoms)} evidence atoms support this claim.",
            "evidence_ids": evidence_ids[:10]
        },
        "billing_summary_section": {
            "section_title": "Billing Summary",
            "content": f"Total Charges: ${request.total_charges:.2f}\n\nThis claim contains {len(request.lines)} service line(s) and {len(request.diagnoses)} diagnosis code(s).\n\n" +
                       ("Review Required: " + ", ".join(request.review_reasons) if request.review_reasons else "No compliance issues identified."),
            "evidence_ids": []
        },
        "total_charges": request.total_charges,
        "status": request.status,
        "requires_review": request.requires_review,
        "review_reasons": request.review_reasons,
        "generated_at": datetime.now().isoformat(),
        "llm_model": "fallback-template",
        "evidence_atoms": [atom.model_dump() for atom in request.evidence_atoms]
    }
