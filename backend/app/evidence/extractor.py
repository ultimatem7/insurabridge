"""
Evidence Extraction Pipeline

Converts raw documents into EvidenceAtoms.

This is the ONLY entry point for new evidence.
Raw text cannot enter the system without becoming EvidenceAtoms.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import BinaryIO
from uuid import uuid4

import structlog
from pydantic import BaseModel

from app.evidence.atoms import (
    EvidenceAtom,
    EvidenceType,
    SourceSystem,
    EvidenceLocation,
    EvidenceStore,
    get_evidence_store,
    create_evidence_atom,
)
from app.ingestion.documents import get_document_parser, ParsedDocument

logger = structlog.get_logger(__name__)


# Maximum tokens per evidence chunk (for citation-safe units)
MAX_CHUNK_TOKENS = 300
APPROX_CHARS_PER_TOKEN = 4
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * APPROX_CHARS_PER_TOKEN


class ExtractionResult(BaseModel):
    """Result of evidence extraction from a document."""
    
    document_id: str
    document_name: str
    document_hash: str
    
    atoms_created: int = 0
    atoms: list[str] = []  # Evidence IDs
    
    extraction_warnings: list[str] = []
    
    @property
    def success(self) -> bool:
        return self.atoms_created > 0


class EvidenceExtractor:
    """
    Extracts EvidenceAtoms from documents.
    
    This is the SOLE gateway for evidence entering the system.
    All content is:
    1. Chunked into citation-safe units
    2. Assigned unique identifiers
    3. Hashed for integrity
    4. Stored immutably
    """
    
    def __init__(self):
        self._store = None
        self._parser = None
    
    @property
    def store(self) -> EvidenceStore:
        if self._store is None:
            self._store = get_evidence_store()
        return self._store
    
    @property
    def parser(self):
        if self._parser is None:
            self._parser = get_document_parser()
        return self._parser
    
    def extract_from_file(
        self,
        file: BinaryIO,
        filename: str,
        source_system: SourceSystem = SourceSystem.MANUAL_UPLOAD,
        author: str | None = None,
    ) -> ExtractionResult:
        """
        Extract evidence atoms from an uploaded file.
        
        The file is parsed, chunked, and converted to EvidenceAtoms.
        """
        # Parse document
        parsed = self.parser.parse(file, filename)
        
        return self.extract_from_parsed(
            parsed=parsed,
            source_system=source_system,
            author=author,
        )
    
    def extract_from_parsed(
        self,
        parsed: ParsedDocument,
        source_system: SourceSystem = SourceSystem.MANUAL_UPLOAD,
        author: str | None = None,
    ) -> ExtractionResult:
        """Extract evidence from an already-parsed document."""
        
        document_id = parsed.metadata.id
        document_name = parsed.metadata.filename
        
        # Hash the original content
        document_hash = hashlib.sha256(parsed.content.encode()).hexdigest()
        
        result = ExtractionResult(
            document_id=document_id,
            document_name=document_name,
            document_hash=document_hash,
        )
        
        atoms_to_store = []
        
        # Extract from sections if available
        if parsed.sections:
            for section_name, section_content in parsed.sections.items():
                section_atoms = self._chunk_and_create_atoms(
                    content=section_content,
                    document_id=document_id,
                    document_name=document_name,
                    document_hash=document_hash,
                    source_system=source_system,
                    section=section_name,
                    author=author,
                )
                atoms_to_store.extend(section_atoms)
        
        # Also chunk the full content (may capture content not in sections)
        full_atoms = self._chunk_and_create_atoms(
            content=parsed.content,
            document_id=document_id,
            document_name=document_name,
            document_hash=document_hash,
            source_system=source_system,
            section=None,
            author=author,
        )
        atoms_to_store.extend(full_atoms)
        
        # Deduplicate by content hash
        seen_hashes = set()
        unique_atoms = []
        for atom in atoms_to_store:
            if atom.content_hash not in seen_hashes:
                seen_hashes.add(atom.content_hash)
                unique_atoms.append(atom)
        
        # Store atoms
        stored = self.store.store_batch(unique_atoms)
        
        result.atoms_created = len(stored)
        result.atoms = [a.evidence_id for a in stored]
        
        logger.info(
            "Evidence extracted from document",
            document_id=document_id,
            atoms_created=result.atoms_created,
        )
        
        return result
    
    def extract_from_text(
        self,
        text: str,
        document_name: str,
        source_system: SourceSystem = SourceSystem.MANUAL_UPLOAD,
        evidence_type: EvidenceType = EvidenceType.CLINICAL_NOTE,
        author: str | None = None,
    ) -> ExtractionResult:
        """Extract evidence from raw text."""
        
        document_id = f"DOC-{uuid4().hex[:12].upper()}"
        document_hash = hashlib.sha256(text.encode()).hexdigest()
        
        result = ExtractionResult(
            document_id=document_id,
            document_name=document_name,
            document_hash=document_hash,
        )
        
        atoms = self._chunk_and_create_atoms(
            content=text,
            document_id=document_id,
            document_name=document_name,
            document_hash=document_hash,
            source_system=source_system,
            evidence_type=evidence_type,
            author=author,
        )
        
        stored = self.store.store_batch(atoms)
        
        result.atoms_created = len(stored)
        result.atoms = [a.evidence_id for a in stored]
        
        return result
    
    def _chunk_and_create_atoms(
        self,
        content: str,
        document_id: str,
        document_name: str,
        document_hash: str,
        source_system: SourceSystem,
        section: str | None = None,
        evidence_type: EvidenceType | None = None,
        author: str | None = None,
    ) -> list[EvidenceAtom]:
        """
        Chunk content into citation-safe units and create atoms.
        
        Chunking strategy:
        1. Split on sentence boundaries where possible
        2. Respect paragraph boundaries
        3. Keep chunks under MAX_CHUNK_CHARS
        4. Preserve medical phrases
        """
        if not content.strip():
            return []
        
        # Determine evidence type from section if not provided
        if evidence_type is None:
            evidence_type = self._infer_evidence_type(section, content)
        
        chunks = self._smart_chunk(content)
        atoms = []
        
        for i, (chunk, start_offset, end_offset) in enumerate(chunks):
            if not chunk.strip():
                continue
            
            # Estimate line numbers
            lines_before = content[:start_offset].count('\n')
            lines_in_chunk = chunk.count('\n')
            
            location = EvidenceLocation(
                section=section,
                line_start=lines_before + 1,
                line_end=lines_before + lines_in_chunk + 1,
                character_offset_start=start_offset,
                character_offset_end=end_offset,
            )
            
            try:
                atom = EvidenceAtom(
                    evidence_type=evidence_type,
                    source_system=source_system,
                    document_id=document_id,
                    document_name=document_name,
                    document_hash=document_hash,
                    content_excerpt=chunk.strip(),
                    location=location,
                    author=author,
                )
                atoms.append(atom)
            except ValueError as e:
                logger.warning(
                    "Failed to create evidence atom",
                    error=str(e),
                    chunk_index=i,
                )
        
        return atoms
    
    def _smart_chunk(self, content: str) -> list[tuple[str, int, int]]:
        """
        Split content into chunks with position tracking.
        
        Returns list of (chunk_text, start_offset, end_offset).
        """
        chunks = []
        
        # First, split by paragraphs (double newline)
        paragraphs = re.split(r'\n\s*\n', content)
        
        offset = 0
        for para in paragraphs:
            if not para.strip():
                offset += len(para) + 2  # Account for split
                continue
            
            # If paragraph is small enough, keep it whole
            if len(para) <= MAX_CHUNK_CHARS:
                chunks.append((para, offset, offset + len(para)))
                offset += len(para) + 2
                continue
            
            # Otherwise, split by sentences
            sentences = self._split_sentences(para)
            
            current_chunk = ""
            chunk_start = offset
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= MAX_CHUNK_CHARS:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append((current_chunk, chunk_start, chunk_start + len(current_chunk)))
                    current_chunk = sentence
                    chunk_start = offset + (len(para) - len(sentence))  # Approximate
            
            if current_chunk:
                chunks.append((current_chunk, chunk_start, chunk_start + len(current_chunk)))
            
            offset += len(para) + 2
        
        return chunks
    
    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences, preserving medical abbreviations."""
        # Simple sentence splitting - in production, use more sophisticated NLP
        # Avoid splitting on common medical abbreviations
        protected = text.replace("Dr.", "Dr§").replace("vs.", "vs§")
        protected = protected.replace("e.g.", "eg§").replace("i.e.", "ie§")
        protected = protected.replace("etc.", "etc§")
        
        sentences = re.split(r'(?<=[.!?])\s+', protected)
        
        # Restore protected periods
        sentences = [s.replace("§", ".") for s in sentences]
        
        return sentences
    
    def _infer_evidence_type(self, section: str | None, content: str) -> EvidenceType:
        """Infer evidence type from section name or content."""
        if section:
            section_lower = section.lower()
            
            if "history" in section_lower or "hpi" in section_lower:
                return EvidenceType.HISTORY
            elif "physical" in section_lower or "exam" in section_lower:
                return EvidenceType.CLINICAL_NOTE
            elif "lab" in section_lower or "result" in section_lower:
                return EvidenceType.LAB
            elif "imaging" in section_lower or "radiology" in section_lower:
                return EvidenceType.IMAGING
            elif "procedure" in section_lower or "operative" in section_lower:
                return EvidenceType.OPERATIVE_REPORT
            elif "discharge" in section_lower:
                return EvidenceType.DISCHARGE_SUMMARY
            elif "assessment" in section_lower or "diagnos" in section_lower:
                return EvidenceType.CLINICAL_NOTE
            elif "medication" in section_lower or "med" in section_lower:
                return EvidenceType.MEDICATION
            elif "vital" in section_lower:
                return EvidenceType.VITAL_SIGN
        
        # Infer from content keywords
        content_lower = content.lower()
        if "mg/dl" in content_lower or "mmol" in content_lower:
            return EvidenceType.LAB
        elif "blood pressure" in content_lower or "heart rate" in content_lower:
            return EvidenceType.VITAL_SIGN
        elif "ct scan" in content_lower or "mri" in content_lower or "x-ray" in content_lower:
            return EvidenceType.IMAGING
        
        return EvidenceType.CLINICAL_NOTE


# Global extractor instance
_extractor: EvidenceExtractor | None = None


def get_evidence_extractor() -> EvidenceExtractor:
    """Get the global evidence extractor."""
    global _extractor
    if _extractor is None:
        _extractor = EvidenceExtractor()
    return _extractor


async def extract_facts_from_evidence(atom: EvidenceAtom) -> None:
    """
    Extract discrete facts from an evidence atom using LLM.
    
    This is a stub for the stateless mode / demo.
    In a full implementation, this would call the reasoning engine.
    """
    # Simulate extraction
    logger.info("Fact extraction skipped for stateless demo", evidence_id=atom.evidence_id)
    pass

