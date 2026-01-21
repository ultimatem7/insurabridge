"""
Fact Extraction Layer

Extracts LITERAL facts from EvidenceAtoms.

CRITICAL CONSTRAINTS:
- NO inference allowed
- NO summarization allowed
- One fact per evidence atom
- Reject facts that cannot be tied to exactly one evidence_id
"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field, field_validator

from app.core.llm import get_llm_client
from app.evidence.atoms import EvidenceAtom, EvidenceStore, get_evidence_store

logger = structlog.get_logger(__name__)


class Fact(BaseModel):
    """
    A single, atomic fact extracted from evidence.
    
    Each fact:
    - States one literal truth
    - Is tied to exactly one EvidenceAtom
    - Contains no inference or interpretation
    """
    
    fact_id: str = Field(default_factory=lambda: f"FACT-{uuid4().hex[:12].upper()}")
    
    # The literal fact text
    fact_text: str = Field(..., min_length=5, max_length=500)
    
    # MANDATORY link to source evidence
    evidence_id: str
    
    # Classification
    fact_type: str  # diagnosis, procedure, measurement, finding, etc.
    
    # Extraction metadata
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    extraction_method: str = "llm"  # llm, rule, manual
    
    # Quality indicators
    is_literal: bool = True  # False if any interpretation was needed
    extraction_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    
    @field_validator("fact_text")
    @classmethod
    def validate_no_inference(cls, v: str) -> str:
        """Check for inference language that shouldn't be present."""
        inference_markers = [
            "likely", "probably", "suggests", "may indicate",
            "possibly", "appears to", "seems", "could be",
            "might", "presumably", "apparently"
        ]
        v_lower = v.lower()
        for marker in inference_markers:
            if marker in v_lower:
                raise ValueError(
                    f"Fact contains inference language ('{marker}'). "
                    "Facts must be literal statements only."
                )
        return v
    
    def get_evidence(self, store: EvidenceStore | None = None) -> EvidenceAtom | None:
        """Retrieve the linked evidence atom."""
        store = store or get_evidence_store()
        return store.get(self.evidence_id)
    
    def to_citation(self) -> str:
        """Generate citation including evidence reference."""
        return f"{self.fact_text} [{self.evidence_id}]"


class FactExtractionResult(BaseModel):
    """Result of fact extraction from evidence atoms."""
    
    facts: list[Fact] = []
    rejected_extractions: list[dict] = []  # Facts that failed validation
    source_evidence_ids: list[str] = []
    extraction_warnings: list[str] = []
    
    @property
    def success_rate(self) -> float:
        total = len(self.facts) + len(self.rejected_extractions)
        return len(self.facts) / total if total > 0 else 0.0


# System prompt for LITERAL fact extraction
FACT_EXTRACTION_PROMPT = """You are extracting LITERAL facts from medical documentation.

CRITICAL RULES - VIOLATIONS WILL BE REJECTED:
1. Extract ONLY facts that are EXPLICITLY stated in the text
2. DO NOT infer, deduce, or assume anything
3. DO NOT summarize or paraphrase - use original language
4. Each fact must be traceable to specific text
5. If something is not explicitly stated, DO NOT extract it

FORBIDDEN:
- "Patient likely has..." (inference)
- "This suggests..." (interpretation)
- "Based on symptoms..." (deduction)
- Any speculation or clinical reasoning

ALLOWED:
- "Patient reports chest pain"
- "Blood pressure measured at 140/90"
- "Diagnosis: Essential hypertension (I10)"
- "Procedure performed: Appendectomy"

For each fact, provide:
1. fact_text: The literal statement (no inference)
2. fact_type: diagnosis | procedure | measurement | finding | history | medication | provider_statement
3. is_literal: true if directly quoted, false if any rewording

OUTPUT FORMAT (JSON array):
[
  {
    "fact_text": "exact or near-exact quote from source",
    "fact_type": "type",
    "is_literal": true,
    "source_quote": "the exact original text this comes from"
  }
]

If NO literal facts can be extracted, return: []

DO NOT MAKE ANYTHING UP. ONLY EXTRACT WHAT IS EXPLICITLY WRITTEN."""


