"""
Denials and Appeals API Routes

Endpoints for:
- Denial classification and analysis
- Appeal letter generation
- Appeal tracking
"""

from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.core.security import (
    get_current_user,
    require_permission,
    Permission,
    TokenPayload,
    generate_secure_id,
)
from app.core.audit import log_event, AuditEventType
from app.core.database import get_session, Denial, Appeal, Claim
from app.core.llm import get_llm_client, SystemPrompts
from app.core.knowledge import get_knowledge_base

logger = structlog.get_logger(__name__)

router = APIRouter()


# Models

class DenialCategory(str):
    MEDICAL_NECESSITY = "medical_necessity"
    CODING = "coding"
    COVERAGE = "coverage"
    AUTHORIZATION = "authorization"
    DOCUMENTATION = "documentation"
    TIMELY_FILING = "timely_filing"
    DUPLICATE = "duplicate"
    OTHER = "other"


class RecordDenialRequest(BaseModel):
    """Request to record a new denial."""
    claim_id: str
    denial_date: datetime
    denial_code: str | None = None  # CARC/RARC code
    denial_reason: str
    denied_amount: float


class DenialAnalysis(BaseModel):
    """AI analysis of a denial."""
    category: str
    category_confidence: float
    
    root_cause: str
    policy_references: list[str] = []
    
    is_appealable: bool
    appeal_likelihood: float  # 0-1
    appeal_rationale: str
    
    recommended_actions: list[str] = []
    required_documentation: list[str] = []


class DenialResponse(BaseModel):
    """Full denial response."""
    id: str
    claim_id: str
    
    denial_date: datetime
    denial_code: str | None = None
    denial_reason: str
    denial_category: str
    denied_amount: float
    
    # Analysis
    analysis: DenialAnalysis | None = None
    appeal_likelihood: float | None = None
    
    # Appeal status
    has_appeal: bool = False
    appeal_status: str | None = None
    
    created_at: datetime


class GenerateAppealRequest(BaseModel):
    """Request to generate an appeal letter."""
    denial_id: str
    additional_context: str | None = None  # Extra info from user
    appeal_level: int = 1  # 1st, 2nd, 3rd level appeal


class AppealResponse(BaseModel):
    """Appeal response with generated letter."""
    id: str
    denial_id: str
    claim_id: str
    
    appeal_level: int
    status: str
    
    # Generated content
    appeal_letter: str
    supporting_arguments: list[str] = []
    citations: list[dict] = []
    
    # Tracking
    submission_date: datetime | None = None
    response_date: datetime | None = None
    outcome: str | None = None
    
    created_at: datetime


@router.post("/", response_model=DenialResponse, status_code=status.HTTP_201_CREATED)
async def record_denial(
    request: RecordDenialRequest,
    user: TokenPayload = Depends(require_permission(Permission.DENIAL_READ)),
):
    """
    Record a denial and analyze it.
    
    Automatically:
    1. Classifies the denial reason
    2. Identifies policy references
    3. Assesses appeal likelihood
    4. Recommends next steps
    """
    # Verify claim exists
    async with get_session() as session:
        from sqlalchemy import select
        stmt = select(Claim).where(Claim.id == request.claim_id)
        result = await session.execute(stmt)
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Claim not found",
            )
    
    # Analyze the denial using LLM
    analysis = await _analyze_denial(
        denial_reason=request.denial_reason,
        denial_code=request.denial_code,
        claim_data=claim.claim_data,
    )
    
    # Create denial record
    denial_id = generate_secure_id()
    
    async with get_session() as session:
        denial = Denial(
            id=denial_id,
            claim_id=request.claim_id,
            denial_date=request.denial_date,
            denial_code=request.denial_code,
            denial_reason=request.denial_reason,
            denial_category=analysis.category,
            denied_amount=request.denied_amount,
            ai_analysis=analysis.model_dump(),
            appeal_likelihood=analysis.appeal_likelihood,
        )
        session.add(denial)
        
        # Update claim status
        claim.status = "denied"
        session.add(claim)
        
        await session.commit()
    
    log_event(
        event_type=AuditEventType.DENIAL_REVIEW,
        description="Denial recorded and analyzed",
        user_id=user.sub,
        resource_type="denial",
        resource_id=denial_id,
        details={
            "claim_id": request.claim_id,
            "category": analysis.category,
            "appeal_likelihood": analysis.appeal_likelihood,
        },
    )
    
    return DenialResponse(
        id=denial_id,
        claim_id=request.claim_id,
        denial_date=request.denial_date,
        denial_code=request.denial_code,
        denial_reason=request.denial_reason,
        denial_category=analysis.category,
        denied_amount=request.denied_amount,
        analysis=analysis,
        appeal_likelihood=analysis.appeal_likelihood,
        created_at=datetime.now(timezone.utc),
    )


