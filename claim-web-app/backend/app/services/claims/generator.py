"""
Claim Generator Service
Transforms FHIR encounter data into structured insurance claims using local LLM
"""

from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import httpx
import structlog

from app.core.config import settings
from app.services.fhir.normalizer import FHIRNormalizer

logger = structlog.get_logger(__name__)


class ClaimGenerator:
    """
    Generates insurance claims from EHR encounter data.
    
    Workflow:
    1. Normalize FHIR resources
    2. Build clinical context
    3. Send to local LLM
    4. Parse and structure response
    5. Add evidence citations
    """
    
    def __init__(self):
        self.normalizer = FHIRNormalizer()
        self.llm_url = settings.LLM_SERVICE_URL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
    
    async def generate_claim(
        self,
        encounter_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate claim from encounter data.
        
        Args:
            encounter_data: FHIR resources (patient, encounter, conditions, etc.)
            user_id: User generating the claim
        
        Returns:
            Structured claim data with evidence
        """
        claim_id = f"CLM-{uuid4().hex[:8].upper()}"
        
        logger.info("Generating claim", claim_id=claim_id)
        
        # Step 1: Normalize FHIR data
        normalized_data = self.normalizer.normalize_encounter_data(encounter_data)
        
        # Step 2: Build clinical context for LLM
        clinical_context = self._build_clinical_context(normalized_data)
        
        # Step 3: Call local LLM
        llm_response = await self._call_llm(clinical_context)
        
        # Step 4: Structure claim output
        claim = self._structure_claim(
            claim_id=claim_id,
            normalized_data=normalized_data,
            llm_response=llm_response,
            user_id=user_id
        )
        
        logger.info("Claim generation complete", 
                   claim_id=claim_id,
                   diagnoses_count=len(claim.get("diagnoses", [])),
                   procedures_count=len(claim.get("procedures", [])))
        
        return claim
    
    def _build_clinical_context(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build clinical context payload for LLM.
        
        Extracts relevant clinical information in a format optimized for LLM processing.
        """
        patient = normalized_data.get("patient", {})
        encounter = normalized_data.get("encounter", {})
        conditions = normalized_data.get("conditions", [])
        procedures = normalized_data.get("procedures", [])
        observations = normalized_data.get("observations", [])
        clinical_notes = normalized_data.get("clinical_notes_text", "")
        
        # Build structured context
        context = {
            "patient": {
                "age": patient.get("age"),
                "gender": patient.get("gender"),
                "demographics": {
                    "name": patient.get("name"),
                    "dob": patient.get("date_of_birth"),
                }
            },
            "encounter": {
                "type": encounter.get("type"),
                "class": encounter.get("class"),
                "start_date": encounter.get("start_datetime"),
                "end_date": encounter.get("end_datetime"),
                "provider": encounter.get("provider_name"),
                "facility": encounter.get("facility_name"),
                "place_of_service": encounter.get("place_of_service"),
            },
            "conditions": [
                {
                    "code": c.get("code"),
                    "display": c.get("display"),
                    "system": c.get("system"),
                    "clinical_status": c.get("clinical_status"),
                }
                for c in conditions
            ],
            "procedures": [
                {
                    "code": p.get("code"),
                    "display": p.get("display"),
                    "system": p.get("system"),
                    "date": p.get("performed_datetime"),
                }
                for p in procedures
            ],
            "observations": [
                {
                    "code": o.get("code"),
                    "display": o.get("display"),
                    "value": o.get("value"),
                    "unit": o.get("unit"),
                }
                for o in observations[:20]  # Limit to avoid token overflow
            ],
            "clinical_notes": clinical_notes[:5000] if clinical_notes else "No clinical notes available",  # Limit length
        }
        
        return context
    
    async def _call_llm(self, clinical_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call local LLM service for claim generation.
        
        Sends clinical context and receives structured claim data.
        """
        payload = {
            "context": clinical_context,
            "task": "generate_insurance_claim",
            "output_format": "structured_claim",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.llm_url}/generate-claim",
                    json=payload
                )
                response.raise_for_status()
                
                llm_data = response.json()
                logger.info("LLM response received", 
                           has_diagnoses=bool(llm_data.get("diagnoses")),
                           has_procedures=bool(llm_data.get("procedures")))
                return llm_data
                
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            # Return fallback claim based on FHIR data
            return self._fallback_claim(clinical_context)
        except httpx.HTTPError as e:
            logger.error("LLM request failed", error=str(e))
            return self._fallback_claim(clinical_context)
        except Exception as e:
            logger.error("Unexpected error calling LLM", error=str(e))
            return self._fallback_claim(clinical_context)
    
    def _fallback_claim(self, clinical_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate fallback claim when LLM is unavailable.
        
        Uses rule-based extraction from FHIR data.
        """
        logger.warning("Using fallback claim generation")
        
        # Extract diagnoses from conditions
        diagnoses = []
        for idx, condition in enumerate(clinical_context.get("conditions", [])):
            if condition.get("code"):
                diagnoses.append({
                    "code": condition["code"],
                    "description": condition.get("display", "Unknown condition"),
                    "sequence": idx + 1,
                    "confidence": 0.7,
                    "confidence_level": "medium",
                })
        
        # Extract procedures
        procedures = []
        for idx, procedure in enumerate(clinical_context.get("procedures", [])):
            if procedure.get("code"):
                procedures.append({
                    "code": procedure["code"],
                    "description": procedure.get("display", "Unknown procedure"),
                    "line_number": idx + 1,
                    "code_type": "CPT" if procedure.get("system", "").find("cpt") >= 0 else "HCPCS",
                    "modifiers": [],
                    "confidence": 0.7,
                    "confidence_level": "medium",
                    "charge_amount": 0.0,
                })
        
        # If no procedures from FHIR, add default E/M code
        if not procedures:
            encounter_type = clinical_context.get("encounter", {}).get("type", "").lower()
            default_code = "99213" if "outpatient" in encounter_type else "99214"
            
            procedures.append({
                "code": default_code,
                "description": "Office or other outpatient visit",
                "line_number": 1,
                "code_type": "CPT",
                "modifiers": [],
                "confidence": 0.6,
                "confidence_level": "low",
                "charge_amount": 150.00,
            })
        
        return {
            "diagnoses": diagnoses,
            "procedures": procedures,
            "supporting_evidence": ["Fallback generation - LLM unavailable"],
            "confidence_score": 0.6,
            "requires_review": True,
            "review_reasons": ["Generated without LLM - requires manual review"],
        }
    
    def _structure_claim(
        self,
        claim_id: str,
        normalized_data: Dict[str, Any],
        llm_response: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Structure final claim output.
        
        Combines normalized FHIR data with LLM-generated codes.
        """
        patient = normalized_data.get("patient", {})
        encounter = normalized_data.get("encounter", {})
        
        # Calculate total charges
        procedures = llm_response.get("procedures", [])
        total_charges = sum(p.get("charge_amount", 0.0) for p in procedures)
        
        # Determine if review is required
        requires_review = llm_response.get("requires_review", True)
        if llm_response.get("confidence_score", 0) < 0.8:
            requires_review = True
        
        # Build structured claim
        claim = {
            "id": claim_id,
            "claim_type": "professional",
            "status": "draft",
            
            # Patient
            "patient": {
                "id": patient.get("id"),
                "name": patient.get("name"),
                "date_of_birth": patient.get("date_of_birth"),
                "gender": patient.get("gender"),
                "address": patient.get("address"),
            },
            
            # Provider
            "provider": {
                "name": encounter.get("provider_name"),
                "npi": encounter.get("provider_npi"),
                "facility": encounter.get("facility_name"),
            },
            
            # Service dates
            "service_date_start": encounter.get("start_datetime"),
            "service_date_end": encounter.get("end_datetime"),
            "place_of_service": encounter.get("place_of_service"),
            
            # Diagnoses (ICD-10)
            "diagnoses": llm_response.get("diagnoses", []),
            
            # Procedures (CPT/HCPCS)
            "procedures": procedures,
            
            # Financial
            "total_charges": total_charges,
            
            # AI metadata
            "confidence_score": llm_response.get("confidence_score"),
            "llm_model": "local",
            
            # Evidence
            "supporting_evidence": llm_response.get("supporting_evidence", []),
            "audit_trail": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "generated",
                    "user_id": user_id,
                    "method": "llm" if not llm_response.get("requires_review") else "fallback",
                }
            ],
            
            # Review flags
            "requires_review": requires_review,
            "review_reasons": llm_response.get("review_reasons", []),
            
            # Timestamps
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return claim