class FactExtractor:
    """
    Extracts atomic facts from EvidenceAtoms.
    
    Uses LLM with strict constraints to extract only literal facts.
    Any extraction that cannot be tied to evidence is rejected.
    """
    
    def __init__(self):
        self.llm = None
        self._store = None
    
    @property
    def store(self) -> EvidenceStore:
        if self._store is None:
            self._store = get_evidence_store()
        return self._store
    
    async def _ensure_llm(self):
        if self.llm is None:
            self.llm = get_llm_client()
    
    async def extract_facts(
        self,
        atoms: list[EvidenceAtom],
    ) -> FactExtractionResult:
        """
        Extract literal facts from evidence atoms.
        
        Each fact is tied to exactly one evidence atom.
        Facts that cannot be verified are rejected.
        """
        await self._ensure_llm()
        
        result = FactExtractionResult(
            source_evidence_ids=[a.evidence_id for a in atoms],
        )
        
        for atom in atoms:
            try:
                atom_facts = await self._extract_from_atom(atom)
                
                for fact_data in atom_facts:
                    try:
                        # Create fact with mandatory evidence link
                        fact = Fact(
                            fact_text=fact_data["fact_text"],
                            fact_type=fact_data.get("fact_type", "finding"),
                            evidence_id=atom.evidence_id,
                            is_literal=fact_data.get("is_literal", True),
                            extraction_confidence=atom.extraction_confidence,
                        )
                        
                        # Verify the fact is actually in the source
                        if not self._verify_fact_in_source(fact, atom):
                            result.rejected_extractions.append({
                                "fact_text": fact_data["fact_text"],
                                "evidence_id": atom.evidence_id,
                                "reason": "Fact text not found in source evidence",
                            })
                            continue
                        
                        result.facts.append(fact)
                        
                    except ValueError as e:
                        # Validation error (e.g., inference language detected)
                        result.rejected_extractions.append({
                            "fact_text": fact_data.get("fact_text", "unknown"),
                            "evidence_id": atom.evidence_id,
                            "reason": str(e),
                        })
                        
            except Exception as e:
                logger.error(
                    "Fact extraction failed for atom",
                    evidence_id=atom.evidence_id,
                    error=str(e),
                )
                result.extraction_warnings.append(
                    f"Failed to extract from {atom.evidence_id}: {str(e)}"
                )
        
        logger.info(
            "Fact extraction complete",
            total_atoms=len(atoms),
            facts_extracted=len(result.facts),
            rejected=len(result.rejected_extractions),
        )
        
        return result
    
    async def _extract_from_atom(self, atom: EvidenceAtom) -> list[dict]:
        """Extract facts from a single evidence atom."""
        prompt = f"""Extract literal facts from this medical documentation excerpt.

EVIDENCE TYPE: {atom.evidence_type.value}
SOURCE: {atom.document_name}
LOCATION: {atom.location.to_citation()}

CONTENT:
\"\"\"
{atom.content_excerpt}
\"\"\"

Remember: Extract ONLY what is EXPLICITLY stated. No inference."""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=FACT_EXTRACTION_PROMPT,
            temperature=0.0,  # Maximum determinism
            json_mode=True,
        )
        
        try:
            facts = json.loads(response.content)
            if not isinstance(facts, list):
                facts = []
            return facts
        except json.JSONDecodeError:
            logger.warning("Failed to parse fact extraction response", evidence_id=atom.evidence_id)
            return []
    
    def _verify_fact_in_source(self, fact: Fact, atom: EvidenceAtom) -> bool:
        """
        Verify that the extracted fact is actually present in the source.
        
        This prevents hallucination at the fact level.
        """
        source_lower = atom.content_excerpt.lower()
        
        # Check for key terms from the fact
        fact_words = fact.fact_text.lower().split()
        significant_words = [w for w in fact_words if len(w) > 3]
        
        if not significant_words:
            return True  # Very short facts pass
        
        # At least 60% of significant words should be in source
        found = sum(1 for w in significant_words if w in source_lower)
        coverage = found / len(significant_words)
        
        return coverage >= 0.6
    
    async def extract_single(self, atom: EvidenceAtom) -> list[Fact]:
        """Extract facts from a single atom (convenience method)."""
        result = await self.extract_facts([atom])
        return result.facts


# Global fact extractor instance
_fact_extractor: FactExtractor | None = None


def get_fact_extractor() -> FactExtractor:
    """Get the global fact extractor instance."""
    global _fact_extractor
    if _fact_extractor is None:
        _fact_extractor = FactExtractor()
    return _fact_extractor


def get_facts_by_evidence_id(evidence_id: str) -> list[Fact]:
    """
    Get all facts linked to a specific evidence ID.
    Stubbed for stateless mode.
    """
    return []