async def _analyze_denial(
    denial_reason: str,
    denial_code: str | None,
    claim_data: dict | None,
) -> DenialAnalysis:
    """Analyze a denial using the LLM."""
    llm = get_llm_client()
    knowledge = get_knowledge_base()
    
    # Search for relevant policies
    policy_results = await knowledge.search_policies(denial_reason, limit=3)
    policy_context = "\n".join([
        f"- {p.title}: {p.content_snippet[:200]}"
        for p in policy_results
    ])
    
    prompt = f"""Analyze this claim denial:

DENIAL REASON: {denial_reason}
DENIAL CODE: {denial_code or "Not provided"}

CLAIM INFORMATION:
{str(claim_data)[:1500] if claim_data else "Not available"}

RELEVANT POLICIES:
{policy_context or "No specific policies found"}

Provide:
1. Category classification (medical_necessity, coding, coverage, authorization, documentation, timely_filing, duplicate, other)
2. Root cause analysis
3. Whether this is appealable and likelihood of success (0-1)
4. Recommended actions
5. Required documentation for appeal

Format as JSON:
{{
  "category": "string",
  "category_confidence": 0.0-1.0,
  "root_cause": "explanation",
  "policy_references": ["policy1", "policy2"],
  "is_appealable": true/false,
  "appeal_likelihood": 0.0-1.0,
  "appeal_rationale": "why appeal may/may not succeed",
  "recommended_actions": ["action1", "action2"],
  "required_documentation": ["doc1", "doc2"]
}}"""

    try:
        response = await llm.generate(
            prompt=prompt,
            system_prompt=SystemPrompts.DENIAL_ANALYST,
            temperature=0.1,
            json_mode=True,
        )
        
        import json
        data = json.loads(response.content)
        
        return DenialAnalysis(
            category=data.get("category", "other"),
            category_confidence=data.get("category_confidence", 0.7),
            root_cause=data.get("root_cause", "Unable to determine"),
            policy_references=data.get("policy_references", []),
            is_appealable=data.get("is_appealable", True),
            appeal_likelihood=data.get("appeal_likelihood", 0.5),
            appeal_rationale=data.get("appeal_rationale", ""),
            recommended_actions=data.get("recommended_actions", []),
            required_documentation=data.get("required_documentation", []),
        )
        
    except Exception as e:
        logger.error("Denial analysis failed", error=str(e))
        return DenialAnalysis(
            category="other",
            category_confidence=0.5,
            root_cause="Analysis failed - manual review required",
            is_appealable=True,
            appeal_likelihood=0.5,
            appeal_rationale="Unable to analyze automatically",
        )


