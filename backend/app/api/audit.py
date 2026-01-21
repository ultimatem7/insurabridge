"""
Audit API Routes

Endpoints for:
- Audit log queries
- Compliance reports
- Risk assessment
"""

from datetime import datetime, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.core.security import (
    require_permission,
    Permission,
    TokenPayload,
)
from app.core.audit import (
    audit_log,
    AuditEventType,
    AuditEntry,
    log_event,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


class AuditEntryResponse(BaseModel):
    """Audit entry for API response."""
    id: str
    timestamp: datetime
    event_type: str
    event_description: str
    user_id: str | None = None
    user_role: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    success: bool
    error_message: str | None = None


class AuditQueryResponse(BaseModel):
    """Response for audit log query."""
    entries: list[AuditEntryResponse]
    total: int
    chain_valid: bool | None = None


class AuditRiskReport(BaseModel):
    """Audit risk assessment report."""
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Summary stats
    total_claims: int
    claims_with_issues: int
    issue_rate: float
    
    # Risk categories
    high_risk_claims: list[str]
    overcoding_flags: int
    undercoding_flags: int
    documentation_gaps: int
    
    # Recommendations
    recommendations: list[str]


@router.get("/logs", response_model=AuditQueryResponse)
async def query_audit_logs(
    event_types: Annotated[list[str] | None, Query()] = None,
    user_id: str | None = None,
    resource_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    user: TokenPayload = Depends(require_permission(Permission.AUDIT_READ)),
):
    """
    Query audit logs with filters.
    
    Requires AUDIT_READ permission.
    """
    # Convert string event types to enum
    event_type_enums = None
    if event_types:
        event_type_enums = []
        for et in event_types:
            try:
                event_type_enums.append(AuditEventType(et))
            except ValueError:
                pass
    
    entries = audit_log.query(
        event_types=event_type_enums,
        user_id=user_id,
        resource_id=resource_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    
    # Log that audit was queried
    log_event(
        event_type=AuditEventType.AUDIT_QUERY,
        description="Audit log queried",
        user_id=user.sub,
        details={
            "filters": {
                "event_types": event_types,
                "user_id": user_id,
                "resource_id": resource_id,
            },
            "results": len(entries),
        },
    )
    
    return AuditQueryResponse(
        entries=[
            AuditEntryResponse(
                id=e.id,
                timestamp=e.timestamp,
                event_type=e.event_type.value,
                event_description=e.event_description,
                user_id=e.user_id,
                user_role=e.user_role,
                resource_type=e.resource_type,
                resource_id=e.resource_id,
                success=e.success,
                error_message=e.error_message,
            )
            for e in entries
        ],
        total=len(entries),
    )


@router.get("/verify-chain")
async def verify_audit_chain(
    user: TokenPayload = Depends(require_permission(Permission.AUDIT_READ)),
):
    """
    Verify the integrity of the audit log chain.
    
    Checks cryptographic hashes to detect tampering.
    """
    is_valid, issues = audit_log.verify_chain()
    
    log_event(
        event_type=AuditEventType.AUDIT_QUERY,
        description="Audit chain verification",
        user_id=user.sub,
        details={
            "is_valid": is_valid,
            "issues_count": len(issues),
        },
    )
    
    return {
        "is_valid": is_valid,
        "issues": issues[:10] if issues else [],  # Limit exposed issues
        "verified_at": datetime.now(timezone.utc),
    }


@router.get("/risk-report", response_model=AuditRiskReport)
async def generate_risk_report(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    user: TokenPayload = Depends(require_permission(Permission.AUDIT_EXPORT)),
):
    """
    Generate a compliance risk assessment report.
    
    Analyzes claims and coding patterns for audit risk.
    """
    from app.core.database import get_session, Claim
    from sqlalchemy import select, func
    
    now = datetime.now(timezone.utc)
    start = start_date or now.replace(day=1)
    end = end_date or now
    
    async with get_session() as session:
        # Get claims in period
        stmt = select(Claim).where(
            Claim.created_at >= start,
            Claim.created_at <= end,
        )
        result = await session.execute(stmt)
        claims = result.scalars().all()
        
        total_claims = len(claims)
        
        # Analyze for issues
        high_risk = []
        overcoding = 0
        undercoding = 0
        doc_gaps = 0
        
        for claim in claims:
            reasoning = claim.reasoning_chain or {}
            issues = reasoning.get("compliance_issues", [])
            
            if issues:
                high_risk.append(claim.id)
            
            # Check confidence
            if claim.confidence_score and claim.confidence_score < 0.6:
                doc_gaps += 1
            
            # Simplified analysis - in production, would be more sophisticated
            claim_data = claim.claim_data or {}
            lines = claim_data.get("lines", [])
            for line in lines:
                conf = line.get("confidence_score", 1.0)
                if conf < 0.5:
                    undercoding += 1
    
    claims_with_issues = len(high_risk)
    issue_rate = claims_with_issues / total_claims if total_claims > 0 else 0
    
    recommendations = []
    if issue_rate > 0.2:
        recommendations.append("High issue rate detected - consider coder training")
    if doc_gaps > 5:
        recommendations.append("Documentation gaps identified - review clinical note quality")
    if overcoding > 0:
        recommendations.append("Overcoding flags detected - audit high-value claims")
    
    log_event(
        event_type=AuditEventType.AUDIT_EXPORT,
        description="Risk report generated",
        user_id=user.sub,
        details={
            "period": f"{start.date()} to {end.date()}",
            "total_claims": total_claims,
            "issue_rate": issue_rate,
        },
    )
    
    return AuditRiskReport(
        generated_at=now,
        period_start=start,
        period_end=end,
        total_claims=total_claims,
        claims_with_issues=claims_with_issues,
        issue_rate=issue_rate,
        high_risk_claims=high_risk[:20],
        overcoding_flags=overcoding,
        undercoding_flags=undercoding,
        documentation_gaps=doc_gaps,
        recommendations=recommendations,
    )

