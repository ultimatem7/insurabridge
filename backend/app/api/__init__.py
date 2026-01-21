"""
API Routes

RESTful API for Insurabridge.
All routes require authentication except health checks.

Evidence-Bound Generation: All claim endpoints now require evidence citations.
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.denials import router as denials_router
from app.api.audit import router as audit_router
from app.api.codes import router as codes_router
from app.api.evidence import router as evidence_router
from app.api.fhir_import import router as fhir_router
from app.api.demo import router as demo_router
from app.api.pipeline import router as pipeline_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(evidence_router, prefix="/evidence", tags=["Evidence"])
router.include_router(fhir_router, tags=["FHIR Import"])
router.include_router(claims_router, prefix="/claims", tags=["Claims"])
router.include_router(denials_router, prefix="/denials", tags=["Denials & Appeals"])
router.include_router(audit_router, prefix="/audit", tags=["Audit"])
router.include_router(codes_router, prefix="/codes", tags=["Code Lookup"])
router.include_router(demo_router, prefix="/demo", tags=["Demo Data"])
router.include_router(pipeline_router, prefix="/pipeline", tags=["Pipeline"])

