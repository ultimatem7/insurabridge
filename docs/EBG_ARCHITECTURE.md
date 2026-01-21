# Evidence-Bound Generation (EBG) Architecture

## Executive Summary

Evidence-Bound Generation is the architectural constraint that makes Insurabridge **structurally incapable** of generating unsupported output. Every claim, code, and conclusion must be traceable to primary source evidence.

---

## Core Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   "The system cannot produce output without provenance."                    │
│                                                                             │
│   This is not a policy - it is an architectural constraint.                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVIDENCE-BOUND GENERATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                                                        │
│  │    Document     │                                                        │
│  │    Upload       │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EVIDENCE EXTRACTION LAYER                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │   Parse     │→ │   Chunk     │→ │   Create    │                  │   │
│  │  │  Document   │  │  (≤300 tok) │  │ EvidenceAtom│                  │   │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘                  │   │
│  │                                           │                          │   │
│  │                                    ┌──────▼──────┐                   │   │
│  │                                    │  Immutable  │                   │   │
│  │                                    │   Store     │                   │   │
│  │                                    └──────┬──────┘                   │   │
│  └───────────────────────────────────────────┼─────────────────────────┘   │
│                                               │                             │
│           ┌───────────────────────────────────┘                             │
│           │                                                                 │
│           ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     FACT EXTRACTION LAYER                            │   │
│  │                                                                      │   │
│  │  Constraint: NO INFERENCE allowed                                   │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │  LLM Prompt:                                                 │    │   │
│  │  │  "Extract ONLY literal facts. NO inference. NO summary."    │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                      │   │
│  │  Output: Fact { fact_id, fact_text, evidence_id }                   │   │
│  │                                                                      │   │
│  │  Validation: Reject facts not found in source text                  │   │
│  └──────────────────────────────────────┬──────────────────────────────┘   │
│                                          │                                  │
│                                          ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CODE MAPPING ENGINE                              │   │
│  │                                                                      │   │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐                 │   │
│  │  │  Fact →    │───▶│  Verify    │───▶│  Build     │                 │   │
│  │  │  Code Map  │    │  in KB     │    │  Proof     │                 │   │
│  │  └────────────┘    └────────────┘    └────────────┘                 │   │
│  │                                                                      │   │
│  │  Required for each code:                                            │   │
│  │  ✓ Justification fact(s)                                           │   │
│  │  ✓ Clinical evidence IDs                                           │   │
│  │  ✓ Codebook reference                                              │   │
│  │  ○ Payer policy reference (recommended)                            │   │
│  └──────────────────────────────────────┬──────────────────────────────┘   │
│                                          │                                  │
│                                          ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     PROOF CHAIN ASSEMBLY                             │   │
│  │                                                                      │   │
│  │  ProofChain {                                                       │   │
│  │    claim_element: "CPT 99214"                                       │   │
│  │    steps: [                                                          │   │
│  │      { step: "Diagnosis confirmed", evidence: [EV-001], ✓ }        │   │
│  │      { step: "Service documented", evidence: [EV-002], ✓ }         │   │
│  │      { step: "Medical necessity", evidence: [], ✗ }  ← BLOCKS      │   │
│  │    ]                                                                 │   │
│  │    status: INCOMPLETE ← Cannot export                               │   │
│  │  }                                                                   │   │
│  └──────────────────────────────────────┬──────────────────────────────┘   │
│                                          │                                  │
│                                          ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     VALIDATION GATE                                  │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                                                              │    │   │
│  │  │   IF any element lacks evidence:                            │    │   │
│  │  │     → Mark as UNSUPPORTED                                   │    │   │
│  │  │     → BLOCK export/submission                               │    │   │
│  │  │     → Flag documentation gap                                │    │   │
│  │  │                                                              │    │   │
│  │  │   This is NOT a warning. This is a VETO.                    │    │   │
│  │  │                                                              │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────┬──────────────────────────────┘   │
│                                          │                                  │
│                                          ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     OUTPUT ASSEMBLY                                  │   │
│  │                                                                      │   │
│  │  Every field in output includes:                                    │   │
│  │  {                                                                   │   │
│  │    "field": "primary_diagnosis",                                    │   │
│  │    "value": "K35.80",                                               │   │
│  │    "evidence_ids": ["EV-1023", "EV-1024"],                         │   │
│  │    "confidence": 0.97                                               │   │
│  │  }                                                                   │   │
│  │                                                                      │   │
│  │  Fields without evidence_ids = REJECTED                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### EvidenceAtom

