"""
Evidence-Bound Generation (EBG) System

This module implements the core constraint:
ALL outputs must be traceable to primary source evidence.

The system is structurally incapable of generating unsupported claims.

Core components:
- EvidenceAtom: Immutable unit of provenance
- EvidenceExtractor: Converts documents to EvidenceAtoms
- FactExtractor: Extracts literal facts with evidence binding
- ProofChain: Structured reasoning with mandatory citations
- EvidenceValidator: Blocks any unsupported output
"""

from app.evidence.atoms import (
    EvidenceAtom,
    EvidenceType,
    SourceSystem,
    EvidenceLocation,
    EvidenceStore,
    get_evidence_store,
    create_evidence_atom,
)

from app.evidence.extractor import (
    EvidenceExtractor,
    ExtractionResult,
    get_evidence_extractor,
)

from app.evidence.facts import (
    Fact,
    FactExtractor,
    FactExtractionResult,
    get_fact_extractor,
)

from app.evidence.proofs import (
    ProofStep,
    ProofChain,
    ProofStatus,
    MedicalNecessityProof,
    ProofChainBuilder,
    CodeJustification,
)

from app.evidence.validator import (
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    EvidenceBoundValue,
    EvidenceValidator,
    validate_or_reject,
    get_validator,
    require_evidence,
)

__all__ = [
    # Atoms
    "EvidenceAtom",
    "EvidenceType",
    "SourceSystem",
    "EvidenceLocation",
    "EvidenceStore",
    "get_evidence_store",
    "create_evidence_atom",
    # Extractor
    "EvidenceExtractor",
    "ExtractionResult",
    "get_evidence_extractor",
    # Facts
    "Fact",
    "FactExtractor",
    "FactExtractionResult",
    "get_fact_extractor",
    # Proofs
    "ProofStep",
    "ProofChain",
    "ProofStatus",
    "MedicalNecessityProof",
    "ProofChainBuilder",
    "CodeJustification",
    # Validation
    "ValidationResult",
    "ValidationError",
    "ValidationSeverity",
    "EvidenceBoundValue",
    "EvidenceValidator",
    "validate_or_reject",
    "get_validator",
    "require_evidence",
]

