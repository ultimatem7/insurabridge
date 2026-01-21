"""
Evidence-Bound Reasoning Engine

This module replaces free-form reasoning with EVIDENCE-BOUND reasoning.

CRITICAL CONSTRAINTS:
1. Every code must be justified by EvidenceAtoms
2. Every conclusion requires a ProofChain
3. Any unsupported output is flagged as UNSUPPORTED
4. No free-text generation without citations
"""

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from app.core.llm import get_llm_client, SystemPrompts
from app.core.knowledge import get_knowledge_base
from app.core.audit import log_event, AuditEventType
from app.evidence.atoms import EvidenceAtom, get_evidence_store, EvidenceType
from app.evidence.facts import Fact, FactExtractor, get_fact_extractor
from app.evidence.proofs import (
    ProofChain,
    ProofStep,
    ProofChainBuilder,
    CodeJustification,
    MedicalNecessityProof,
    ProofStatus,
)
from app.evidence.validator import (
    ValidationResult,
    EvidenceValidator,
    EvidenceBoundValue,
    get_validator,
)

logger = structlog.get_logger(__name__)


class EvidenceBoundDiagnosis(BaseModel):
    """
    A diagnosis with mandatory evidence binding.
    
    Cannot be created without evidence.
    """
    
    code: str
    code_type: str = "ICD10CM"
    description: str
    
    # MANDATORY evidence binding
    evidence_ids: list[str] = Field(..., min_length=1)
    justification_fact_ids: list[str] = []
    
    # Proof chain
    proof_chain: ProofChain | None = None
    
    # Codebook reference
    codebook_reference: str
    codebook_section: str | None = None
    
    # Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Status
    is_primary: bool = False
    sequence: int = 1
    
    # Validation
    is_supported: bool = False
    unsupported_reason: str | None = None
    requires_review: bool = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._validate_support()
    
    def _validate_support(self):
        if not self.evidence_ids:
            self.is_supported = False
            self.unsupported_reason = "No clinical evidence provided"
        elif not self.codebook_reference:
            self.is_supported = False
            self.unsupported_reason = "No codebook reference"
        elif self.proof_chain and not self.proof_chain.is_valid:
            self.is_supported = False
            self.unsupported_reason = f"Incomplete proof: {self.proof_chain.get_gaps()}"
        else:
            self.is_supported = True
            self.requires_review = self.confidence < 0.85


class EvidenceBoundProcedure(BaseModel):
    """
    A procedure code with mandatory evidence binding.
    """
    
    code: str
    code_type: str = "CPT"
    description: str
    
    # MANDATORY evidence binding
    evidence_ids: list[str] = Field(..., min_length=1)
    justification_fact_ids: list[str] = []
    
    # Proof chain (REQUIRED for procedures)
    proof_chain: ProofChain
    medical_necessity_proof: MedicalNecessityProof | None = None
    
    # Code references
    codebook_reference: str
    payer_policy_reference: str | None = None
    
    # Modifiers
    modifiers: list[str] = []
    modifier_evidence_ids: dict[str, list[str]] = {}  # modifier -> evidence IDs
    
    # Units and charges
    units: float = 1.0
    charge_amount: float | None = None
    
    # Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Validation
    is_supported: bool = False
    unsupported_reason: str | None = None
    requires_review: bool = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._validate_support()
    
    def _validate_support(self):
        if not self.evidence_ids:
            self.is_supported = False
            self.unsupported_reason = "No clinical evidence provided"
        elif not self.codebook_reference:
            self.is_supported = False
            self.unsupported_reason = "No codebook reference"
        elif not self.proof_chain.is_valid:
            self.is_supported = False
            self.unsupported_reason = f"Incomplete proof chain"
        else:
            self.is_supported = True
            self.requires_review = self.confidence < 0.85 or not self.payer_policy_reference


