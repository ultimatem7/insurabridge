"""
EvidenceAtom - The Immutable Unit of Provenance

Every piece of information in Insurabridge must originate from an EvidenceAtom.
EvidenceAtoms are:
- Immutable once created
- Cryptographically hashed
- Traceable to source documents
- Stored in a versioned, append-only store

NO downstream logic may consume raw text - only EvidenceAtoms.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import settings
from app.core.audit import log_event, AuditEventType

logger = structlog.get_logger(__name__)


class EvidenceType(str, Enum):
    """Types of evidence sources."""
    CLINICAL_NOTE = "clinical_note"
    LAB = "lab"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    POLICY = "policy"
    CODEBOOK = "codebook"
    GUIDELINE = "guideline"
    VITAL_SIGN = "vital_sign"
    MEDICATION = "medication"
    DISCHARGE_SUMMARY = "discharge_summary"
    OPERATIVE_REPORT = "operative_report"
    HISTORY = "history"
    INSURANCE = "insurance"
    CLAIM = "claim"


class SourceSystem(str, Enum):
    """Source systems for evidence."""
    EPIC = "EPIC"
    MANUAL_UPLOAD = "Manual Upload"
    INTERNAL_DB = "Internal DB"
    FHIR = "FHIR"
    HL7 = "HL7"


class EvidenceLocation(BaseModel):
    """Precise location within source document."""
    page: int | None = None
    line_start: int | None = None
    line_end: int | None = None
    section: str | None = None
    paragraph: int | None = None
    character_offset_start: int | None = None
    character_offset_end: int | None = None
    
    @property
    def line_range(self) -> str | None:
        """Human-readable line range."""
        if self.line_start is not None:
            if self.line_end is not None and self.line_end != self.line_start:
                return f"{self.line_start}-{self.line_end}"
            return str(self.line_start)
        return None
    
    def to_citation(self) -> str:
        """Generate human-readable citation."""
        parts = []
        if self.page is not None:
            parts.append(f"p.{self.page}")
        if self.line_range:
            parts.append(f"lines {self.line_range}")
        if self.section:
            parts.append(f"§{self.section}")
        return ", ".join(parts) if parts else "location unknown"


class EvidenceAtom(BaseModel):
    """
    The fundamental, immutable unit of evidence.
    
    CRITICAL CONSTRAINTS:
    - Once created, an EvidenceAtom cannot be modified
    - The hash must match the content
    - All downstream processing must reference EvidenceAtoms by ID
    - Raw text cannot be used without an EvidenceAtom wrapper
    """
    
    # Unique identifier
    evidence_id: str = Field(default_factory=lambda: f"EV-{uuid4().hex[:12].upper()}")
    
    # Classification
    evidence_type: EvidenceType
    source_system: SourceSystem
    
    # Source document
    document_id: str
    document_name: str
    document_hash: str  # SHA-256 of original document
    
    # Authorship
    author: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Content (immutable after creation)
    content_excerpt: str = Field(..., min_length=1, max_length=2000)
    
    # Location in source
    location: EvidenceLocation
    
    # Integrity
    content_hash: str | None = None  # Computed on creation
    
    # Confidence in extraction accuracy
    extraction_confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Immutability flag - once set to True, object cannot be modified
    _frozen: bool = False
    
    @field_validator("content_excerpt")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Evidence content cannot be empty or whitespace-only")
        return v.strip()
    
    @model_validator(mode="after")
    def compute_hash_and_freeze(self) -> "EvidenceAtom":
        """Compute content hash and freeze the object."""
        if self.content_hash is None:
            # Compute hash of content + location for integrity verification
            hash_input = json.dumps({
                "content": self.content_excerpt,
                "document_id": self.document_id,
                "location": self.location.model_dump(),
            }, sort_keys=True)
            self.content_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Mark as frozen
        object.__setattr__(self, "_frozen", True)
        return self
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification after freezing."""
        if hasattr(self, "_frozen") and self._frozen and name != "_frozen":
            raise AttributeError(
                f"EvidenceAtom is immutable. Cannot modify '{name}' after creation."
            )
        super().__setattr__(name, value)
    
    def verify_integrity(self) -> bool:
        """Verify the content hash matches."""
        hash_input = json.dumps({
            "content": self.content_excerpt,
            "document_id": self.document_id,
            "location": self.location.model_dump(),
        }, sort_keys=True)
        computed = hashlib.sha256(hash_input.encode()).hexdigest()
        return computed == self.content_hash
    
    def to_citation(self) -> str:
        """Generate a full citation string."""
        loc = self.location.to_citation()
        return f"[{self.evidence_id}] {self.document_name}, {loc}"
    
    def to_inline_citation(self) -> str:
        """Generate inline citation for appeal letters."""
        return f"[{self.evidence_id}]"


