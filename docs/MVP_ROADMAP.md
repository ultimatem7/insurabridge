# Insurabridge MVP Roadmap

## Executive Summary

Insurabridge is a HIPAA-compliant, locally-hosted AI platform for health insurance claims intelligence. This roadmap outlines the path from concept to hospital pilot in 90 days.

---

## Phase 1: Foundation (Days 1-30)

### Week 1-2: Core Infrastructure

**Backend Setup**
- [x] FastAPI project structure with async support
- [x] SQLite + SQLCipher encrypted database
- [x] Role-based access control (RBAC)
- [x] Audit logging with cryptographic chaining
- [x] Session management with short-lived JWTs

**LLM Integration**
- [x] Ollama client with Gemma 4B
- [x] Structured output parsing
- [x] System prompts for each task type
- [x] Temperature and token optimization

**Deliverables:**
- Working backend API
- Authentication system
- LLM inference pipeline

### Week 3-4: Data Pipeline

**Ingestion Layer**
- [x] FHIR R4 resource parsing
- [x] PDF parsing with OCR fallback
- [x] DOCX and text file parsing
- [x] HL7 v2.x message parsing
- [x] Schema normalization

**Knowledge Base**
- [x] ICD-10-CM/PCS code database
- [x] CPT code database
- [x] HCPCS Level II database
- [x] NCCI edit tables
- [x] MUE limits
- [ ] Policy document indexing (ChromaDB)

**Deliverables:**
- Document upload and parsing
- Code lookup with search
- Basic policy retrieval

---

## Phase 2: Intelligence (Days 31-60)

### Week 5-6: Reasoning Engine

**Evidence Extraction**
- [x] Clinical entity extraction via LLM
- [x] Citation linking to source documents
- [x] Confidence scoring per extraction
- [ ] Multi-document synthesis

**Code Mapping**
- [x] Diagnosis → ICD-10 mapping
- [x] Procedure → CPT/HCPCS mapping
- [x] Modifier recommendation
- [ ] Specificity optimization
- [ ] Laterality/anatomical checking

**Deliverables:**
- Automated code suggestion from clinical notes
- Evidence-based rationale for each code

### Week 7-8: Compliance & Validation

**Compliance Engine**
- [x] NCCI bundling checks
- [x] MUE limit validation
- [x] Modifier requirement checks
- [ ] Global period checking
- [ ] Payer-specific rules

**Claim Generation**
- [x] CMS-1500 data structure
- [ ] UB-04 data structure
- [ ] Charge calculation (fee schedule)
- [ ] Export to EDI 837

**Deliverables:**
- Complete claim generation workflow
- Compliance issue detection
- Audit risk scoring

### Week 8: Denial Handling

**Denial Analysis**
- [x] Denial classification (5 categories)
- [x] Policy reference matching
- [x] Appeal likelihood scoring
- [ ] Historical pattern analysis

**Appeal Generation**
- [x] Appeal letter templates
- [x] Citation insertion
- [ ] Level-appropriate formatting
- [ ] Attachment recommendation

**Deliverables:**
- Denial intake and classification
- Generated appeal letters

---

## Phase 3: Production Ready (Days 61-90)

### Week 9-10: Frontend Polish

**User Interface**
- [x] Dashboard with key metrics
- [x] Claim generation workflow
- [x] Code suggestion display with confidence
- [ ] Denial management view
- [ ] Appeal tracking
- [ ] Audit log viewer

**User Experience**
- [x] Dark/light mode
- [x] Responsive design
- [ ] Keyboard shortcuts
- [ ] Bulk operations
- [ ] Export functionality

**Deliverables:**
- Production-quality UI
- Complete workflow coverage

### Week 11-12: Integration & Security

**EPIC Integration**
- [ ] App Orchard registration
- [ ] OAuth2 authentication flow
- [ ] FHIR resource fetching
- [ ] Sandbox testing

**Security Hardening**
- [x] Encrypted storage (SQLCipher)
- [x] Secure password hashing (Argon2id)
- [x] Immutable audit logs
- [ ] Penetration testing
- [ ] HIPAA compliance checklist
- [ ] Security documentation

