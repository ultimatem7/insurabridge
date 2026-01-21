"""
Knowledge Layer

Local indexed databases for:
- ICD-10-CM/PCS codes
- CPT codes
- HCPCS Level II codes
- MS-DRG mappings
- NCD/LCD policies
- Payer medical policies

All data stored locally with versioning and citation support.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field
# import chromadb
# from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.core.database import Base, get_session
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = structlog.get_logger(__name__)


# Database Models for Code Lookup

class ICD10Code(Base):
    """ICD-10-CM/PCS code reference."""
    __tablename__ = "icd10_codes"
    
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification
    code_type: Mapped[str] = mapped_column(String(3), nullable=False)  # CM or PCS
    chapter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Validity
    is_billable: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Version
    version_year: Mapped[int] = mapped_column(Integer, default=2024)
    
    __table_args__ = (
        Index("ix_icd10_description", "description"),
    )


class CPTCode(Base):
    """CPT code reference."""
    __tablename__ = "cpt_codes"
    
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subsection: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Modifiers commonly used
    common_modifiers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    
    # RVUs (Relative Value Units) - for charge estimation
    work_rvu: Mapped[float | None] = mapped_column(nullable=True)
    facility_pe_rvu: Mapped[float | None] = mapped_column(nullable=True)
    non_facility_pe_rvu: Mapped[float | None] = mapped_column(nullable=True)
    mp_rvu: Mapped[float | None] = mapped_column(nullable=True)
    
    # Version
    version_year: Mapped[int] = mapped_column(Integer, default=2024)
    
    __table_args__ = (
        Index("ix_cpt_description", "description"),
    )


class HCPCSCode(Base):
    """HCPCS Level II code reference."""
    __tablename__ = "hcpcs_codes"
    
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Classification
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Pricing
    pricing_indicator: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # Status
    status_code: Mapped[str | None] = mapped_column(String(1), nullable=True)
    
    # Version
    version_year: Mapped[int] = mapped_column(Integer, default=2024)


class ModifierCode(Base):
    """CPT/HCPCS modifier reference."""
    __tablename__ = "modifier_codes"
    
    code: Mapped[str] = mapped_column(String(5), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Type
    modifier_type: Mapped[str] = mapped_column(String(20), nullable=False)  # CPT, HCPCS, Both
    
    # Usage guidance
    usage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class NCCIEdit(Base):
    """National Correct Coding Initiative edits."""
    __tablename__ = "ncci_edits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    column_1_code: Mapped[str] = mapped_column(String(10), nullable=False)
    column_2_code: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Edit type
    edit_type: Mapped[str] = mapped_column(String(1), nullable=False)  # 0, 1, 9
    # 0 = not allowed, 1 = allowed with modifier, 9 = not applicable
    
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deletion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("ix_ncci_column1", "column_1_code"),
        Index("ix_ncci_column2", "column_2_code"),
    )


class MUEValue(Base):
    """Medically Unlikely Edits - max units per service."""
    __tablename__ = "mue_values"
    
    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    
    practitioner_mue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outpatient_hospital_mue: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    rationale: Mapped[str | None] = mapped_column(String(1), nullable=True)
    # A = anatomic, C = code descriptor, D = DME, E = per encounter
    
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Pydantic models for search results

class CodeSearchResult(BaseModel):
    """Result from code search."""
    code: str
    description: str
    code_type: str  # ICD10CM, ICD10PCS, CPT, HCPCS
    relevance_score: float = 1.0
    is_billable: bool = True
    additional_info: dict = Field(default_factory=dict)


class PolicySearchResult(BaseModel):
    """Result from policy search."""
    policy_id: str
    title: str
    payer: str
    content_snippet: str
    relevance_score: float
    effective_date: datetime | None = None
    source_url: str | None = None


class NCCICheckResult(BaseModel):
    """Result from NCCI edit check."""
    code1: str
    code2: str
    is_allowed: bool
    requires_modifier: bool
    edit_type: str
    recommendation: str


# Knowledge Base Service

class KnowledgeBase:
    """
    Central knowledge base for coding and policy lookup.
    
    Provides:
    - Fast code search (SQL FTS5)
    - Semantic policy search (ChromaDB vectors)
    - NCCI/MUE validation
    - Citation-ready results
    """
    
    def __init__(self):
        self._chroma_client: chromadb.Client | None = None
        self._policy_collection = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the knowledge base."""
        # Mock initialization for stateless mode
        self._initialized = True
        logger.info("Knowledge base initialized (Stateless Mode)")
    
    def is_available(self) -> bool:
        """Check if knowledge base is available."""
        return self._initialized
    
    async def search_icd10(
        self,
        query: str,
        code_type: str | None = None,  # CM or PCS
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """
        Search ICD-10 codes by description or code.
        
        Supports:
        - Exact code lookup
        - Description keyword search
        - Partial code matching
        """
        results = []
        
        async with get_session() as session:
            # Build query
            conditions = []
            
            # Check if query looks like a code
            code_pattern = re.compile(r'^[A-Z]\d{2}\.?\d{0,4}$', re.IGNORECASE)
            
            if code_pattern.match(query):
                # Exact or prefix code match
                normalized = query.upper().replace(".", "")
                conditions.append(
                    or_(
                        ICD10Code.code == normalized,
                        ICD10Code.code.startswith(normalized),
                    )
                )
            else:
                # Description search
                search_terms = query.lower().split()
                for term in search_terms:
                    conditions.append(
                        or_(
                            ICD10Code.description.ilike(f"%{term}%"),
                            ICD10Code.long_description.ilike(f"%{term}%"),
                        )
                    )
            
            if code_type:
                conditions.append(ICD10Code.code_type == code_type.upper())
            
            # Only billable codes
            conditions.append(ICD10Code.is_billable == True)
            
            stmt = (
                select(ICD10Code)
                .where(and_(*conditions))
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            codes = result.scalars().all()
            
            for code in codes:
                results.append(CodeSearchResult(
                    code=code.code,
                    description=code.description,
                    code_type=f"ICD10{code.code_type}",
                    is_billable=code.is_billable,
                    additional_info={
                        "chapter": code.chapter,
                        "category": code.category,
                        "version_year": code.version_year,
                    },
                ))
        
        return results
    
    async def search_cpt(
        self,
        query: str,
        section: str | None = None,
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """Search CPT codes by description or code."""
        results = []
        
        async with get_session() as session:
            conditions = []
            
            # Check if query looks like a CPT code
            code_pattern = re.compile(r'^\d{5}$')
            
            if code_pattern.match(query):
                conditions.append(CPTCode.code == query)
            else:
                search_terms = query.lower().split()
                for term in search_terms:
                    conditions.append(
                        or_(
                            CPTCode.description.ilike(f"%{term}%"),
                            CPTCode.long_description.ilike(f"%{term}%"),
                        )
                    )
            
            if section:
                conditions.append(CPTCode.section.ilike(f"%{section}%"))
            
            stmt = (
                select(CPTCode)
                .where(and_(*conditions))
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            codes = result.scalars().all()
            
            for code in codes:
                results.append(CodeSearchResult(
                    code=code.code,
                    description=code.description,
                    code_type="CPT",
                    additional_info={
                        "section": code.section,
                        "work_rvu": code.work_rvu,
                        "common_modifiers": code.common_modifiers,
                    },
                ))
        
        return results
    
    async def search_hcpcs(
        self,
        query: str,
        limit: int = 10,
    ) -> list[CodeSearchResult]:
        """Search HCPCS Level II codes."""
        results = []
        
        async with get_session() as session:
            conditions = []
            
            # HCPCS codes start with a letter
            code_pattern = re.compile(r'^[A-Z]\d{4}$', re.IGNORECASE)
            
            if code_pattern.match(query):
                conditions.append(HCPCSCode.code == query.upper())
            else:
                search_terms = query.lower().split()
                for term in search_terms:
                    conditions.append(
                        or_(
                            HCPCSCode.description.ilike(f"%{term}%"),
                            HCPCSCode.long_description.ilike(f"%{term}%"),
                        )
                    )
            
            stmt = (
                select(HCPCSCode)
                .where(and_(*conditions))
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            codes = result.scalars().all()
            
            for code in codes:
                results.append(CodeSearchResult(
                    code=code.code,
                    description=code.description,
                    code_type="HCPCS",
                    additional_info={
                        "category": code.category,
                        "status_code": code.status_code,
                    },
                ))
        
        return results
    
    async def check_ncci_edit(
        self,
        code1: str,
        code2: str,
    ) -> NCCICheckResult | None:
        """
        Check if two codes have an NCCI edit conflict.
        
        Returns None if no edit exists (codes can be billed together).
        """
        async with get_session() as session:
            stmt = select(NCCIEdit).where(
                or_(
                    and_(
                        NCCIEdit.column_1_code == code1,
                        NCCIEdit.column_2_code == code2,
                    ),
                    and_(
                        NCCIEdit.column_1_code == code2,
                        NCCIEdit.column_2_code == code1,
                    ),
                )
            )
            
            result = await session.execute(stmt)
            edit = result.scalar_one_or_none()
            
            if not edit:
                return None
            
            # Interpret edit type
            is_allowed = edit.edit_type != "0"
            requires_modifier = edit.edit_type == "1"
            
            recommendation = ""
            if edit.edit_type == "0":
                recommendation = f"Code {code2} is bundled into {code1} and cannot be billed separately."
            elif edit.edit_type == "1":
                recommendation = f"Codes can be billed together with appropriate modifier (e.g., 59, XE, XS, XP, XU)."
            else:
                recommendation = "No action needed - codes can be billed together."
            
            return NCCICheckResult(
                code1=code1,
                code2=code2,
                is_allowed=is_allowed,
                requires_modifier=requires_modifier,
                edit_type=edit.edit_type,
                recommendation=recommendation,
            )
    
    async def get_mue(self, code: str) -> int | None:
        """Get the MUE (max units) for a code."""
        async with get_session() as session:
            stmt = select(MUEValue).where(MUEValue.code == code)
            result = await session.execute(stmt)
            mue = result.scalar_one_or_none()
            
            if mue:
                # Return practitioner MUE by default
                return mue.practitioner_mue
            return None
    
    async def search_policies(
        self,
        query: str,
        payer: str | None = None,
        limit: int = 5,
    ) -> list[PolicySearchResult]:
        """
        Semantic search of payer policies using vector similarity.
        
        Searches LCD, NCD, and commercial payer policies.
        """
        # Mock results for stateless mode
        return []
    
    async def add_policy(
        self,
        policy_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Add a policy document to the vector store."""
        pass


# Global knowledge base instance
_knowledge_base: KnowledgeBase | None = None


async def init_knowledge_base() -> None:
    """Initialize the global knowledge base."""
    global _knowledge_base
    _knowledge_base = KnowledgeBase()
    await _knowledge_base.initialize()


async def check_knowledge_base() -> bool:
    """Check knowledge base availability."""
    global _knowledge_base
    return _knowledge_base is not None and _knowledge_base.is_available()


def get_knowledge_base() -> KnowledgeBase:
    """Get the global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        raise RuntimeError("Knowledge base not initialized")
    return _knowledge_base