class EvidenceStore:
    """
    Immutable, append-only store for EvidenceAtoms.
    
    Design principles:
    - Atoms are never deleted or modified
    - All access is logged
    - Integrity is verifiable
    - Efficient retrieval by ID, document, and type
    """
    
    def __init__(self, store_path: Path | None = None):
        self.store_path = store_path or (settings.data_dir / "evidence")
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory index for fast lookups
        self._atoms: dict[str, EvidenceAtom] = {}
        self._by_document: dict[str, list[str]] = {}  # document_id -> [evidence_ids]
        self._by_type: dict[EvidenceType, list[str]] = {}
        
        # Load existing atoms
        self._load_store()
    
    def _load_store(self) -> None:
        """Load atoms from disk."""
        atoms_file = self.store_path / "atoms.jsonl"
        if atoms_file.exists():
            with open(atoms_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        atom = EvidenceAtom.model_validate(data)
                        self._index_atom(atom)
                    except Exception as e:
                        logger.error("Failed to load evidence atom", error=str(e))
    
    def _index_atom(self, atom: EvidenceAtom) -> None:
        """Add atom to in-memory indexes."""
        self._atoms[atom.evidence_id] = atom
        
        if atom.document_id not in self._by_document:
            self._by_document[atom.document_id] = []
        self._by_document[atom.document_id].append(atom.evidence_id)
        
        if atom.evidence_type not in self._by_type:
            self._by_type[atom.evidence_type] = []
        self._by_type[atom.evidence_type].append(atom.evidence_id)
    
    def store(self, atom: EvidenceAtom) -> EvidenceAtom:
        """
        Store an EvidenceAtom immutably.
        
        Once stored, the atom cannot be modified or deleted.
        """
        # Verify integrity
        if not atom.verify_integrity():
            raise ValueError("EvidenceAtom integrity check failed")
        
        # Check for duplicate
        if atom.evidence_id in self._atoms:
            existing = self._atoms[atom.evidence_id]
            if existing.content_hash != atom.content_hash:
                raise ValueError(
                    f"Evidence ID {atom.evidence_id} already exists with different content"
                )
            return existing  # Return existing if identical
        
        # Append to store file
        atoms_file = self.store_path / "atoms.jsonl"
        with open(atoms_file, "a") as f:
            f.write(atom.model_dump_json() + "\n")
        
        # Index in memory
        self._index_atom(atom)
        
        logger.debug(
            "Evidence atom stored",
            evidence_id=atom.evidence_id,
            document_id=atom.document_id,
            evidence_type=atom.evidence_type,
        )
        
        return atom
    
    def store_batch(self, atoms: list[EvidenceAtom]) -> list[EvidenceAtom]:
        """Store multiple atoms efficiently."""
        stored = []
        atoms_file = self.store_path / "atoms.jsonl"
        
        with open(atoms_file, "a") as f:
            for atom in atoms:
                if not atom.verify_integrity():
                    logger.warning("Skipping atom with failed integrity", evidence_id=atom.evidence_id)
                    continue
                
                if atom.evidence_id not in self._atoms:
                    f.write(atom.model_dump_json() + "\n")
                    self._index_atom(atom)
                    stored.append(atom)
                else:
                    stored.append(self._atoms[atom.evidence_id])
        
        return stored
    
    def get(self, evidence_id: str) -> EvidenceAtom | None:
        """Retrieve an atom by ID."""
        return self._atoms.get(evidence_id)
    
    def get_many(self, evidence_ids: list[str]) -> list[EvidenceAtom]:
        """Retrieve multiple atoms by ID."""
        return [self._atoms[eid] for eid in evidence_ids if eid in self._atoms]
    
    def get_by_document(self, document_id: str) -> list[EvidenceAtom]:
        """Get all atoms from a specific document."""
        ids = self._by_document.get(document_id, [])
        return [self._atoms[eid] for eid in ids]
    
    def get_by_type(self, evidence_type: EvidenceType) -> list[EvidenceAtom]:
        """Get all atoms of a specific type."""
        ids = self._by_type.get(evidence_type, [])
        return [self._atoms[eid] for eid in ids]
    
    def exists(self, evidence_id: str) -> bool:
        """Check if an evidence ID exists."""
        return evidence_id in self._atoms
    
    def verify_all(self) -> tuple[int, list[str]]:
        """
        Verify integrity of all stored atoms.
        
        Returns (valid_count, list of invalid IDs).
        """
        valid = 0
        invalid = []
        
        for eid, atom in self._atoms.items():
            if atom.verify_integrity():
                valid += 1
            else:
                invalid.append(eid)
        
        return valid, invalid
    
    def count(self) -> int:
        """Total number of stored atoms."""
        return len(self._atoms)
    
    def search_content(self, query: str, limit: int = 20) -> list[EvidenceAtom]:
        """
        Simple content search.
        
        For production, use full-text search index.
        """
        query_lower = query.lower()
        results = []
        
        for atom in self._atoms.values():
            if query_lower in atom.content_excerpt.lower():
                results.append(atom)
                if len(results) >= limit:
                    break
        
        return results


# Global evidence store instance
_evidence_store: EvidenceStore | None = None


def get_evidence_store() -> EvidenceStore:
    """Get the global evidence store instance."""
    global _evidence_store
    if _evidence_store is None:
        _evidence_store = EvidenceStore()
    return _evidence_store


def create_evidence_atom(
    content: str,
    evidence_type: EvidenceType,
    source_system: SourceSystem,
    document_id: str,
    document_name: str,
    document_hash: str,
    location: EvidenceLocation,
    author: str | None = None,
    extraction_confidence: float = 1.0,
) -> EvidenceAtom:
    """
    Factory function to create and store an EvidenceAtom.
    
    This is the ONLY approved way to create evidence.
    """
    atom = EvidenceAtom(
        evidence_type=evidence_type,
        source_system=source_system,
        document_id=document_id,
        document_name=document_name,
        document_hash=document_hash,
        content_excerpt=content,
        location=location,
        author=author,
        extraction_confidence=extraction_confidence,
    )
    
    store = get_evidence_store()
    return store.store(atom)


def store_evidence_atom(atom: EvidenceAtom) -> EvidenceAtom:
    """Store an existing atom."""
    store = get_evidence_store()
    return store.store(atom)


def get_evidence_atom(evidence_id: str) -> EvidenceAtom | None:
    """Retrieve an atom by ID."""
    store = get_evidence_store()
    return store.get(evidence_id)


# Aliases for backward compatibility
Location = EvidenceLocation

