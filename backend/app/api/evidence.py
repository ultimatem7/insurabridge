"""
Evidence API Routes

Endpoints for:
- Evidence upload and extraction
- Evidence atom retrieval
- Fact extraction
- Proof chain inspection
"""

import io
from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Query
from pydantic import BaseModel, Field

from app.core.security import (
    get_current_user,
    require_permission,
    Permission,
    TokenPayload,
)
from app.core.audit import log_event, AuditEventType
from app.evidence.atoms import (
    EvidenceAtom,
    EvidenceType,
    SourceSystem,
    get_evidence_store,
)
from app.evidence.extractor import get_evidence_extractor, ExtractionResult
from app.evidence.facts import get_fact_extractor, Fact, FactExtractionResult
from app.evidence.proofs import ProofChain, ProofStatus
from app.evidence.validator import ValidationResult, get_validator

logger = structlog.get_logger(__name__)

router = APIRouter()


# Response Models

class EvidenceAtomResponse(BaseModel):
    """Evidence atom for API response."""
    evidence_id: str
    evidence_type: str
    source_system: str
    document_name: str
    content_excerpt: str
    location: dict
    extraction_confidence: float
    created_at: datetime
    citation: str


class EvidenceExtractionResponse(BaseModel):
    """Response from evidence extraction."""
    document_id: str
    document_name: str
    atoms_created: int
    atom_ids: list[str]
    warnings: list[str]


class FactResponse(BaseModel):
    """Fact for API response."""
    fact_id: str
    fact_text: str
    fact_type: str
    evidence_id: str
    is_literal: bool
    extraction_confidence: float


class FactExtractionResponse(BaseModel):
    """Response from fact extraction."""
    facts: list[FactResponse]
    rejected_count: int
    rejection_reasons: list[str]
    success_rate: float


class ProofChainResponse(BaseModel):
    """Proof chain for API response."""
    chain_id: str
    claim_element: str
    status: str
    is_valid: bool
    total_steps: int
    steps_with_evidence: int
    gaps: list[str]
    overall_confidence: float
    narrative: str