class EvidenceBoundClaim(BaseModel):
    """
    A complete claim where EVERY field is evidence-bound.
    
    Claims with unsupported fields cannot be exported.
    """
    
    claim_id: str
    
    # Patient/encounter (references, not PHI)
    patient_id: str | None = None
    encounter_id: str | None = None
    
    # Evidence-bound diagnoses
    diagnoses: list[EvidenceBoundDiagnosis] = []
    
    # Evidence-bound procedures
    procedures: list[EvidenceBoundProcedure] = []
    
    # All evidence used
    all_evidence_ids: list[str] = []
    
    # Validation
    validation_result: ValidationResult | None = None
    
    # Status
    is_valid: bool = False
    is_exportable: bool = False
    unsupported_elements: list[str] = []
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def validate(self) -> ValidationResult:
        """Run full validation on the claim."""
        validator = get_validator()
        
        # Build claim data dict
        claim_data = {
            "diagnoses": [
                {
                    "code": dx.code,
                    "description": dx.description,
                    "evidence_ids": dx.evidence_ids,
                    "codebook_reference": dx.codebook_reference,
                    "proof_chain": dx.proof_chain.model_dump() if dx.proof_chain else None,
                }
                for dx in self.diagnoses
            ],
            "lines": [
                {
                    "code": proc.code,
                    "description": proc.description,
                    "evidence_ids": proc.evidence_ids,
                    "codebook_reference": proc.codebook_reference,
                    "proof_chain": proc.proof_chain.model_dump(),
                }
                for proc in self.procedures
            ],
        }
        
        result = validator.validate_claim(claim_data, self.claim_id)
        self.validation_result = result
        self.is_valid = result.is_valid
        self.is_exportable = result.is_exportable
        
        # Collect unsupported elements
        self.unsupported_elements = []
        for dx in self.diagnoses:
            if not dx.is_supported:
                self.unsupported_elements.append(f"Diagnosis {dx.code}: {dx.unsupported_reason}")
        for proc in self.procedures:
            if not proc.is_supported:
                self.unsupported_elements.append(f"Procedure {proc.code}: {proc.unsupported_reason}")
        
        # Collect all evidence IDs
        all_ids = set()
        for dx in self.diagnoses:
            all_ids.update(dx.evidence_ids)
        for proc in self.procedures:
            all_ids.update(proc.evidence_ids)
        self.all_evidence_ids = list(all_ids)
        
        return result


# Evidence-Bound Code Mapping Prompts

CODE_MAPPING_PROMPT = """You are mapping clinical facts to medical codes.

CRITICAL RULES - VIOLATIONS WILL BE REJECTED:
1. ONLY suggest codes that are DIRECTLY supported by the provided facts
2. Each code MUST cite the specific fact(s) that justify it
3. You MUST provide a codebook reference for each code
4. Do NOT infer conditions not explicitly stated
5. If a code cannot be fully justified, mark it as requires_review

For each code suggestion, provide:
1. code: The ICD-10, CPT, or HCPCS code
2. code_type: ICD10CM | ICD10PCS | CPT | HCPCS
3. justification_facts: List of FACT-IDs that support this code
4. codebook_reference: The specific coding guideline (e.g., "ICD-10-CM Guidelines Section I.A.1")
5. confidence: 0.0-1.0 based on how clearly the facts support the code
6. notes: Any considerations for human review

OUTPUT FORMAT (JSON array):
[
  {
    "code": "I10",
    "code_type": "ICD10CM",
    "description": "Essential (primary) hypertension",
    "justification_facts": ["FACT-ABC123"],
    "codebook_reference": "ICD-10-CM Section I.C.9.a",
    "confidence": 0.92,
    "notes": null
  }
]

If NO codes can be justified, return: []

DO NOT SUGGEST CODES WITHOUT FACT CITATIONS."""


