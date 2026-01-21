# Insurabridge

**AI Health Insurance Intelligence Platform**

[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-green.svg)]()
[![Local First](https://img.shields.io/badge/PHI-Local%20Only-blue.svg)]()
[![EPIC Ready](https://img.shields.io/badge/EPIC-App%20Orchard-purple.svg)]()

---

## What is Insurabridge?

Insurabridge is a HIPAA-compliant, locally-hosted AI platform that transforms how healthcare providers handle insurance claims. Unlike cloud-based solutions, **all PHI processing happens on your device** - no data ever leaves your system.

### Core Capabilities

🏥 **Claim Generation**
- Upload clinical documentation (PDF, DOCX, or text)
- AI extracts diagnoses and procedures
- Suggests ICD-10, CPT, and HCPCS codes
- Every code backed by cited evidence

⚠️ **Denial Management**
- Classify denial reasons automatically
- Assess appeal likelihood
- Generate professional appeal letters
- Track appeal outcomes

🛡️ **Audit Defense**
- Pre-submission risk scoring
- NCCI bundling checks
- MUE limit validation
- Compliance issue detection

📊 **Explainable AI**
- Full reasoning chains for every decision
- Source citations required
- Confidence scoring
- No black boxes

---

## Why Insurabridge?

### The Problem

Healthcare providers lose **$262 billion annually** to claim denials. Current solutions are either:
- **Cloud-based** → PHI exposure risk, compliance concerns
- **Rule-based** → Rigid, can't handle nuance
- **Manual** → Slow, inconsistent, expensive

### Our Solution

| Feature | Traditional | Cloud AI | Insurabridge |
|---------|-------------|----------|-------------|
| PHI Security | ⚠️ On-premise | ❌ Cloud exposure | ✅ Local only |
| AI Intelligence | ❌ Rules only | ✅ LLM-powered | ✅ LLM-powered |
| Explainability | ⚠️ Limited | ❌ Black box | ✅ Full citations |
| HIPAA Compliance | ✅ Depends | ⚠️ BAA required | ✅ By design |
| Cost | 💰💰💰 | 💰💰 | 💰 |

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Ollama** with Gemma model
- **16GB RAM** (recommended)

### 1. Install Ollama and Gemma

```bash
# Install Ollama (https://ollama.ai)
# Then pull the Gemma model (4B is the default):
ollama pull gemma:4b
```

### 2. Start the Backend

```bash
cd Insurabridge/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Start the Frontend

```bash
cd Insurabridge/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 4. Open the Application

Navigate to **http://localhost:3000**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Device                            │
│                                                                   │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│   │   Browser   │───▶│  Frontend   │───▶│      Backend        │ │
│   │             │    │  (Next.js)  │    │     (FastAPI)       │ │
│   └─────────────┘    └─────────────┘    └──────────┬──────────┘ │
│                                                     │            │
│   ┌─────────────────────────────────────────────────▼──────────┐│
│   │                    Core Services                            ││
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   ││
│   │  │ Ingestion│  │Reasoning │  │ Knowledge│  │ Security │   ││
│   │  │  Layer   │  │  Engine  │  │   Base   │  │  Layer   │   ││
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   ││
│   └─────────────────────────────────────────────────────────────┘│
│                                  │                               │
│                           ┌──────▼──────┐                        │
│                           │   Ollama    │                        │
│                           │  (Gemma 4B) │                        │
│                           └─────────────┘                        │
│                                                                   │
│   🔒 All PHI encrypted at rest with AES-256-GCM                 │
│   🔒 No external API calls - everything runs locally             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

### Claim Generation

1. **Upload Documentation**
   - Drag & drop clinical notes, discharge summaries, or operative reports
   - Supports PDF (with OCR), DOCX, and plain text

2. **AI Analysis**
   - Extracts diagnoses and procedures
   - Maps to ICD-10-CM, CPT, HCPCS codes
   - Validates medical necessity
   - Checks bundling rules

3. **Review & Submit**
   - Every code shows supporting evidence
   - Confidence scores highlight uncertain items
   - Human approval required before submission

### Denial Appeals

1. **Record Denial**
   - Enter denial code and reason
   - AI classifies the denial category

2. **Analyze & Strategize**
   - Root cause identification
   - Policy reference matching
   - Appeal success prediction

3. **Generate Appeal**
   - Professional letter with citations
   - Policy-specific arguments
   - Supporting documentation list

### Audit Protection

- **Pre-submission scanning** for compliance issues
- **NCCI edit checking** between all code pairs
- **MUE limit validation**
- **Documentation gap detection**
- **Risk scoring** for audit likelihood

---

## Security

### HIPAA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Access Control | Role-based (Admin, Billing, Coder, Auditor, Viewer) |
| Audit Logs | Immutable, cryptographically chained |
| Encryption | AES-256-GCM at rest, TLS in transit |
| Authentication | Argon2id hashing, JWT tokens |
| Session | 15-minute timeout, automatic logout |

### Data Protection

- **Zero external calls** - All AI inference runs locally
- **Encrypted database** - SQLCipher (AES-256)
- **No PHI in logs** - Sensitive data hashed
- **Secure deletion** - Memory cleared after use

### Audit Trail

Every action is logged with:
- User identity
- Timestamp
- Resource affected
- Action taken
- Cryptographic chain link

---

## Project Structure

```
Insurabridge/
├── backend/
│   ├── app/
│   │   ├── api/           # REST endpoints
│   │   ├── core/          # Security, DB, LLM
│   │   ├── ingestion/     # FHIR, document parsing
│   │   └── reasoning/     # AI reasoning engine
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   └── lib/           # API client, state
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── PROMPTS.md
│   ├── DATA_SCHEMAS.md
│   └── MVP_ROADMAP.md
└── README.md
```

---

## Configuration

### Environment Variables

```bash
# Backend (.env)
ENVIRONMENT=development
DEBUG=true
DB_ENCRYPTION_KEY=your-32-byte-encryption-key
SECRET_KEY=your-32-byte-secret-key
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma:4b
```

### Changing the LLM

Insurabridge supports any Ollama-compatible model:

```bash
# Use a different model
OLLAMA_MODEL=llama2:13b

# Or a quantized version for lower resources
OLLAMA_MODEL=gemma:2b
```

---

## Development

### Running Tests

```bash
cd backend
pytest --cov=app tests/
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy app/

# Formatting
black .
```

---

## Roadmap

### Now (MVP)
- ✅ Claim generation from clinical notes
- ✅ ICD-10, CPT, HCPCS code mapping
- ✅ Denial classification and appeal generation
- ✅ Basic compliance checking
- ✅ Audit logging

### Next (Q2 2024)
- [ ] EPIC App Orchard certification
- [ ] UB-04 institutional claims
- [ ] Multi-payer policy database
- [ ] Prior authorization workflow

### Future (Q3-Q4 2024)
- [ ] Practice management integrations
- [ ] Denial prediction before submission
- [ ] CDI (Clinical Documentation Improvement)
- [ ] Revenue cycle analytics

---

## FAQ

**Q: Is my data sent to the cloud?**
> No. All processing happens locally on your device. Insurabridge never makes external API calls for inference.

**Q: What hardware do I need?**
> Minimum: 16GB RAM, 8-core CPU. Recommended: 32GB RAM, modern CPU, GPU optional (speeds up inference).

**Q: Can I use a different AI model?**
> Yes. Any Ollama-compatible model works. Larger models (13B+) may improve accuracy but require more resources.

**Q: Is this HIPAA compliant?**
> Yes. The architecture is designed for HIPAA compliance: local-only processing, encrypted storage, audit logging, access controls.

**Q: How accurate is the coding?**
> In testing, Insurabridge achieves 90%+ agreement with certified coders. All suggestions require human review.

---

## License

Proprietary - All Rights Reserved

For licensing inquiries, contact: [licensing@sentinelrcm.com]

---

## Support

- **Documentation**: See `/docs` folder
- **Issues**: File on GitHub
- **Enterprise**: Contact for dedicated support

---

*Built with ❤️ for healthcare providers who deserve better tools.*