@router.post("/extract", response_model=EvidenceExtractionResponse)
async def extract_evidence_from_document(
    file: Annotated[UploadFile, File(description="Document to extract evidence from")],
    user: TokenPayload = Depends(require_permission(Permission.CLAIM_CREATE)),
):
    """
    Extract evidence atoms from an uploaded document.
    
    The document is parsed, chunked into citation-safe units,
    and stored as immutable EvidenceAtoms.
    
    All downstream processing uses these atoms as the source of truth.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    
    extractor = get_evidence_extractor()
    
    try:
        content = await file.read()
        result = extractor.extract_from_file(
            file=io.BytesIO(content),
            filename=file.filename,
            source_system=SourceSystem.MANUAL_UPLOAD,
        )
    except Exception as e:
        logger.error("Evidence extraction failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract evidence: {str(e)}",
        )
    
    log_event(
        event_type=AuditEventType.PHI_CREATE,
        description="Evidence extracted from document",
        user_id=user.sub,
        resource_type="document",
        resource_id=result.document_id,
        details={
            "filename": file.filename,
            "atoms_created": result.atoms_created,
        },
    )
    
    return EvidenceExtractionResponse(
        document_id=result.document_id,
        document_name=file.filename,
        atoms_created=result.atoms_created,
        atom_ids=result.atoms,
        warnings=result.extraction_warnings,
    )


@router.post("/extract/text", response_model=EvidenceExtractionResponse)
async def extract_evidence_from_text(
    text: str,
    document_name: str = "Clinical Notes",
    user: TokenPayload = Depends(require_permission(Permission.CLAIM_CREATE)),
):
    """
    Extract evidence atoms from raw text.
    
    Use this for pasting clinical notes directly.
    """
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )
    
    extractor = get_evidence_extractor()
    
    result = extractor.extract_from_text(
        text=text,
        document_name=document_name,
        source_system=SourceSystem.MANUAL_UPLOAD,
    )
    
    log_event(
        event_type=AuditEventType.PHI_CREATE,
        description="Evidence extracted from text",
        user_id=user.sub,
        resource_type="text",
        resource_id=result.document_id,
        details={
            "text_length": len(text),
            "atoms_created": result.atoms_created,
        },
    )
    
    return EvidenceExtractionResponse(
        document_id=result.document_id,
        document_name=document_name,
        atoms_created=result.atoms_created,
        atom_ids=result.atoms,
        warnings=result.extraction_warnings,
    )


@router.get("/atoms/{evidence_id}", response_model=EvidenceAtomResponse)
async def get_evidence_atom(
    evidence_id: str,
    user: TokenPayload = Depends(get_current_user),
):
    """Get a single evidence atom by ID."""
    store = get_evidence_store()
    atom = store.get(evidence_id)
    
    if not atom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence atom {evidence_id} not found",
        )
    
    log_event(
        event_type=AuditEventType.PHI_VIEW,
        description="Evidence atom viewed",
        user_id=user.sub,
        resource_type="evidence",
        resource_id=evidence_id,
    )
    
    return EvidenceAtomResponse(
        evidence_id=atom.evidence_id,
        evidence_type=atom.evidence_type.value,
        source_system=atom.source_system.value,
        document_name=atom.document_name,
        content_excerpt=atom.content_excerpt,
        location=atom.location.model_dump(),
        extraction_confidence=atom.extraction_confidence,
        created_at=atom.created_at,
        citation=atom.to_citation(),
    )


@router.get("/atoms", response_model=list[EvidenceAtomResponse])
async def list_evidence_atoms(
    document_id: str | None = None,
    evidence_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    user: TokenPayload = Depends(get_current_user),
):
    """List evidence atoms with optional filters."""
    store = get_evidence_store()
    
    if document_id:
        atoms = store.get_by_document(document_id)
    elif evidence_type:
        try:
            et = EvidenceType(evidence_type)
            atoms = store.get_by_type(et)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid evidence type: {evidence_type}",
            )
    else:
        # Get recent atoms (in production, use proper pagination)
        atoms = list(store._atoms.values())[-limit:]
    
    return [
        EvidenceAtomResponse(
            evidence_id=a.evidence_id,
            evidence_type=a.evidence_type.value,
            source_system=a.source_system.value,
            document_name=a.document_name,
            content_excerpt=a.content_excerpt[:500],  # Truncate for listing
            location=a.location.model_dump(),
            extraction_confidence=a.extraction_confidence,
            created_at=a.created_at,
            citation=a.to_citation(),
        )
        for a in atoms[:limit]
    ]


@router.post("/facts/extract", response_model=FactExtractionResponse)
async def extract_facts(
    evidence_ids: list[str],
    user: TokenPayload = Depends(require_permission(Permission.CLAIM_CREATE)),
):
    """
    Extract literal facts from evidence atoms.
    
    Each fact is tied to exactly one evidence atom.
    Facts that cannot be verified against source are rejected.
    """
    if not evidence_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one evidence ID is required",
        )
    
    store = get_evidence_store()
    atoms = store.get_many(evidence_ids)
    
    if not atoms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid evidence atoms found",
        )
    
    extractor = get_fact_extractor()
    result = await extractor.extract_facts(atoms)
    
    log_event(
        event_type=AuditEventType.LLM_REASONING,
        description="Facts extracted from evidence",
        user_id=user.sub,
        details={
            "evidence_count": len(atoms),
            "facts_extracted": len(result.facts),
            "rejected": len(result.rejected_extractions),
        },
    )
    
    return FactExtractionResponse(
        facts=[
            FactResponse(
                fact_id=f.fact_id,
                fact_text=f.fact_text,
                fact_type=f.fact_type,
                evidence_id=f.evidence_id,
                is_literal=f.is_literal,
                extraction_confidence=f.extraction_confidence,
            )
            for f in result.facts
        ],
        rejected_count=len(result.rejected_extractions),
        rejection_reasons=[r.get("reason", "") for r in result.rejected_extractions],
        success_rate=result.success_rate,
    )


@router.post("/validate", response_model=dict)
async def validate_evidence_binding(
    claim_data: dict,
    claim_id: str,
    user: TokenPayload = Depends(require_permission(Permission.CLAIM_READ)),
):
    """
    Validate that claim data has proper evidence binding.
    
    Returns validation result with any blocking errors.
    Claims with blocking errors cannot be exported.
    """
    validator = get_validator()
    result = validator.validate_claim(claim_data, claim_id)
    
    return {
        "is_valid": result.is_valid,
        "is_exportable": result.is_exportable,
        "evidence_coverage": result.evidence_coverage,
        "blocking_errors": [
            {
                "field": e.field_path,
                "error": e.message,
                "remediation": e.remediation,
            }
            for e in result.blocking_errors
        ],
        "warnings": [
            {
                "field": e.field_path,
                "warning": e.message,
            }
            for e in result.warnings
        ],
        "total_evidence": len(result.all_evidence_ids),
    }


@router.get("/store/stats")
async def get_evidence_store_stats(
    user: TokenPayload = Depends(get_current_user),
):
    """Get statistics about the evidence store."""
    store = get_evidence_store()
    
    valid, invalid = store.verify_all()
    
    return {
        "total_atoms": store.count(),
        "valid_atoms": valid,
        "invalid_atoms": len(invalid),
        "integrity_verified": len(invalid) == 0,
    }