@router.post("/appeals/generate", response_model=AppealResponse)
async def generate_appeal(
    request: GenerateAppealRequest,
    user: TokenPayload = Depends(require_permission(Permission.DENIAL_APPEAL)),
):
    """
    Generate an appeal letter for a denial.
    
    Creates a professionally formatted appeal with:
    - Specific policy citations
    - Clinical evidence references
    - Clear request for reconsideration
    """
    # Get denial and claim data
    async with get_session() as session:
        from sqlalchemy import select
        
        stmt = select(Denial).where(Denial.id == request.denial_id)
        result = await session.execute(stmt)
        denial = result.scalar_one_or_none()
        
        if not denial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Denial not found",
            )
        
        stmt = select(Claim).where(Claim.id == denial.claim_id)
        result = await session.execute(stmt)
        claim = result.scalar_one_or_none()
    
    # Generate appeal letter
    llm = get_llm_client()
    knowledge = get_knowledge_base()
    
    # Get relevant policies
    policies = await knowledge.search_policies(
        denial.denial_reason,
        limit=5,
    )
    
    policy_text = "\n".join([
        f"Policy: {p.title}\nContent: {p.content_snippet}"
        for p in policies
    ])
    
    # Get claim codes for reference
    claim_data = claim.claim_data or {}
    diagnoses = claim_data.get("diagnoses", [])
    procedures = claim_data.get("lines", [])
    
    codes_text = "Diagnosis Codes:\n" + "\n".join([
        f"- {d.get('code')}: {d.get('description')}"
        for d in diagnoses
    ])
    codes_text += "\n\nProcedure Codes:\n" + "\n".join([
        f"- {p.get('code')}: {p.get('description')}"
        for p in procedures
    ])
    
    prompt = f"""Generate a professional appeal letter for this denied claim.

DENIAL INFORMATION:
- Denial Date: {denial.denial_date.strftime("%B %d, %Y")}
- Denial Code: {denial.denial_code or "Not specified"}
- Denial Reason: {denial.denial_reason}
- Denied Amount: ${denial.denied_amount:.2f}

CLAIM CODES:
{codes_text}

RELEVANT PAYER POLICIES:
{policy_text}

ADDITIONAL CONTEXT:
{request.additional_context or "None provided"}

APPEAL LEVEL: {request.appeal_level}

Generate a formal appeal letter that:
1. Identifies the patient and claim
2. States the specific denial reason being appealed
3. Provides clinical justification with evidence
4. Cites relevant payer policies
5. Requests specific action (payment, reconsideration)

The letter should be professional, factual, and persuasive.
Include [PLACEHOLDER] markers for patient-specific information.

Also provide a JSON summary of supporting arguments and citations.

FORMAT:
===LETTER===
(Full letter text)
===END_LETTER===

===SUMMARY===
{{
  "supporting_arguments": ["arg1", "arg2"],
  "citations": [{{"source": "name", "reference": "text"}}]
}}
===END_SUMMARY==="""

    try:
        response = await llm.generate(
            prompt=prompt,
            system_prompt=SystemPrompts.APPEAL_WRITER,
            temperature=0.3,  # Slightly higher for better writing
            max_tokens=3000,
        )
        
        content = response.content
        
        # Parse letter and summary
        import re
        letter_match = re.search(r"===LETTER===(.*?)===END_LETTER===", content, re.DOTALL)
        summary_match = re.search(r"===SUMMARY===(.*?)===END_SUMMARY===", content, re.DOTALL)
        
        letter = letter_match.group(1).strip() if letter_match else content
        
        supporting_arguments = []
        citations = []
        
        if summary_match:
            try:
                import json
                summary = json.loads(summary_match.group(1).strip())
                supporting_arguments = summary.get("supporting_arguments", [])
                citations = summary.get("citations", [])
            except:
                pass
        
    except Exception as e:
        logger.error("Appeal generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate appeal letter",
        )
    
    # Save appeal
    appeal_id = generate_secure_id()
    
    async with get_session() as session:
        appeal = Appeal(
            id=appeal_id,
            denial_id=request.denial_id,
            claim_id=denial.claim_id,
            appeal_level=request.appeal_level,
            status="draft",
            appeal_letter=letter,
            supporting_arguments={"arguments": supporting_arguments},
            citations=citations,
        )
        session.add(appeal)
        await session.commit()
    
    log_event(
        event_type=AuditEventType.APPEAL_GENERATE,
        description="Appeal letter generated",
        user_id=user.sub,
        resource_type="appeal",
        resource_id=appeal_id,
        details={
            "denial_id": request.denial_id,
            "appeal_level": request.appeal_level,
        },
    )
    
    return AppealResponse(
        id=appeal_id,
        denial_id=request.denial_id,
        claim_id=denial.claim_id,
        appeal_level=request.appeal_level,
        status="draft",
        appeal_letter=letter,
        supporting_arguments=supporting_arguments,
        citations=citations,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/{denial_id}", response_model=DenialResponse)
async def get_denial(
    denial_id: str,
    user: TokenPayload = Depends(require_permission(Permission.DENIAL_READ)),
):
    """Get a denial by ID."""
    async with get_session() as session:
        from sqlalchemy import select
        
        stmt = select(Denial).where(Denial.id == denial_id)
        result = await session.execute(stmt)
        denial = result.scalar_one_or_none()
        
        if not denial:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Denial not found",
            )
        
        # Check for appeals
        stmt = select(Appeal).where(Appeal.denial_id == denial_id)
        result = await session.execute(stmt)
        appeal = result.scalar_one_or_none()
        
        analysis = None
        if denial.ai_analysis:
            analysis = DenialAnalysis(**denial.ai_analysis)
        
        return DenialResponse(
            id=denial.id,
            claim_id=denial.claim_id,
            denial_date=denial.denial_date,
            denial_code=denial.denial_code,
            denial_reason=denial.denial_reason,
            denial_category=denial.denial_category,
            denied_amount=denial.denied_amount,
            analysis=analysis,
            appeal_likelihood=denial.appeal_likelihood,
            has_appeal=appeal is not None,
            appeal_status=appeal.status if appeal else None,
            created_at=denial.created_at,
        )


@router.get("/appeals/{appeal_id}", response_model=AppealResponse)
async def get_appeal(
    appeal_id: str,
    user: TokenPayload = Depends(require_permission(Permission.DENIAL_READ)),
):
    """Get an appeal by ID."""
    async with get_session() as session:
        from sqlalchemy import select
        
        stmt = select(Appeal).where(Appeal.id == appeal_id)
        result = await session.execute(stmt)
        appeal = result.scalar_one_or_none()
        
        if not appeal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appeal not found",
            )
        
        return AppealResponse(
            id=appeal.id,
            denial_id=appeal.denial_id,
            claim_id=appeal.claim_id,
            appeal_level=appeal.appeal_level,
            status=appeal.status,
            appeal_letter=appeal.appeal_letter or "",
            supporting_arguments=appeal.supporting_arguments.get("arguments", []) if appeal.supporting_arguments else [],
            citations=appeal.citations or [],
            submission_date=appeal.submission_date,
            response_date=appeal.response_date,
            outcome=appeal.outcome,
            created_at=appeal.created_at,
        )