The fundamental, immutable unit of evidence:

```python
class EvidenceAtom:
    evidence_id: str           # "EV-ABC123" - unique identifier
    evidence_type: Enum        # clinical_note, lab, imaging, policy, etc.
    source_system: Enum        # EPIC, Manual Upload, FHIR
    
    document_id: str           # Reference to source document
    document_name: str
    document_hash: str         # SHA-256 of original document
    
    content_excerpt: str       # The actual evidence text (≤2000 chars)
    location: EvidenceLocation # Page, line, section
    
    content_hash: str          # SHA-256 of content for integrity
    extraction_confidence: float
    
    # IMMUTABLE after creation - raises error on modification attempt
```

### Fact

A literal fact extracted from evidence:

```python
class Fact:
    fact_id: str               # "FACT-ABC123"
    fact_text: str             # The literal statement
    evidence_id: str           # MANDATORY link to EvidenceAtom
    fact_type: str             # diagnosis, procedure, finding, etc.
    
    is_literal: bool           # False if ANY interpretation was needed
    extraction_confidence: float
    
    # Validation: Rejects inference language ("likely", "suggests", etc.)
```

### ProofChain

Structured reasoning with mandatory citations:

```python
class ProofChain:
    chain_id: str
    claim_element: str         # What this proves (e.g., "CPT 99214")
    
    steps: List[ProofStep]     # Each step must have evidence
    
    status: Enum               # valid, incomplete, unsupported, invalid
    
    # Computed:
    total_steps: int
    steps_with_evidence: int
    missing_evidence_steps: List[int]
    
    # A chain is VALID only if ALL steps have evidence
```

### CodeJustification

Complete justification for a suggested code:

```python
class CodeJustification:
    code: str
    code_type: str
    
    justification_fact_id: str      # MANDATORY
    clinical_evidence_ids: List[str] # MANDATORY, min length 1
    codebook_reference: str          # MANDATORY
    payer_policy_reference: str      # Recommended
    
    proof_chain: ProofChain          # Full reasoning
    
    is_supported: bool               # Computed from above
    unsupported_reason: str          # If not supported, why
```

---

## Validation Rules

### Blocking Errors (CANNOT proceed)

| Rule | Condition | Remediation |
|------|-----------|-------------|
| NO_EVIDENCE | Field has empty evidence_ids | Link to clinical documentation |
| INVALID_REFERENCE | Evidence ID doesn't exist | Provide valid evidence ID |
| INCOMPLETE_PROOF | Proof chain has unsupported steps | Add evidence for missing steps |
| NO_CODEBOOK | Code lacks codebook reference | Add coding guideline reference |
| INFERENCE_DETECTED | Fact contains speculation | Use only literal statements |

### Warnings (Human override allowed)

| Rule | Condition | Guidance |
|------|-----------|----------|
| LOW_CONFIDENCE | Confidence < 0.6 | Review evidence quality |
| NO_POLICY | Procedure lacks payer policy | Add policy reference |
| SINGLE_EVIDENCE | Only one evidence atom | Consider additional documentation |

---

## LLM Constraints

### Fact Extraction Prompt

