"""
Code Lookup API Routes

Endpoints for:
- ICD-10 code search
- CPT code search
- HCPCS code search
- NCCI edit checking
"""

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.core.security import get_current_user, TokenPayload
from app.core.knowledge import (
    get_knowledge_base,
    CodeSearchResult,
    NCCICheckResult,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


class CodeSearchResponse(BaseModel):
    """Response for code search."""
    results: list[CodeSearchResult]
    query: str
    total: int


class NCCICheckRequest(BaseModel):
    """Request to check NCCI edits."""
    codes: list[str]


class NCCICheckResponse(BaseModel):
    """Response for NCCI edit check."""
    checks: list[NCCICheckResult]
    has_issues: bool


@router.get("/icd10", response_model=CodeSearchResponse)
async def search_icd10(
    q: str = Query(..., min_length=2, description="Search query"),
    code_type: str | None = Query(None, description="CM or PCS"),
    limit: int = Query(10, ge=1, le=50),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Search ICD-10-CM/PCS codes.
    
    Supports:
    - Code lookup (e.g., "I10")
    - Description search (e.g., "hypertension")
    - Partial matching
    """
    knowledge = get_knowledge_base()
    
    results = await knowledge.search_icd10(
        query=q,
        code_type=code_type,
        limit=limit,
    )
    
    return CodeSearchResponse(
        results=results,
        query=q,
        total=len(results),
    )


@router.get("/cpt", response_model=CodeSearchResponse)
async def search_cpt(
    q: str = Query(..., min_length=2, description="Search query"),
    section: str | None = Query(None, description="CPT section filter"),
    limit: int = Query(10, ge=1, le=50),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Search CPT codes.
    
    Supports:
    - Code lookup (e.g., "99213")
    - Description search (e.g., "office visit")
    """
    knowledge = get_knowledge_base()
    
    results = await knowledge.search_cpt(
        query=q,
        section=section,
        limit=limit,
    )
    
    return CodeSearchResponse(
        results=results,
        query=q,
        total=len(results),
    )


@router.get("/hcpcs", response_model=CodeSearchResponse)
async def search_hcpcs(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Search HCPCS Level II codes.
    
    Supports:
    - Code lookup (e.g., "J1234")
    - Description search (e.g., "injection")
    """
    knowledge = get_knowledge_base()
    
    results = await knowledge.search_hcpcs(
        query=q,
        limit=limit,
    )
    
    return CodeSearchResponse(
        results=results,
        query=q,
        total=len(results),
    )


@router.post("/ncci-check", response_model=NCCICheckResponse)
async def check_ncci_edits(
    request: NCCICheckRequest,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Check NCCI edit compatibility between codes.
    
    Checks all pairs of provided codes for bundling conflicts.
    """
    if len(request.codes) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 codes required for NCCI check",
        )
    
    if len(request.codes) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 codes allowed per check",
        )
    
    knowledge = get_knowledge_base()
    checks = []
    has_issues = False
    
    # Check all pairs
    for i, code1 in enumerate(request.codes):
        for code2 in request.codes[i+1:]:
            result = await knowledge.check_ncci_edit(code1, code2)
            if result:
                checks.append(result)
                if not result.is_allowed:
                    has_issues = True
    
    return NCCICheckResponse(
        checks=checks,
        has_issues=has_issues,
    )


@router.get("/mue/{code}")
async def get_mue_limit(
    code: str,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get MUE (Medically Unlikely Edit) limit for a code.
    
    Returns the maximum units typically allowed per date of service.
    """
    knowledge = get_knowledge_base()
    
    mue = await knowledge.get_mue(code)
    
    return {
        "code": code,
        "mue_limit": mue,
        "has_limit": mue is not None,
    }