**Deliverables:**
- EPIC sandbox connection
- Security audit report

### Week 12: Pilot Preparation

**Documentation**
- [ ] User manual
- [ ] Admin guide
- [ ] API documentation
- [ ] Training materials

**Deployment**
- [ ] Windows installer (MSI)
- [ ] macOS installer (DMG)
- [ ] Linux packages
- [ ] Update mechanism

**Pilot Support**
- [ ] Onboarding checklist
- [ ] Support channel setup
- [ ] Feedback collection system

**Deliverables:**
- Installable packages
- Complete documentation
- Pilot site agreement

---

## Success Metrics

### Technical
| Metric | Target | Measurement |
|--------|--------|-------------|
| Claim generation time | < 30 seconds | From upload to draft |
| Code accuracy | > 90% | Compared to human review |
| Compliance detection | > 95% | NCCI/MUE issues caught |
| System uptime | 99.5% | Monitored availability |

### Business
| Metric | Target | Measurement |
|--------|--------|-------------|
| Denial rate reduction | 15% | Before/after comparison |
| Appeal success rate | 70% | For AI-generated appeals |
| Coding time savings | 40% | Coder time study |
| Clean claim rate | 95% | First-pass acceptance |

---

## Risk Mitigation

### Technical Risks

**Risk:** LLM hallucination in code suggestions
- **Mitigation:** All codes verified against knowledge base
- **Mitigation:** Confidence scoring with mandatory human review
- **Mitigation:** Explicit "I don't know" responses when uncertain

**Risk:** Performance on commodity hardware
- **Mitigation:** Gemma 4B selected for efficiency
- **Mitigation:** Quantized models as fallback
- **Mitigation:** Async processing for large documents

**Risk:** OCR accuracy for scanned documents
- **Mitigation:** Tesseract 5 with preprocessing
- **Mitigation:** Confidence flags for OCR content
- **Mitigation:** Manual entry fallback

### Regulatory Risks

**Risk:** HIPAA violation through data exposure
- **Mitigation:** Zero external API calls
- **Mitigation:** All data encrypted at rest
- **Mitigation:** Comprehensive audit logging
- **Mitigation:** No PHI in logs or error messages

**Risk:** Incorrect coding leading to compliance issues
- **Mitigation:** Mandatory human review before submission
- **Mitigation:** Clear "AI-assisted" labeling
- **Mitigation:** Reasoning transparency

---

## Team Structure (Suggested)

| Role | Responsibility | FTE |
|------|----------------|-----|
| Technical Lead | Architecture, LLM integration | 1.0 |
| Backend Engineer | API, database, security | 1.0 |
| Frontend Engineer | React, UX | 1.0 |
| Healthcare SME | Coding rules, compliance | 0.5 |
| QA Engineer | Testing, security audit | 0.5 |

---

## Post-MVP Expansion

### 6-Month Horizon
1. **Multi-payer support** - Commercial payer policy databases
2. **Practice management integration** - AdvancedMD, Kareo, etc.
3. **Real-time claim scrubbing** - Pre-submission validation
4. **Denial prediction** - Risk scoring before submission

### 12-Month Horizon
1. **Inpatient coding** - DRG optimization
2. **Prior authorization** - Automated requests
3. **Revenue cycle analytics** - Pattern detection
4. **Multi-site deployment** - Central policy management

### 24-Month Horizon
1. **Payer negotiation support** - Contract analysis
2. **Clinical documentation improvement** - CDI integration
3. **Audit defense automation** - Full audit response generation
4. **Regulatory change monitoring** - Automatic policy updates

---

## Investment Requirements

### Seed (MVP Development)
- **Amount:** $500K - $750K
- **Use:** Team of 3-4 for 6 months
- **Milestone:** Working pilot at 2-3 sites

### Series A (Market Entry)
- **Amount:** $3M - $5M
- **Use:** Team of 12-15, sales, compliance
- **Milestone:** 50 paying customers, $1M ARR

### Key Metrics for Investors
- **TAM:** $20B revenue cycle management market
- **Beachhead:** 100K+ physician practices in US
- **Unit economics:** $500-5000/month per practice
- **Moat:** Local data, workflow lock-in, regulatory compliance

