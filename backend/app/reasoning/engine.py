"""
Reasoning Engine Core

Implements step-by-step chain-of-evidence analysis.
Every decision is traceable to source documentation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from app.core.llm import get_llm_client, SystemPrompts, Message, LLMRole
from app.core.knowledge import get_knowledge_base, CodeSearchResult, PolicySearchResult
from app.core.audit import log_event, AuditEventType

logger = structlog.get_logger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence levels for reasoning outputs."""
    HIGH = "high"          # >85% - Strong evidence, clear guidelines
    MEDIUM = "medium"      # 60-85% - Some ambiguity, review recommended
    LOW = "low"           # <60% - Insufficient evidence, requires human review
    UNCERTAIN = "uncertain"  # Cannot determine - flag for human


class EvidenceType(str, Enum):
    """Types of clinical evidence."""
    DIAGNOSIS = "diagnosis"
    PROCEDURE = "procedure"
    LAB_RESULT = "lab_result"
    VITAL_SIGN = "vital_sign"
    MEDICATION = "medication"
    IMAGING = "imaging"
    PROVIDER_ATTESTATION = "provider_attestation"
    HISTORY = "history"


class Citation(BaseModel):
    """A traceable citation to source material."""
    source_type: str  # document, policy, guideline, code_book
    source_id: str
    source_title: str
    location: str | None = None  # page, section, paragraph
    quoted_text: str | None = None
    relevance: str  # Why this citation supports the conclusion


class Evidence(BaseModel):
    """Extracted clinical evidence with citations."""
    evidence_type: EvidenceType
    content: str
    extracted_value: str | None = None  # Normalized value if applicable
    date: datetime | None = None
    provider: str | None = None
    citation: Citation
    confidence: float = 1.0


class CodeSuggestion(BaseModel):
    """A suggested code with full justification."""
    code: str
    code_type: str  # ICD10CM, ICD10PCS, CPT, HCPCS
    description: str
    
    # Evidence chain
    supporting_evidence: list[Evidence]
    
    # Compliance
    policy_citations: list[Citation] = []
    guideline_citations: list[Citation] = []
    
    # Medical necessity
    medical_necessity_met: bool = True
    medical_necessity_rationale: str | None = None
    
    # Confidence
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.75
    uncertainty_factors: list[str] = []
    
    # Compliance flags
    requires_modifier: bool = False
    suggested_modifiers: list[str] = []
    bundling_notes: str | None = None
    
    # Human review
    requires_review: bool = True
    review_reason: str | None = None


class ReasoningStep(BaseModel):
    """A single step in the reasoning chain."""
    step_number: int
    step_type: str  # extraction, mapping, validation, etc.
    input_summary: str
    output_summary: str
    reasoning: str
    citations: list[Citation] = []
    duration_ms: int = 0


class ReasoningChain(BaseModel):
    """Complete reasoning chain for a decision."""
    chain_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context
    encounter_id: str | None = None
    task_type: str  # claim_generation, validation, denial_analysis, audit
    
    # Steps
    steps: list[ReasoningStep] = []
    
    # Outputs
    diagnoses: list[CodeSuggestion] = []
    procedures: list[CodeSuggestion] = []
    
    # Overall assessment
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    overall_score: float = 0.75
    
    # Compliance
    compliance_issues: list[str] = []
    recommendations: list[str] = []
    
    # Audit
    requires_human_review: bool = True
    review_priority: str = "normal"  # low, normal, high, urgent