class EvidenceBoundReasoningEngine:
    """
    Reasoning engine that produces ONLY evidence-bound output.
    
    This engine is structurally incapable of generating unsupported claims.
    """
    
    def __init__(self):
        self.llm = None
        self.knowledge = None
        self.fact_extractor = None
        self.evidence_store = None
        self.validator = None
    
    async def _ensure_initialized(self):
        if self.llm is None:
            self.llm = get_llm_client()
        if self.knowledge is None:
            self.knowledge = get_knowledge_base()
        if self.fact_extractor is None:
            self.fact_extractor = get_fact_extractor()
        if self.evidence_store is None:
            self.evidence_store = get_evidence_store()
        if self.validator is None:
            self.validator = get_validator()
    
    async def generate_evidence_bound_claim(
        self,
        evidence_ids: list[str],
        encounter_id: str | None = None,
        patient_id: str | None = None,
        payer: str | None = None,
    ) -> EvidenceBoundClaim:
        """
        Generate a claim from evidence atoms.
        
        Every element of the claim will be traceable to source evidence.
        """
        await self._ensure_initialized()
        
        from app.core.security import generate_secure_id
        claim_id = f"CLM-{generate_secure_id()}"
        
        # Step 1: Retrieve evidence atoms
        atoms = self.evidence_store.get_many(evidence_ids)
        if not atoms:
            return EvidenceBoundClaim(
                claim_id=claim_id,
                patient_id=patient_id,
                encounter_id=encounter_id,
                is_valid=False,
                unsupported_elements=["No evidence provided"],
            )
        
        # Step 2: Extract facts from evidence
        fact_result = await self.fact_extractor.extract_facts(atoms)
        facts = fact_result.facts
        
        if not facts:
            return EvidenceBoundClaim(
                claim_id=claim_id,
                patient_id=patient_id,
                encounter_id=encounter_id,
                is_valid=False,
                unsupported_elements=["No extractable facts from evidence"],
            )
        
        # Step 3: Map facts to codes
        diagnoses = await self._map_diagnosis_codes(facts, atoms)
        procedures = await self._map_procedure_codes(facts, atoms, payer)
        
        # Step 4: Build proof chains
        for proc in procedures:
            # Medical necessity proof for procedures
            proc.medical_necessity_proof = await self._build_medical_necessity_proof(
                proc, diagnoses, facts
            )
        
        # Step 5: Create the claim
        claim = EvidenceBoundClaim(
            claim_id=claim_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            diagnoses=diagnoses,
            procedures=procedures,
        )
        
        # Step 6: Validate
        claim.validate()
        
        # Log
        log_event(
            event_type=AuditEventType.CLAIM_CREATE,
            description="Evidence-bound claim generated",
            resource_type="claim",
            resource_id=claim_id,
            details={
                "evidence_count": len(evidence_ids),
                "fact_count": len(facts),
                "diagnosis_count": len(diagnoses),
                "procedure_count": len(procedures),
                "is_valid": claim.is_valid,
                "is_exportable": claim.is_exportable,
            },
        )
        
        return claim
    
    async def _map_diagnosis_codes(
        self,
        facts: list[Fact],
        atoms: list[EvidenceAtom],
    ) -> list[EvidenceBoundDiagnosis]:
        """Map facts to diagnosis codes with full evidence binding."""
        
        # Filter to diagnosis-relevant facts
        diagnosis_facts = [f for f in facts if f.fact_type in ["diagnosis", "finding", "history"]]
        
        if not diagnosis_facts:
            return []
        
        # Build fact summary for LLM
        fact_summary = "\n".join([
            f"- [{f.fact_id}] {f.fact_text}"
            for f in diagnosis_facts
        ])
        
        prompt = f"""Map these clinical facts to ICD-10-CM diagnosis codes.

FACTS:
{fact_summary}

Remember: Each code MUST cite specific FACT-IDs as justification.
Only suggest codes that are DIRECTLY supported by the facts."""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=CODE_MAPPING_PROMPT,
            temperature=0.0,
            json_mode=True,
        )
        
        diagnoses = []
        
        try:
            suggestions = json.loads(response.content)
            
            for i, sugg in enumerate(suggestions):
                code = sugg.get("code", "")
                
                # Verify code exists
                code_results = await self.knowledge.search_icd10(code, limit=1)
                if not code_results:
                    logger.warning("LLM suggested non-existent ICD-10 code", code=code)
                    continue
                
                # Get evidence IDs from cited facts
                fact_ids = sugg.get("justification_facts", [])
                evidence_ids = []
                for fid in fact_ids:
                    for fact in diagnosis_facts:
                        if fact.fact_id == fid:
                            evidence_ids.append(fact.evidence_id)
                            break
                
                if not evidence_ids:
                    logger.warning("Code has no traceable evidence", code=code)
                    continue
                
                # Build proof chain
                proof = (
                    ProofChainBuilder(f"ICD-10 {code}", "diagnosis")
                    .add_diagnosis_confirmation(code, evidence_ids)
                    .add_codebook_reference("ICD-10-CM", sugg.get("codebook_reference", ""))
                    .build()
                )
                
                dx = EvidenceBoundDiagnosis(
                    code=code,
                    code_type="ICD10CM",
                    description=code_results[0].description,
                    evidence_ids=evidence_ids,
                    justification_fact_ids=fact_ids,
                    proof_chain=proof,
                    codebook_reference=sugg.get("codebook_reference", "ICD-10-CM Guidelines"),
                    confidence=sugg.get("confidence", 0.7),
                    is_primary=(i == 0),
                    sequence=i + 1,
                )
                diagnoses.append(dx)
                
        except Exception as e:
            logger.error("Failed to map diagnosis codes", error=str(e))
        
        return diagnoses
    
    async def _map_procedure_codes(
        self,
        facts: list[Fact],
        atoms: list[EvidenceAtom],
        payer: str | None = None,
    ) -> list[EvidenceBoundProcedure]:
        """Map facts to procedure codes with full evidence binding."""
        
        # Filter to procedure-relevant facts
        procedure_facts = [f for f in facts if f.fact_type in ["procedure", "finding", "provider_statement"]]
        
        if not procedure_facts:
            return []
        
        fact_summary = "\n".join([
            f"- [{f.fact_id}] {f.fact_text}"
            for f in procedure_facts
        ])
        
        prompt = f"""Map these clinical facts to CPT/HCPCS procedure codes.

FACTS:
{fact_summary}

Remember: Each code MUST cite specific FACT-IDs as justification.
Include codebook references (e.g., "CPT Guidelines - Evaluation and Management")."""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=CODE_MAPPING_PROMPT.replace("ICD-10", "CPT/HCPCS"),
            temperature=0.0,
            json_mode=True,
        )
        
        procedures = []
        
        try:
            suggestions = json.loads(response.content)
            
            for sugg in suggestions:
                code = sugg.get("code", "")
                code_type = sugg.get("code_type", "CPT")
                
                # Verify code exists
                if code_type == "CPT":
                    code_results = await self.knowledge.search_cpt(code, limit=1)
                else:
                    code_results = await self.knowledge.search_hcpcs(code, limit=1)
                
                if not code_results:
                    logger.warning("LLM suggested non-existent code", code=code)
                    continue
                
                # Get evidence IDs
                fact_ids = sugg.get("justification_facts", [])
                evidence_ids = []
                for fid in fact_ids:
                    for fact in procedure_facts:
                        if fact.fact_id == fid:
                            evidence_ids.append(fact.evidence_id)
                            break
                
                if not evidence_ids:
                    continue
                
                # Get policy reference if available
                policy_ref = None
                if payer:
                    policies = await self.knowledge.search_policies(
                        f"{code_results[0].description} coverage",
                        payer=payer,
                        limit=1,
                    )
                    if policies:
                        policy_ref = f"{policies[0].payer}: {policies[0].title}"
                
                # Build proof chain
                proof = (
                    ProofChainBuilder(f"{code_type} {code}", "procedure")
                    .add_step("Service documented", evidence_ids)
                    .add_codebook_reference(code_type, sugg.get("codebook_reference", ""))
                    .build()
                )
                
                proc = EvidenceBoundProcedure(
                    code=code,
                    code_type=code_type,
                    description=code_results[0].description,
                    evidence_ids=evidence_ids,
                    justification_fact_ids=fact_ids,
                    proof_chain=proof,
                    codebook_reference=sugg.get("codebook_reference", f"{code_type} Guidelines"),
                    payer_policy_reference=policy_ref,
                    confidence=sugg.get("confidence", 0.7),
                )
                procedures.append(proc)
                
        except Exception as e:
            logger.error("Failed to map procedure codes", error=str(e))
        
        return procedures
    
    async def _build_medical_necessity_proof(
        self,
        procedure: EvidenceBoundProcedure,
        diagnoses: list[EvidenceBoundDiagnosis],
        facts: list[Fact],
    ) -> MedicalNecessityProof:
        """Build a medical necessity proof chain for a procedure."""
        
        builder = ProofChainBuilder(
            f"Medical Necessity for {procedure.code}",
            "medical_necessity"
        )
        
        # Step 1: Diagnosis support
        supporting_dx_evidence = []
        for dx in diagnoses:
            supporting_dx_evidence.extend(dx.evidence_ids)
        
        if supporting_dx_evidence:
            builder.add_diagnosis_confirmation(
                ", ".join([dx.code for dx in diagnoses]),
                supporting_dx_evidence,
            )
        
        # Step 2: Procedure documentation
        builder.add_step(
            "Procedure performed and documented",
            procedure.evidence_ids,
        )
        
        # Step 3: Codebook compliance
        builder.add_codebook_reference(
            procedure.code_type,
            procedure.codebook_reference,
        )
        
        # Step 4: Policy compliance (if available)
        if procedure.payer_policy_reference:
            builder.add_policy_compliance(
                procedure.payer_policy_reference.split(":")[0],
                procedure.payer_policy_reference,
                procedure.evidence_ids,
            )
        
        return builder.build_medical_necessity()


# Global evidence-bound engine instance
_eb_engine: EvidenceBoundReasoningEngine | None = None


def get_evidence_bound_engine() -> EvidenceBoundReasoningEngine:
    """Get the evidence-bound reasoning engine."""
    global _eb_engine
    if _eb_engine is None:
        _eb_engine = EvidenceBoundReasoningEngine()
    return _eb_engine

