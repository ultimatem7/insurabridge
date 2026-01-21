# Insurabridge Architecture

## System Overview

Insurabridge is a HIPAA-compliant, locally-hosted AI platform for health insurance intelligence. All PHI processing occurs on-device with zero external API calls.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Insurabridge                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Upload    │  │   Claims    │  │   Denials   │  │    Audit    │        │
│  │  Encounter  │  │  Generator  │  │   Appeals   │  │    Risk     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│  ┌──────▼────────────────▼────────────────▼────────────────▼──────┐        │
│  │                    REASONING ENGINE                             │        │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │        │
│  │  │ Evidence   │  │  Policy    │  │   Code     │  │ Citation  │ │        │
│  │  │ Extraction │  │  Matching  │  │  Mapping   │  │ Generator │ │        │
│  │  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │        │
│  └────────────────────────────┬───────────────────────────────────┘        │
│                               │                                             │
│  ┌────────────────────────────▼───────────────────────────────────┐        │
│  │                    LLM ORCHESTRATION                            │        │
│  │  ┌────────────────────────────────────────────────────────────┐│        │
│  │  │  Ollama (Gemma 4B) - Local Inference Only                  ││        │
│  │  │  • Deterministic temperature (0.1)                         ││        │
│  │  │  • Token-efficient prompts                                 ││        │
│  │  │  • Structured output parsing                               ││        │
│  │  └────────────────────────────────────────────────────────────┘│        │
│  └────────────────────────────┬───────────────────────────────────┘        │
│                               │                                             │
│  ┌──────────────┬─────────────┴─────────────┬──────────────┐               │
│  │              │                           │              │               │
│  ▼              ▼                           ▼              ▼               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  FHIR    │  │  ICD-10  │  │   CPT    │  │  Policy  │  │  Audit   │     │
│  │  Store   │  │  Index   │  │  Index   │  │  Store   │  │   Log    │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    SECURITY LAYER                                │       │
│  │  • AES-256 encryption at rest                                   │       │
│  │  • Role-based access control                                    │       │
│  │  • Immutable audit logging                                      │       │
│  │  • Session management                                           │       │
│  └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. Zero Trust for PHI
- No external network calls for inference
- All data encrypted at rest (AES-256-GCM)
- Memory cleared after processing
- No caching of PHI in plain text

### 2. Explainable AI
- Every decision includes:
  - Source documentation citation
  - Payer policy reference
  - Coding guideline justification
  - Confidence score with uncertainty bounds
- No black-box outputs

### 3. Defensive Coding Logic
- Explicit prevention of:
  - Auto-upcoding (codes must be evidence-supported)
  - Unsupported medical necessity claims
  - Policy hallucination (all policies from indexed store)
  - Bundling violations

### 4. Audit-First Design
- Immutable append-only logs
- Every action timestamped and attributed
- Reasoning chains preserved
- Rollback capability

## Layer Specifications

### Data Ingestion Layer

```
Input Sources:
├── EPIC FHIR R4 (primary)
│   ├── Patient
│   ├── Encounter
│   ├── Condition
│   ├── Procedure
│   ├── Observation
│   ├── DiagnosticReport
│   ├── Claim
│   ├── Coverage
│   └── ExplanationOfBenefit
├── Document Upload
│   ├── PDF (with local OCR)
│   ├── DOCX
│   ├── Plain text
│   └── HL7 v2.x messages
└── Manual Entry
    └── Structured forms
```

**Normalization Pipeline:**
1. Parse input format
2. Extract entities (NER via LLM)
3. Map to canonical schema
4. Validate completeness
5. Store with encryption

### Knowledge Layer

```
Knowledge Stores:
├── Coding Databases (SQLite + FTS5)
│   ├── ICD-10-CM (2024)
│   ├── ICD-10-PCS (2024)
│   ├── CPT (2024)
│   ├── HCPCS Level II
│   ├── MS-DRG v41
│   └── Modifier codes
├── Policy Store (ChromaDB vectors)
│   ├── CMS NCDs
│   ├── CMS LCDs by MAC
│   ├── Major payer policies
│   └── Coding guidelines (AMA, AHA)
└── Reference Data
    ├── NCCI edits
    ├── MUE values
    └── Place of service codes
```

**Versioning Strategy:**
- Each policy indexed with effective date
- Point-in-time queries supported
- Monthly update cycle
- Delta tracking for changes

### Reasoning Engine

The core differentiator. Uses structured chain-of-evidence reasoning:

```python
class ReasoningChain:
    """
    Every claim decision follows this structure:
    
    1. EVIDENCE EXTRACTION
       - What clinical facts support this?
       - Source: [document, page, section]
    
    2. CODE MAPPING
       - What codes are indicated?
       - Guideline: [source, section, rule]
    
    3. POLICY ALIGNMENT
       - Does payer cover this?
       - Policy: [payer, policy_id, section]
    
    4. MEDICAL NECESSITY
       - Is this service necessary?
       - Criteria: [LCD/NCD reference]
    
    5. COMPLIANCE CHECK
       - Any bundling issues?
       - Any modifier requirements?
       - NCCI edits clear?
    
    6. CONFIDENCE ASSESSMENT
       - Overall confidence score
       - Uncertainty factors
       - Human review flags
    """
```