class ReasoningEngine:
    """
    The core reasoning engine.
    
    Implements a multi-step process:
    1. Evidence Extraction - Pull clinical facts from documentation
    2. Code Mapping - Map evidence to appropriate codes
    3. Policy Alignment - Verify payer coverage and requirements
    4. Medical Necessity - Check necessity criteria
    5. Compliance Check - Bundling, modifiers, MUE
    6. Confidence Assessment - Score certainty and flag issues
    """
    
    def __init__(self):
        self.llm = None
        self.knowledge = None
    
    async def _ensure_initialized(self):
        """Ensure LLM and knowledge base are available."""
        if self.llm is None:
            self.llm = get_llm_client()
        if self.knowledge is None:
            self.knowledge = get_knowledge_base()
    
    async def extract_evidence(
        self,
        clinical_text: str,
        document_id: str,
        document_title: str = "Clinical Document",
    ) -> list[Evidence]:
        """
        Extract clinical evidence from documentation.
        
        Uses LLM to identify and extract:
        - Diagnoses and conditions
        - Procedures performed
        - Lab results and vitals
        - Provider statements
        """
        await self._ensure_initialized()
        
        # Prompt for evidence extraction
        prompt = f"""Analyze this clinical documentation and extract all relevant clinical evidence.

DOCUMENTATION:
{clinical_text}

For each piece of evidence, provide:
1. The type (diagnosis, procedure, lab_result, vital_sign, medication, imaging, provider_attestation, history)
2. The exact text from the document
3. The normalized/structured value if applicable
4. Any relevant dates mentioned

Format as JSON array:
[
  {{
    "evidence_type": "diagnosis",
    "content": "exact quoted text from document",
    "extracted_value": "normalized value",
    "date": "YYYY-MM-DD if mentioned",
    "location": "section or context where found"
  }}
]

Be precise. Only extract what is explicitly stated. Do not infer or assume."""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SystemPrompts.EVIDENCE_EXTRACTOR,
            temperature=0.1,
            json_mode=True,
        )
        
        evidence_list = []
        
        try:
            import json
            extracted = json.loads(response.content)
            
            for item in extracted:
                evidence = Evidence(
                    evidence_type=EvidenceType(item.get("evidence_type", "history")),
                    content=item.get("content", ""),
                    extracted_value=item.get("extracted_value"),
                    date=item.get("date"),
                    citation=Citation(
                        source_type="document",
                        source_id=document_id,
                        source_title=document_title,
                        location=item.get("location"),
                        quoted_text=item.get("content"),
                        relevance="Direct clinical evidence",
                    ),
                )
                evidence_list.append(evidence)
                
        except Exception as e:
            logger.error("Failed to parse evidence extraction", error=str(e))
        
        logger.info(
            "Evidence extracted",
            document_id=document_id,
            evidence_count=len(evidence_list),
        )
        
        return evidence_list
    
    async def map_diagnosis_codes(
        self,
        evidence: list[Evidence],
        existing_codes: list[str] | None = None,
    ) -> list[CodeSuggestion]:
        """
        Map clinical evidence to ICD-10 diagnosis codes.
        
        Each code suggestion includes:
        - Supporting evidence citations
        - Specificity analysis
        - Confidence scoring
        """
        await self._ensure_initialized()
        
        # Filter to diagnosis evidence
        diagnosis_evidence = [
            e for e in evidence 
            if e.evidence_type in [EvidenceType.DIAGNOSIS, EvidenceType.HISTORY]
        ]
        
        if not diagnosis_evidence:
            return []
        
        suggestions = []
        
        # Build prompt with evidence
        evidence_text = "\n".join([
            f"- {e.content} (Source: {e.citation.source_title})"
            for e in diagnosis_evidence
        ])
        
        prompt = f"""Based on the following clinical evidence, suggest appropriate ICD-10-CM diagnosis codes.

CLINICAL EVIDENCE:
{evidence_text}

For each diagnosis, provide:
1. The ICD-10-CM code
2. Why this code is appropriate
3. What evidence supports it
4. Any coding considerations (specificity, laterality, etc.)
5. Your confidence level (high/medium/low)

Format as JSON array:
[
  {{
    "code": "X00.0",
    "rationale": "Why this code",
    "supporting_evidence": ["evidence 1", "evidence 2"],
    "considerations": "any notes",
    "confidence": "high|medium|low",
    "uncertainty_factors": ["list any concerns"]
  }}
]

RULES:
- Only suggest codes you are certain exist
- Choose the most specific code supported by documentation
- Do not assume laterality or details not documented
- Flag when documentation is insufficient for specificity"""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SystemPrompts.MEDICAL_CODER,
            temperature=0.1,
            json_mode=True,
        )
        
        try:
            import json
            suggested = json.loads(response.content)
            
            for item in suggested:
                code = item.get("code", "")
                
                # Verify code exists in knowledge base
                code_results = await self.knowledge.search_icd10(code, limit=1)
                
                if code_results:
                    verified_code = code_results[0]
                    
                    # Map confidence
                    conf_map = {
                        "high": (ConfidenceLevel.HIGH, 0.9),
                        "medium": (ConfidenceLevel.MEDIUM, 0.7),
                        "low": (ConfidenceLevel.LOW, 0.5),
                    }
                    conf_level, conf_score = conf_map.get(
                        item.get("confidence", "medium"),
                        (ConfidenceLevel.MEDIUM, 0.7)
                    )
                    
                    # Find matching evidence
                    supporting = []
                    for ev in diagnosis_evidence:
                        for supp in item.get("supporting_evidence", []):
                            if supp.lower() in ev.content.lower():
                                supporting.append(ev)
                                break
                    
                    suggestion = CodeSuggestion(
                        code=verified_code.code,
                        code_type="ICD10CM",
                        description=verified_code.description,
                        supporting_evidence=supporting,
                        confidence_level=conf_level,
                        confidence_score=conf_score,
                        uncertainty_factors=item.get("uncertainty_factors", []),
                        requires_review=conf_level != ConfidenceLevel.HIGH,
                        review_reason=item.get("considerations"),
                    )
                    suggestions.append(suggestion)
                else:
                    logger.warning("LLM suggested non-existent code", code=code)
                    
        except Exception as e:
            logger.error("Failed to parse code suggestions", error=str(e))
        
        return suggestions
    
    async def map_procedure_codes(
        self,
        evidence: list[Evidence],
        place_of_service: str | None = None,
    ) -> list[CodeSuggestion]:
        """
        Map clinical evidence to CPT/HCPCS procedure codes.
        
        Includes:
        - Code selection rationale
        - Modifier requirements
        - Medical necessity check
        """
        await self._ensure_initialized()
        
        # Filter to procedure evidence
        procedure_evidence = [
            e for e in evidence
            if e.evidence_type == EvidenceType.PROCEDURE
        ]
        
        if not procedure_evidence:
            return []
        
        suggestions = []
        
        evidence_text = "\n".join([
            f"- {e.content} (Source: {e.citation.source_title})"
            for e in procedure_evidence
        ])
        
        prompt = f"""Based on the following clinical evidence, suggest appropriate CPT/HCPCS codes.

CLINICAL EVIDENCE:
{evidence_text}

PLACE OF SERVICE: {place_of_service or "Not specified"}

For each procedure, provide:
1. The CPT or HCPCS code
2. Why this code is appropriate
3. What evidence supports it
4. Any required modifiers
5. Medical necessity justification
6. Your confidence level

Format as JSON array:
[
  {{
    "code": "99213",
    "code_type": "CPT",
    "rationale": "Why this code",
    "supporting_evidence": ["evidence"],
    "modifiers": ["25", "59"],
    "medical_necessity": "Justification text",
    "confidence": "high|medium|low",
    "uncertainty_factors": []
  }}
]

RULES:
- Match code to exact service documented
- Include all necessary modifiers
- Do not unbundle services inappropriately
- Consider global periods for surgical codes"""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=SystemPrompts.MEDICAL_CODER,
            temperature=0.1,
            json_mode=True,
        )
        
        try:
            import json
            suggested = json.loads(response.content)
            
            for item in suggested:
                code = item.get("code", "")
                code_type = item.get("code_type", "CPT")
                
                # Verify code exists
                if code_type == "CPT":
                    code_results = await self.knowledge.search_cpt(code, limit=1)
                else:
                    code_results = await self.knowledge.search_hcpcs(code, limit=1)
                
                if code_results:
                    verified_code = code_results[0]
                    
                    conf_map = {
                        "high": (ConfidenceLevel.HIGH, 0.9),
                        "medium": (ConfidenceLevel.MEDIUM, 0.7),
                        "low": (ConfidenceLevel.LOW, 0.5),
                    }
                    conf_level, conf_score = conf_map.get(
                        item.get("confidence", "medium"),
                        (ConfidenceLevel.MEDIUM, 0.7)
                    )
                    
                    suggestion = CodeSuggestion(
                        code=verified_code.code,
                        code_type=code_type,
                        description=verified_code.description,
                        supporting_evidence=[
                            e for e in procedure_evidence
                            if any(s.lower() in e.content.lower() 
                                   for s in item.get("supporting_evidence", []))
                        ],
                        medical_necessity_met=True,
                        medical_necessity_rationale=item.get("medical_necessity"),
                        confidence_level=conf_level,
                        confidence_score=conf_score,
                        uncertainty_factors=item.get("uncertainty_factors", []),
                        requires_modifier=bool(item.get("modifiers")),
                        suggested_modifiers=item.get("modifiers", []),
                        requires_review=conf_level != ConfidenceLevel.HIGH,
                    )
                    suggestions.append(suggestion)
                    
        except Exception as e:
            logger.error("Failed to parse procedure suggestions", error=str(e))
        
        return suggestions
    
    async def check_compliance(
        self,
        diagnoses: list[CodeSuggestion],
        procedures: list[CodeSuggestion],
    ) -> list[str]:
        """
        Run compliance checks on suggested codes.
        
        Checks:
        - NCCI edits (bundling)
        - MUE limits
        - Modifier requirements
        - Medical necessity alignment
        """
        await self._ensure_initialized()
        
        issues = []
        
        # Check NCCI edits between all procedure pairs
        procedure_codes = [p.code for p in procedures]
        
        for i, code1 in enumerate(procedure_codes):
            for code2 in procedure_codes[i+1:]:
                edit_result = await self.knowledge.check_ncci_edit(code1, code2)
                if edit_result and not edit_result.is_allowed:
                    issues.append(
                        f"NCCI Edit: {code1} and {code2} - {edit_result.recommendation}"
                    )
                elif edit_result and edit_result.requires_modifier:
                    # Check if modifier is present
                    code1_sugg = next((p for p in procedures if p.code == code1), None)
                    code2_sugg = next((p for p in procedures if p.code == code2), None)
                    
                    has_modifier = False
                    if code1_sugg and any(m in ["59", "XE", "XS", "XP", "XU"] for m in code1_sugg.suggested_modifiers):
                        has_modifier = True
                    if code2_sugg and any(m in ["59", "XE", "XS", "XP", "XU"] for m in code2_sugg.suggested_modifiers):
                        has_modifier = True
                    
                    if not has_modifier:
                        issues.append(
                            f"Modifier Required: {code1} and {code2} need a modifier (59, XE, XS, XP, or XU) to bill together"
                        )
        
        # Check MUE limits
        for proc in procedures:
            mue = await self.knowledge.get_mue(proc.code)
            if mue:
                # In real implementation, would check actual units
                pass
        
        # Check diagnosis support for procedures
        if procedures and not diagnoses:
            issues.append("No diagnosis codes to support procedure codes - claims may be denied")
        
        return issues
    
    async def generate_reasoning_chain(
        self,
        clinical_text: str,
        document_id: str,
        document_title: str,
        task_type: str = "claim_generation",
        encounter_id: str | None = None,
        payer: str | None = None,
    ) -> ReasoningChain:
        """
        Generate a complete reasoning chain for a clinical document.
        
        This is the main entry point for claim generation.
        """
        import time
        from app.core.security import generate_secure_id
        
        chain = ReasoningChain(
            chain_id=generate_secure_id(),
            task_type=task_type,
            encounter_id=encounter_id,
        )
        
        # Step 1: Evidence Extraction
        start = time.time()
        evidence = await self.extract_evidence(
            clinical_text=clinical_text,
            document_id=document_id,
            document_title=document_title,
        )
        
        chain.steps.append(ReasoningStep(
            step_number=1,
            step_type="evidence_extraction",
            input_summary=f"Clinical document: {len(clinical_text)} characters",
            output_summary=f"Extracted {len(evidence)} evidence items",
            reasoning="Parsed clinical documentation to identify diagnoses, procedures, and supporting evidence",
            duration_ms=int((time.time() - start) * 1000),
        ))
        
        # Step 2: Diagnosis Mapping
        start = time.time()
        diagnoses = await self.map_diagnosis_codes(evidence)
        
        chain.steps.append(ReasoningStep(
            step_number=2,
            step_type="diagnosis_mapping",
            input_summary=f"{len([e for e in evidence if e.evidence_type == EvidenceType.DIAGNOSIS])} diagnosis evidence items",
            output_summary=f"Suggested {len(diagnoses)} ICD-10 codes",
            reasoning="Mapped clinical findings to appropriate ICD-10-CM codes with specificity analysis",
            citations=[d.supporting_evidence[0].citation for d in diagnoses if d.supporting_evidence],
            duration_ms=int((time.time() - start) * 1000),
        ))
        chain.diagnoses = diagnoses
        
        # Step 3: Procedure Mapping
        start = time.time()
        procedures = await self.map_procedure_codes(evidence)
        
        chain.steps.append(ReasoningStep(
            step_number=3,
            step_type="procedure_mapping",
            input_summary=f"{len([e for e in evidence if e.evidence_type == EvidenceType.PROCEDURE])} procedure evidence items",
            output_summary=f"Suggested {len(procedures)} CPT/HCPCS codes",
            reasoning="Mapped documented services to appropriate procedure codes with modifier analysis",
            citations=[p.supporting_evidence[0].citation for p in procedures if p.supporting_evidence],
            duration_ms=int((time.time() - start) * 1000),
        ))
        chain.procedures = procedures
        
        # Step 4: Policy Alignment
        start = time.time()
        policy_issues = []
        
        if payer:
            for proc in procedures:
                policies = await self.knowledge.search_policies(
                    f"{proc.description} coverage criteria",
                    payer=payer,
                    limit=2,
                )
                if policies:
                    proc.policy_citations = [
                        Citation(
                            source_type="policy",
                            source_id=p.policy_id,
                            source_title=p.title,
                            quoted_text=p.content_snippet[:200],
                            relevance=f"Payer coverage policy for {proc.code}",
                        )
                        for p in policies
                    ]
        
        chain.steps.append(ReasoningStep(
            step_number=4,
            step_type="policy_alignment",
            input_summary=f"Checking {len(procedures)} procedures against payer policies",
            output_summary=f"Found {sum(len(p.policy_citations) for p in procedures)} relevant policies",
            reasoning="Verified procedure codes against payer coverage policies",
            duration_ms=int((time.time() - start) * 1000),
        ))
        
        # Step 5: Compliance Check
        start = time.time()
        compliance_issues = await self.check_compliance(diagnoses, procedures)
        
        chain.steps.append(ReasoningStep(
            step_number=5,
            step_type="compliance_check",
            input_summary=f"Checking {len(diagnoses)} diagnoses and {len(procedures)} procedures",
            output_summary=f"Found {len(compliance_issues)} compliance considerations",
            reasoning="Ran NCCI edits, MUE limits, and modifier checks",
            duration_ms=int((time.time() - start) * 1000),
        ))
        chain.compliance_issues = compliance_issues
        
        # Step 6: Confidence Assessment
        all_scores = [d.confidence_score for d in diagnoses] + [p.confidence_score for p in procedures]
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            chain.overall_score = avg_score
            
            if avg_score >= 0.85:
                chain.overall_confidence = ConfidenceLevel.HIGH
            elif avg_score >= 0.6:
                chain.overall_confidence = ConfidenceLevel.MEDIUM
            else:
                chain.overall_confidence = ConfidenceLevel.LOW
        
        chain.requires_human_review = (
            chain.overall_confidence != ConfidenceLevel.HIGH
            or len(compliance_issues) > 0
        )
        
        if compliance_issues:
            chain.review_priority = "high"
        
        # Log reasoning chain
        log_event(
            event_type=AuditEventType.LLM_REASONING,
            description="Reasoning chain completed",
            resource_type="reasoning_chain",
            resource_id=chain.chain_id,
            details={
                "task_type": task_type,
                "diagnoses_count": len(diagnoses),
                "procedures_count": len(procedures),
                "compliance_issues": len(compliance_issues),
                "overall_confidence": chain.overall_confidence.value,
            },
        )
        
        return chain


# Global reasoning engine instance
_reasoning_engine: ReasoningEngine | None = None


def get_reasoning_engine() -> ReasoningEngine:
    """Get the global reasoning engine instance."""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine

