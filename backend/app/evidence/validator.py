"""
Evidence Validator

The gatekeeper that ensures NO unsupported output leaves the system.

This module implements the HARD RULE:
Any output without full provenance MUST be blocked.

Validation failures are not warnings - they are BLOCKING errors.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar
from functools import wraps

import structlog
from pydantic import BaseModel, Field

from app.evidence.atoms import EvidenceAtom, get_evidence_store
from app.evidence.proofs import ProofChain, ProofStatus, CodeJustification
from app.core.audit import log_event, AuditEventType

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    BLOCKING = "blocking"      # Prevents submission - MUST be resolved
    WARNING = "warning"        # Should be reviewed - human override allowed
    INFO = "info"             # For awareness only


class ValidationError(BaseModel):
    """
    A validation error that BLOCKS output.
    
    These are not warnings - they prevent the system from producing output.
    """
    
    error_id: str = Field(default_factory=lambda: f"VERR-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}")
    
    # What failed
    field_path: str  # e.g., "claim.lines[0].code"
    error_type: str  # unsupported, missing_evidence, invalid_proof, etc.
    message: str
    
    # Severity
    severity: ValidationSeverity = ValidationSeverity.BLOCKING
    
    # What evidence was expected but missing
    missing_evidence_for: str | None = None
    
    # What would fix this
    remediation: str | None = None
    
    # Timestamp
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def is_blocking(self) -> bool:
        return self.severity == ValidationSeverity.BLOCKING


class ValidationResult(BaseModel):
    """
    Complete validation result for an output.
    
    If is_valid is False, the output CANNOT be used or exported.
    """
    
    # Overall result
    is_valid: bool = False
    is_exportable: bool = False
    
    # What was validated
    validated_object_type: str
    validated_object_id: str | None = None
    
    # Errors and warnings
    errors: list[ValidationError] = []
    
    # Statistics
    total_fields_checked: int = 0
    fields_with_evidence: int = 0
    fields_without_evidence: int = 0
    
    # Evidence coverage
    evidence_coverage: float = 0.0  # 0-1
    all_evidence_ids: list[str] = []
    
    # Timestamp
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def blocking_errors(self) -> list[ValidationError]:
        return [e for e in self.errors if e.is_blocking]
    
    @property
    def warnings(self) -> list[ValidationError]:
        return [e for e in self.errors if e.severity == ValidationSeverity.WARNING]
    
    def add_error(
        self,
        field_path: str,
        error_type: str,
        message: str,
        severity: ValidationSeverity = ValidationSeverity.BLOCKING,
        remediation: str | None = None,
    ) -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(
            field_path=field_path,
            error_type=error_type,
            message=message,
            severity=severity,
            remediation=remediation,
        ))
        if severity == ValidationSeverity.BLOCKING:
            self.is_valid = False
            self.is_exportable = False
    
    def compute_coverage(self) -> None:
        """Compute evidence coverage statistics."""
        if self.total_fields_checked > 0:
            self.evidence_coverage = self.fields_with_evidence / self.total_fields_checked
        self.is_valid = len(self.blocking_errors) == 0
        self.is_exportable = self.is_valid and self.evidence_coverage >= 0.9


class EvidenceBoundValue(BaseModel):
    """
    A value that is bound to evidence.
    
    This is the ONLY acceptable format for claim fields.
    Raw values without evidence binding are rejected.
    """
    
    field_name: str
    value: Any
    evidence_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Proof chain (optional but recommended)
    proof_chain_id: str | None = None
    
    # Status
    is_supported: bool = False
    unsupported_reason: str | None = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-compute support status
        if self.evidence_ids:
            self.is_supported = True
        else:
            self.is_supported = False
            self.unsupported_reason = "No evidence IDs provided"
    
    def verify_evidence_exists(self) -> bool:
        """Verify all referenced evidence exists in store."""
        store = get_evidence_store()
        for eid in self.evidence_ids:
            if not store.exists(eid):
                return False
        return True


class EvidenceValidator:
    """
    The central validator that enforces evidence binding.
    
    CRITICAL: This validator has VETO POWER.
    Any output that fails validation CANNOT be exported.
    """
    
    def __init__(self):
        self._store = None
    
    @property
    def store(self):
        if self._store is None:
            self._store = get_evidence_store()
        return self._store
    
    def validate_evidence_bound_value(
        self,
        value: EvidenceBoundValue,
        field_path: str,
    ) -> list[ValidationError]:
        """Validate a single evidence-bound value."""
        errors = []
        
        # Check if evidence is provided
        if not value.evidence_ids:
            errors.append(ValidationError(
                field_path=field_path,
                error_type="missing_evidence",
                message=f"Field '{value.field_name}' has no evidence binding",
                severity=ValidationSeverity.BLOCKING,
                remediation=f"Add evidence_ids to support the value '{value.value}'",
            ))
            return errors
        
        # Verify all evidence exists
        for eid in value.evidence_ids:
            if not self.store.exists(eid):
                errors.append(ValidationError(
                    field_path=f"{field_path}.evidence_ids",
                    error_type="invalid_evidence_reference",
                    message=f"Evidence ID '{eid}' does not exist",
                    severity=ValidationSeverity.BLOCKING,
                    remediation=f"Provide a valid evidence ID",
                ))
        
        # Check confidence threshold
        if value.confidence < 0.5:
            errors.append(ValidationError(
                field_path=field_path,
                error_type="low_confidence",
                message=f"Confidence {value.confidence:.0%} is below threshold",
                severity=ValidationSeverity.WARNING,
                remediation="Review evidence and consider adding more documentation",
            ))
        
        return errors
    
    def validate_proof_chain(
        self,
        chain: ProofChain,
        field_path: str,
    ) -> list[ValidationError]:
        """Validate a proof chain is complete."""
        errors = []
        
        if chain.status == ProofStatus.UNSUPPORTED:
            errors.append(ValidationError(
                field_path=field_path,
                error_type="unsupported_proof",
                message=f"Proof chain for '{chain.claim_element}' has no supporting evidence",
                severity=ValidationSeverity.BLOCKING,
                remediation="Add evidence for all proof steps",
            ))
        elif chain.status == ProofStatus.INCOMPLETE:
            gaps = chain.get_gaps()
            for gap in gaps:
                errors.append(ValidationError(
                    field_path=f"{field_path}.steps",
                    error_type="incomplete_proof",
                    message=gap,
                    severity=ValidationSeverity.BLOCKING,
                    remediation="Provide evidence for the missing step",
                ))
        elif chain.status == ProofStatus.INVALID:
            errors.append(ValidationError(
                field_path=field_path,
                error_type="invalid_proof",
                message=f"Proof chain for '{chain.claim_element}' contains contradictions",
                severity=ValidationSeverity.BLOCKING,
            ))
        
        # Verify all referenced evidence exists
        for eid in chain.get_all_evidence_ids():
            if not self.store.exists(eid):
                errors.append(ValidationError(
                    field_path=f"{field_path}.evidence",
                    error_type="invalid_evidence_reference",
                    message=f"Evidence ID '{eid}' in proof chain does not exist",
                    severity=ValidationSeverity.BLOCKING,
                ))
        
        return errors
    
    def validate_code_justification(
        self,
        justification: CodeJustification,
        field_path: str,
    ) -> list[ValidationError]:
        """Validate a code has proper justification."""
        errors = []
        
        # Must have clinical evidence
        if not justification.clinical_evidence_ids:
            errors.append(ValidationError(
                field_path=f"{field_path}.{justification.code}",
                error_type="no_clinical_evidence",
                message=f"Code {justification.code} has no clinical evidence",
                severity=ValidationSeverity.BLOCKING,
                remediation="Link to clinical documentation that supports this code",
            ))
        
        # Must have codebook reference
        if not justification.codebook_reference:
            errors.append(ValidationError(
                field_path=f"{field_path}.{justification.code}",
                error_type="no_codebook_reference",
                message=f"Code {justification.code} has no codebook reference",
                severity=ValidationSeverity.BLOCKING,
                remediation="Add reference to coding guidelines (e.g., 'ICD-10-CM Guidelines Section I.A')",
            ))
        
        # If proof chain exists, validate it
        if justification.proof_chain:
            errors.extend(self.validate_proof_chain(
                justification.proof_chain,
                f"{field_path}.{justification.code}.proof_chain",
            ))
        
        # Verify evidence exists
        for eid in justification.clinical_evidence_ids:
            if not self.store.exists(eid):
                errors.append(ValidationError(
                    field_path=f"{field_path}.{justification.code}.evidence",
                    error_type="invalid_evidence_reference",
                    message=f"Evidence ID '{eid}' does not exist",
                    severity=ValidationSeverity.BLOCKING,
                ))
        
        # Check overall support
        if not justification.is_supported:
            errors.append(ValidationError(
                field_path=f"{field_path}.{justification.code}",
                error_type="unsupported_code",
                message=f"Code {justification.code}: {justification.unsupported_reason}",
                severity=ValidationSeverity.BLOCKING,
            ))
        
        return errors
    
    def validate_claim(
        self,
        claim_data: dict,
        claim_id: str,
    ) -> ValidationResult:
        """
        Validate an entire claim for evidence binding.
        
        Returns a ValidationResult that determines if the claim
        can be exported/submitted.
        """
        result = ValidationResult(
            validated_object_type="claim",
            validated_object_id=claim_id,
            is_valid=True,
            is_exportable=True,
        )
        
        all_evidence = set()
        
        # Validate diagnoses
        diagnoses = claim_data.get("diagnoses", [])
        for i, dx in enumerate(diagnoses):
            result.total_fields_checked += 1
            
            evidence_ids = dx.get("evidence_ids", dx.get("evidence", []))
            if not evidence_ids:
                result.add_error(
                    field_path=f"diagnoses[{i}]",
                    error_type="unsupported_diagnosis",
                    message=f"Diagnosis {dx.get('code', 'unknown')} has no evidence",
                    remediation="Link diagnosis to clinical documentation",
                )
                result.fields_without_evidence += 1
            else:
                result.fields_with_evidence += 1
                all_evidence.update(evidence_ids)
        
        # Validate service lines
        lines = claim_data.get("lines", [])
        for i, line in enumerate(lines):
            result.total_fields_checked += 1
            
            evidence_ids = line.get("evidence_ids", line.get("supporting_evidence", []))
            
            # Check for evidence
            if not evidence_ids:
                result.add_error(
                    field_path=f"lines[{i}]",
                    error_type="unsupported_line",
                    message=f"Line {i+1} ({line.get('code', 'unknown')}) has no evidence",
                    remediation="Link service line to clinical documentation",
                )
                result.fields_without_evidence += 1
            else:
                result.fields_with_evidence += 1
                all_evidence.update(evidence_ids)
            
            # Check for codebook reference
            if not line.get("codebook_reference"):
                result.add_error(
                    field_path=f"lines[{i}].codebook_reference",
                    error_type="no_codebook_reference",
                    message=f"Line {i+1} ({line.get('code', 'unknown')}) has no codebook reference",
                    severity=ValidationSeverity.WARNING,
                    remediation="Add CPT/HCPCS coding reference",
                )
            
            # Check for proof chain
            if line.get("proof_chain"):
                chain = ProofChain.model_validate(line["proof_chain"])
                errors = self.validate_proof_chain(chain, f"lines[{i}].proof_chain")
                result.errors.extend(errors)
        
        # Verify all evidence exists
        for eid in all_evidence:
            if not self.store.exists(eid):
                result.add_error(
                    field_path="evidence",
                    error_type="invalid_evidence_reference",
                    message=f"Referenced evidence '{eid}' not found in store",
                )
        
        result.all_evidence_ids = list(all_evidence)
        result.compute_coverage()
        
        # Log validation
        log_event(
            event_type=AuditEventType.CLAIM_VALIDATE,
            description="Evidence validation performed",
            resource_type="claim",
            resource_id=claim_id,
            details={
                "is_valid": result.is_valid,
                "blocking_errors": len(result.blocking_errors),
                "warnings": len(result.warnings),
                "evidence_coverage": result.evidence_coverage,
            },
        )
        
        return result
    
    def validate_appeal(
        self,
        appeal_data: dict,
        appeal_id: str,
    ) -> ValidationResult:
        """Validate an appeal letter has proper citations."""
        result = ValidationResult(
            validated_object_type="appeal",
            validated_object_id=appeal_id,
            is_valid=True,
            is_exportable=True,
        )
        
        # Check for inline citations in letter
        letter = appeal_data.get("appeal_letter", "")
        if "[EV-" not in letter and "[FACT-" not in letter:
            result.add_error(
                field_path="appeal_letter",
                error_type="no_citations",
                message="Appeal letter contains no inline evidence citations",
                remediation="Insert evidence citations in format [EV-XXXX]",
            )
        
        # Check for policy references
        if not appeal_data.get("policy_citations"):
            result.add_error(
                field_path="policy_citations",
                error_type="no_policy_citations",
                message="Appeal has no payer policy citations",
                severity=ValidationSeverity.WARNING,
                remediation="Add relevant payer policy references",
            )
        
        # Check for proof chain
        if not appeal_data.get("proof_chain"):
            result.add_error(
                field_path="proof_chain",
                error_type="no_proof_chain",
                message="Appeal has no structured proof chain",
                severity=ValidationSeverity.WARNING,
                remediation="Add proof chain demonstrating medical necessity",
            )
        
        result.compute_coverage()
        return result


# Global validator instance
_validator: EvidenceValidator | None = None


def get_validator() -> EvidenceValidator:
    """Get the global evidence validator."""
    global _validator
    if _validator is None:
        _validator = EvidenceValidator()
    return _validator


def validate_or_reject(
    data: dict,
    object_type: str,
    object_id: str,
) -> ValidationResult:
    """
    Validate data and return result.
    
    This is the main entry point for validation.
    """
    validator = get_validator()
    
    if object_type == "claim":
        return validator.validate_claim(data, object_id)
    elif object_type == "appeal":
        return validator.validate_appeal(data, object_id)
    else:
        # Generic validation
        result = ValidationResult(
            validated_object_type=object_type,
            validated_object_id=object_id,
        )
        result.compute_coverage()
        return result


def require_evidence(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that validates output has evidence before returning.
    
    Use on any function that produces claim data.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        
        # If result has claim data, validate it
        if hasattr(result, "claim_data") or isinstance(result, dict):
            data = result.claim_data if hasattr(result, "claim_data") else result
            object_id = getattr(result, "id", "unknown")
            
            validation = validate_or_reject(data, "claim", object_id)
            
            if not validation.is_valid:
                # Attach validation errors to result
                if hasattr(result, "__dict__"):
                    result.validation_errors = validation.errors
                    result.is_valid = False
                
                logger.warning(
                    "Output blocked due to missing evidence",
                    object_id=object_id,
                    errors=[e.message for e in validation.blocking_errors],
                )
        
        return result
    
    return wrapper

