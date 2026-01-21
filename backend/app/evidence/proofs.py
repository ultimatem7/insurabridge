"""
Proof Chain System

Implements structured reasoning with MANDATORY citations.
Every claim element must have a complete proof chain.

A proof chain is valid ONLY if every step has evidence.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field, model_validator

from app.evidence.atoms import EvidenceAtom, get_evidence_store
from app.evidence.facts import Fact

logger = structlog.get_logger(__name__)


class ProofStatus(str, Enum):
    """Status of a proof chain."""
    VALID = "valid"           # All steps have evidence
    INCOMPLETE = "incomplete" # Missing evidence for some steps
    INVALID = "invalid"       # Contradictory or unsupportable
    UNSUPPORTED = "unsupported"  # No evidence provided


class ProofStep(BaseModel):
    """
    A single step in a proof chain.
    
    Each step must cite evidence. Steps without evidence
    render the entire proof chain invalid.
    """
    
    step_number: int
    step_description: str
    
    # MANDATORY: Evidence supporting this step
    evidence_ids: list[str] = Field(..., min_length=0)
    
    # Optional: Reference to external authority
    policy_reference: str | None = None
    guideline_reference: str | None = None
    codebook_reference: str | None = None
    
    # Validation
    has_evidence: bool = False
    evidence_strength: float = Field(ge=0.0, le=1.0, default=0.0)
    
    @model_validator(mode="after")
    def validate_evidence(self) -> "ProofStep":
        """Set has_evidence flag based on evidence_ids."""
        self.has_evidence = len(self.evidence_ids) > 0
        if self.has_evidence:
            # Base strength on number of supporting evidence atoms
            self.evidence_strength = min(1.0, len(self.evidence_ids) * 0.33)
        return self
    
    def get_evidence(self) -> list[EvidenceAtom]:
        """Retrieve all evidence atoms for this step."""
        store = get_evidence_store()
        return store.get_many(self.evidence_ids)
    
    def to_citation_text(self) -> str:
        """Generate text with inline citations."""
        citations = ", ".join(f"[{eid}]" for eid in self.evidence_ids)
        refs = []
        if self.policy_reference:
            refs.append(f"Policy: {self.policy_reference}")
        if self.guideline_reference:
            refs.append(f"Guideline: {self.guideline_reference}")
        if self.codebook_reference:
            refs.append(f"Codebook: {self.codebook_reference}")
        
        ref_text = "; ".join(refs) if refs else ""
        return f"{self.step_description} {citations} {ref_text}".strip()


class ProofChain(BaseModel):
    """
    A complete proof chain for a claim element.
    
    The chain is valid ONLY if ALL steps have evidence.
    Any missing evidence renders the entire chain INVALID.
    """
    
    chain_id: str = Field(default_factory=lambda: f"PROOF-{uuid4().hex[:12].upper()}")
    
    # What this proof is for
    claim_element: str  # e.g., "CPT 44970", "ICD-10 K35.80"
    claim_element_type: str  # diagnosis, procedure, modifier
    
    # The proof steps
    steps: list[ProofStep] = []
    
    # Overall validity
    status: ProofStatus = ProofStatus.UNSUPPORTED
    
    # Computed fields
    total_steps: int = 0
    steps_with_evidence: int = 0
    missing_evidence_steps: list[int] = []
    overall_confidence: float = 0.0
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @model_validator(mode="after")
    def compute_validity(self) -> "ProofChain":
        """Compute proof chain validity."""
        self.total_steps = len(self.steps)
        self.steps_with_evidence = sum(1 for s in self.steps if s.has_evidence)
        self.missing_evidence_steps = [
            s.step_number for s in self.steps if not s.has_evidence
        ]
        
        if self.total_steps == 0:
            self.status = ProofStatus.UNSUPPORTED
            self.overall_confidence = 0.0
        elif self.steps_with_evidence == self.total_steps:
            self.status = ProofStatus.VALID
            self.overall_confidence = sum(s.evidence_strength for s in self.steps) / self.total_steps
        elif self.steps_with_evidence > 0:
            self.status = ProofStatus.INCOMPLETE
            self.overall_confidence = (self.steps_with_evidence / self.total_steps) * 0.5
        else:
            self.status = ProofStatus.UNSUPPORTED
            self.overall_confidence = 0.0
        
        return self
    
    @property
    def is_valid(self) -> bool:
        """Check if proof chain is complete and valid."""
        return self.status == ProofStatus.VALID
    
    @property
    def is_submittable(self) -> bool:
        """Check if this proof allows claim submission."""
        return self.status == ProofStatus.VALID and self.overall_confidence >= 0.7
    
    def get_all_evidence_ids(self) -> list[str]:
        """Get all unique evidence IDs from all steps."""
        ids = set()
        for step in self.steps:
            ids.update(step.evidence_ids)
        return list(ids)
    
    def get_gaps(self) -> list[str]:
        """Get list of gaps that need to be filled."""
        gaps = []
        for step in self.steps:
            if not step.has_evidence:
                gaps.append(f"Step {step.step_number}: {step.step_description} - NO EVIDENCE")
        return gaps
    
    def to_narrative(self) -> str:
        """Generate a narrative explanation of the proof."""
        if not self.steps:
            return f"No proof available for {self.claim_element}"
        
        lines = [f"Proof Chain for {self.claim_element}:"]
        for step in self.steps:
            status = "✓" if step.has_evidence else "✗ UNSUPPORTED"
            lines.append(f"  {step.step_number}. {step.step_description} [{status}]")
            if step.evidence_ids:
                lines.append(f"     Evidence: {', '.join(step.evidence_ids)}")
            if step.policy_reference:
                lines.append(f"     Policy: {step.policy_reference}")
        
        lines.append(f"\nStatus: {self.status.value.upper()}")
        lines.append(f"Confidence: {self.overall_confidence:.0%}")
        
        return "\n".join(lines)


class MedicalNecessityProof(ProofChain):
    """
    Specialized proof chain for medical necessity.
    
    Required steps:
    1. Diagnosis confirmed
    2. Condition severity documented
    3. Treatment appropriateness established
    4. No less invasive alternatives (if applicable)
    """
    
    claim_element_type: str = "medical_necessity"
    
    # Standard medical necessity criteria
    diagnosis_confirmed: bool = False
    severity_documented: bool = False
    treatment_appropriate: bool = False
    alternatives_considered: bool = False
    
    @model_validator(mode="after")
    def check_medical_necessity_criteria(self) -> "MedicalNecessityProof":
        """Check if standard medical necessity criteria are met."""
        for step in self.steps:
            desc_lower = step.step_description.lower()
            if "diagnosis" in desc_lower and step.has_evidence:
                self.diagnosis_confirmed = True
            if "severity" in desc_lower and step.has_evidence:
                self.severity_documented = True
            if "treatment" in desc_lower or "appropriate" in desc_lower:
                if step.has_evidence:
                    self.treatment_appropriate = True
            if "alternative" in desc_lower and step.has_evidence:
                self.alternatives_considered = True
        
        return self


class CodeJustification(BaseModel):
    """
    Complete justification for a suggested code.
    
    Includes all required citations to evidence, codebook, and policy.
    """
    
    code: str
    code_type: str  # ICD-10, CPT, HCPCS, DRG
    description: str
    
    # MANDATORY: Fact that justifies this code
    justification_fact_id: str
    
    # MANDATORY: Clinical evidence
    clinical_evidence_ids: list[str] = Field(..., min_length=1)
    
    # MANDATORY: Codebook reference
    codebook_reference: str
    codebook_section: str | None = None
    
    # Optional but recommended: Payer policy
    payer_policy_reference: str | None = None
    payer_policy_section: str | None = None
    
    # The full proof chain
    proof_chain: ProofChain | None = None
    
    # Confidence and status
    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = True
    is_supported: bool = False
    unsupported_reason: str | None = None
    
    @model_validator(mode="after")
    def validate_support(self) -> "CodeJustification":
        """Determine if code is fully supported."""
        if not self.clinical_evidence_ids:
            self.is_supported = False
            self.unsupported_reason = "No clinical evidence provided"
        elif not self.codebook_reference:
            self.is_supported = False
            self.unsupported_reason = "No codebook reference provided"
        elif self.proof_chain and not self.proof_chain.is_valid:
            self.is_supported = False
            self.unsupported_reason = f"Proof chain incomplete: {', '.join(self.proof_chain.get_gaps())}"
        else:
            self.is_supported = True
            self.requires_review = self.confidence < 0.85
        
        return self
    
    def get_clinical_evidence(self) -> list[EvidenceAtom]:
        """Retrieve all clinical evidence atoms."""
        store = get_evidence_store()
        return store.get_many(self.clinical_evidence_ids)


class ProofChainBuilder:
    """
    Builder for constructing proof chains with validation.
    
    Ensures all required elements are present before finalizing.
    """
    
    def __init__(self, claim_element: str, claim_element_type: str = "code"):
        self.claim_element = claim_element
        self.claim_element_type = claim_element_type
        self.steps: list[ProofStep] = []
        self._step_counter = 0
    
    def add_step(
        self,
        description: str,
        evidence_ids: list[str] | None = None,
        policy_reference: str | None = None,
        guideline_reference: str | None = None,
        codebook_reference: str | None = None,
    ) -> "ProofChainBuilder":
        """Add a step to the proof chain."""
        self._step_counter += 1
        
        step = ProofStep(
            step_number=self._step_counter,
            step_description=description,
            evidence_ids=evidence_ids or [],
            policy_reference=policy_reference,
            guideline_reference=guideline_reference,
            codebook_reference=codebook_reference,
        )
        
        self.steps.append(step)
        return self
    
    def add_diagnosis_confirmation(
        self,
        diagnosis: str,
        evidence_ids: list[str],
    ) -> "ProofChainBuilder":
        """Add a diagnosis confirmation step."""
        return self.add_step(
            description=f"Diagnosis confirmed: {diagnosis}",
            evidence_ids=evidence_ids,
        )
    
    def add_severity_documentation(
        self,
        severity: str,
        evidence_ids: list[str],
    ) -> "ProofChainBuilder":
        """Add a severity documentation step."""
        return self.add_step(
            description=f"Severity documented: {severity}",
            evidence_ids=evidence_ids,
        )
    
    def add_policy_compliance(
        self,
        policy_name: str,
        policy_section: str,
        evidence_ids: list[str],
    ) -> "ProofChainBuilder":
        """Add a policy compliance step."""
        return self.add_step(
            description=f"Meets policy criteria",
            evidence_ids=evidence_ids,
            policy_reference=f"{policy_name} {policy_section}",
        )
    
    def add_codebook_reference(
        self,
        codebook: str,
        section: str,
    ) -> "ProofChainBuilder":
        """Add a codebook reference step."""
        return self.add_step(
            description=f"Codebook guidance applied",
            evidence_ids=[],  # Codebook itself is the authority
            codebook_reference=f"{codebook} {section}",
        )
    
    def build(self) -> ProofChain:
        """Build the final proof chain."""
        return ProofChain(
            claim_element=self.claim_element,
            claim_element_type=self.claim_element_type,
            steps=self.steps,
        )
    
    def build_medical_necessity(self) -> MedicalNecessityProof:
        """Build as a medical necessity proof."""
        return MedicalNecessityProof(
            claim_element=self.claim_element,
            steps=self.steps,
        )