### LLM Orchestration

**Model Selection Rationale:**
- Gemma 4B chosen for:
  - Reasonable inference speed on consumer hardware
  - Sufficient context window (8K tokens)
  - Good instruction following
  - Apache 2.0 license (commercial use)

**Prompt Engineering:**
- System prompts locked per task type
- Few-shot examples for consistency
- Structured output enforcement (JSON mode)
- Temperature: 0.1 (near-deterministic)

**Token Efficiency:**
- Chunked document processing
- Extractive summarization before reasoning
- Key-value caching where possible

### Security Model

```
┌─────────────────────────────────────────┐
│            Access Control               │
├─────────────────────────────────────────┤
│  ROLES:                                 │
│  ├── Admin: Full system access          │
│  ├── Billing Manager: Claims + Appeals  │
│  ├── Coder: Code validation only        │
│  ├── Auditor: Read-only + reports       │
│  └── Viewer: Dashboard only             │
├─────────────────────────────────────────┤
│  AUTHENTICATION:                        │
│  ├── Local accounts (bcrypt hashed)     │
│  ├── Optional LDAP/AD integration       │
│  └── Session timeout: 15 minutes        │
├─────────────────────────────────────────┤
│  ENCRYPTION:                            │
│  ├── At rest: AES-256-GCM               │
│  ├── Key derivation: Argon2id           │
│  └── Key storage: OS keychain           │
├─────────────────────────────────────────┤
│  AUDIT:                                 │
│  ├── Append-only SQLite log             │
│  ├── Cryptographic chaining             │
│  └── Tamper detection                   │
└─────────────────────────────────────────┘
```

## Data Flow

### Claim Generation Flow

```
1. User uploads encounter documentation
                    │
                    ▼
2. Document Parser extracts structured data
   - OCR if needed (Tesseract, local)
   - NER for clinical entities
   - Date/provider extraction
                    │
                    ▼
3. Evidence Assembler creates clinical summary
   - Diagnoses with supporting notes
   - Procedures with operative details
   - Timeline of care
                    │
                    ▼
4. Code Mapper suggests codes
   - ICD-10 for diagnoses
   - CPT/HCPCS for procedures
   - Each code linked to evidence
                    │
                    ▼
5. Policy Validator checks coverage
   - Retrieve patient coverage
   - Match against payer policies
   - Flag potential issues
                    │
                    ▼
6. Compliance Engine runs checks
   - NCCI edits
   - MUE limits
   - Modifier requirements
   - Bundling rules
                    │
                    ▼
7. Claim Assembler generates output
   - CMS-1500 or UB-04 format
   - Supporting documentation
   - Confidence scores per line
                    │
                    ▼
8. Human Review Queue
   - Mandatory before submission
   - Accept/modify/reject per line
   - Comments captured
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python 3.11 + FastAPI | Healthcare ML ecosystem, async support |
| Frontend | Next.js 14 + React | Modern UI, SSR for security |
| Database | SQLite + SQLCipher | Local, encrypted, no server needed |
| Vector Store | ChromaDB | Local embeddings, good for policies |
| LLM | Ollama + Gemma 4B | Local inference, permissive license |
| OCR | Tesseract 5 | Local, accurate, open source |
| FHIR | fhir.resources | Python FHIR R4 models |

## Deployment Model

```
Local Installation (Primary):
├── Windows installer (MSI)
├── macOS installer (DMG)
└── Linux packages (deb/rpm)

Hardware Requirements:
├── Minimum: 16GB RAM, 8 cores, 50GB storage
├── Recommended: 32GB RAM, 16 cores, 100GB SSD
└── GPU optional (CUDA for faster inference)
```

## MVP Scope (90 Days)

### Days 1-30: Foundation
- [ ] Core ingestion pipeline (FHIR + PDF)
- [ ] ICD-10/CPT lookup with search
- [ ] Basic LLM integration
- [ ] Claim generation (CMS-1500)
- [ ] Minimal viable UI

### Days 31-60: Intelligence
- [ ] Reasoning engine with citations
- [ ] Policy store with major payers
- [ ] Denial classification
- [ ] Appeal letter generation
- [ ] Audit risk scoring

### Days 61-90: Production Ready
- [ ] Full security implementation
- [ ] EPIC sandbox integration
- [ ] Performance optimization
- [ ] Documentation
- [ ] Pilot preparation

## Competitive Moat

1. **Local-First**: Only solution with zero PHI exposure
2. **Explainability**: Full reasoning chains, not black boxes
3. **EPIC Native**: App Orchard certified path
4. **Defensible Data**: Local policy + workflow learning
5. **Regulatory Positioning**: HIPAA by architecture, not policy