```
CRITICAL RULES - VIOLATIONS WILL BE REJECTED:
1. Extract ONLY facts that are EXPLICITLY stated
2. DO NOT infer, deduce, or assume anything
3. Each fact must be traceable to specific text
4. If not explicitly stated, DO NOT extract

FORBIDDEN:
- "Patient likely has..." (inference)
- "This suggests..." (interpretation)
- Any speculation or clinical reasoning

ALLOWED:
- Direct quotes from documentation
- Measurements with explicit values
- Documented diagnoses and procedures
```

### Code Mapping Prompt

```
For each code:
1. code: The specific code
2. justification_facts: FACT-IDs that support this code
3. codebook_reference: The specific guideline section
4. confidence: Based on evidence strength

If NO codes can be justified from the facts, return []

DO NOT SUGGEST CODES WITHOUT FACT CITATIONS.
```

---

## UI Requirements

### Mandatory UI Elements

1. **Citation badges** on every code
   - Clickable to view source evidence
   - Color-coded by confidence

2. **"Why this code?" expandable panels**
   - Shows proof chain steps
   - Links to source documents
   - Highlights any gaps

3. **Unsupported warnings**
   - Red banner for blocking issues
   - Cannot dismiss without adding evidence
   - Lists specific documentation gaps

4. **Evidence popover on hover**
   - Source document name
   - Exact excerpt
   - Location (page/line/section)

5. **Proof chain visualization**
   - Step-by-step reasoning
   - Green check for supported steps
   - Red X for missing evidence

---

## Performance Considerations

### For Gemma 4B

| Concern | Mitigation |
|---------|------------|
| Context length | Chunk documents to ≤300 tokens per atom |
| Inference time | Batch fact extraction per document |
| Memory | Process documents sequentially, not parallel |
| Accuracy | Use temperature=0.0 for fact extraction |

### Storage

| Store | Size Estimate | Strategy |
|-------|---------------|----------|
| Evidence atoms | ~1KB each | Append-only JSONL |
| Proof chains | ~5KB each | Embedded in claim |
| Facts | ~200B each | In-memory + disk |

---

## Limitations & Fallbacks

### Known Limitations

1. **OCR quality** - Scanned documents may have low extraction confidence
   - Fallback: Flag for manual entry if confidence < 0.7

2. **Complex reasoning** - Multi-step clinical logic may be oversimplified
   - Fallback: Require human review for multi-step proofs

3. **Ambiguous documentation** - Unclear notes may not yield extractable facts
   - Fallback: Report "insufficient documentation" rather than guess

### Safe Fallbacks

1. When evidence is uncertain → Flag as REVIEW_REQUIRED
2. When code cannot be justified → Do not suggest it
3. When proof chain is incomplete → Block export
4. When confidence is low → Require human confirmation

---

## Audit Trail

Every evidence operation is logged:

```python
{
    "event_type": "evidence.created",
    "evidence_id": "EV-ABC123",
    "document_id": "DOC-XYZ",
    "user_id": "USER-001",
    "timestamp": "2024-01-15T10:30:00Z",
    "action": "extract",
    "details": {
        "extraction_confidence": 0.95,
        "chunk_index": 3
    }
}
```

---

## Compliance Mapping

| HIPAA Requirement | EBG Implementation |
|-------------------|-------------------|
| Audit controls | Full evidence usage logging |
| Integrity | SHA-256 hashes on all evidence |
| Documentation | Complete proof chains |
| Accountability | User attribution on every action |

| Payer Audit Defense | EBG Support |
|---------------------|-------------|
| "Why this code?" | Proof chain with citations |
| "Where is documentation?" | Evidence atom with location |
| "Medical necessity?" | Dedicated proof chain type |

---

## Summary

Evidence-Bound Generation transforms Insurabridge from an AI that *tries* to be accurate into a system that *cannot* produce unsupported output.

The constraint is architectural, not behavioral:
- **EvidenceAtoms** are immutable
- **Facts** must link to evidence
- **Codes** must cite facts and guidelines
- **Proof chains** must be complete
- **Validation** has veto power

The result: Every claim, every code, every conclusion has a clickable trail back to source documentation.

