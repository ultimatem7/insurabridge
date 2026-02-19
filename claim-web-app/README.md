# Healthcare Claims Automation Platform

**Production-Grade EHR-Integrated Insurance Claim Generation System**

## Overview

This application automates insurance claim generation from EHR data using SMART on FHIR integration and local AI processing. Designed for on-premise hospital deployment with HIPAA compliance.

## Features

- ✅ Multi-EHR provider authentication (Epic, Cerner, eClinicalWorks, Athenahealth, Meditech)
- ✅ SMART on FHIR OAuth2 integration
- ✅ FHIR R4 resource extraction and normalization
- ✅ Local LLM-based claim generation
- ✅ Structured claim output (CMS-1500 format)
- ✅ Evidence-based citations
- ✅ Zero external cloud dependencies
- ✅ PostgreSQL data persistence
- ✅ Docker-based deployment
- ✅ HIPAA-conscious security

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Hospital Network (On-Premise)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐  │
│  │   React UI   │────▶│  FastAPI     │────▶│  PostgreSQL    │  │
│  │  Port 3000   │     │  Port 8000   │     │  Port 5432     │  │
│  └──────┬───────┘     └──────┬───────┘     └────────────────┘  │
│         │                    │                                  │
│         │                    │                                  │
│         │            ┌───────▼────────┐                         │
│         │            │  EHR Adapters  │                         │
│         │            │  • Epic        │                         │
│         │            │  • Cerner      │                         │
│         │            │  • Others      │                         │
│         │            └───────┬────────┘                         │
│         │                    │                                  │
│         │            ┌───────▼────────┐                         │
│         └───────────▶│  Local LLM     │                         │
│                      │  Port 8001     │                         │
│                      └────────────────┘                         │
│                                                                  │
│  All PHI stays within this boundary ───────────────────────────▶│
└─────────────────────────────────────────────────────────────────┘
         │
         │ OAuth redirect only
         ▼
   [EHR Provider Auth]
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL (via Docker)
- Local LLM service (Ollama or similar)

### Installation

1. **Clone and configure:**

```bash
cd claim-web-app
cp .env.example .env
# Edit .env with your configuration
```

2. **Start services:**

```bash
docker-compose up -d
```

3. **Initialize database:**

```bash
docker-compose exec backend alembic upgrade head
```

4. **Access application:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development Mode

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## EHR Provider Setup

### Epic Integration

1. Register your application at Epic App Orchard
2. Obtain client ID and redirect URI
3. Configure in `.env`:

```
EPIC_CLIENT_ID=your_client_id
EPIC_REDIRECT_URI=http://localhost:8000/auth/epic/callback
EPIC_FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
```

### Cerner Integration

1. Register at Cerner Code Console
2. Configure credentials
3. Update `.env` with Cerner settings

### Other Providers

Follow similar OAuth registration process for:
- eClinicalWorks
- Athenahealth
- Meditech

## Project Structure

```
claim-web-app/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core utilities
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── ehr/          # EHR adapters
│   │   │   ├── fhir/         # FHIR processing
│   │   │   └── claims/       # Claim generation
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API clients
│   │   ├── hooks/            # Custom hooks
│   │   └── types/            # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Security Considerations

### HIPAA Compliance

- ✅ All PHI processing on-premise
- ✅ Encrypted database connections (TLS)
- ✅ Secure token storage (encrypted cookies)
- ✅ Audit logging for all PHI access
- ✅ Role-based access control
- ✅ Session timeout (15 minutes)
- ✅ No external API calls with PHI

### Network Security

- Deploy behind hospital firewall
- Use reverse proxy (nginx) with TLS
- Configure CORS appropriately
- Implement rate limiting
- Use environment variables for secrets

### Data Retention

Configure in `.env`:
```
DATA_RETENTION_DAYS=2555  # 7 years for HIPAA
AUDIT_LOG_RETENTION_DAYS=2555
```

## API Documentation

### Authentication Endpoints

```
POST /auth/{provider}/login    - Initiate OAuth flow
GET  /auth/{provider}/callback - OAuth callback
POST /auth/logout              - End session
GET  /auth/status              - Check auth status
```

### FHIR Endpoints

```
GET  /fhir/patients           - List patients
GET  /fhir/encounters/{id}    - Get encounter details
GET  /fhir/clinical-notes/{id} - Get clinical documentation
```

### Claims Endpoints

```
POST /claims/generate         - Generate claim from encounter
GET  /claims/{id}             - Retrieve generated claim
GET  /claims                  - List claims
POST /claims/{id}/export      - Export claim data
```

## Claim Generation Flow

1. **User authenticates** with EHR provider
2. **Select encounter** from patient list
3. **System fetches** FHIR resources:
   - Patient demographics
   - Encounter details
   - Conditions (diagnoses)
   - Procedures
   - Clinical notes
   - Lab results
4. **Normalize data** to internal schema
5. **Send to local LLM** for claim generation
6. **Receive structured claim** with evidence
7. **Display in UI** with copy/export options

## Local LLM Integration

The system expects a local LLM service at `http://localhost:8001`.

**Request format:**
```json
POST /generate-claim
{
  "patient": {...},
  "encounter": {...},
  "conditions": [...],
  "procedures": [...],
  "clinical_notes": "..."
}
```

**Response format:**
```json
{
  "claim_id": "CLM-12345",
  "diagnoses": [
    {
      "code": "I10",
      "description": "Essential hypertension",
      "confidence": 0.95
    }
  ],
  "procedures": [
    {
      "code": "99214",
      "description": "Office visit",
      "modifiers": ["25"],
      "confidence": 0.92
    }
  ],
  "supporting_evidence": [...],
  "audit_trail": [...]
}
```

## Deployment

### Docker Deployment (Recommended)

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

- Database credentials
- EHR provider OAuth credentials
- Session secrets
- LLM endpoint
- Security settings

### Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback
docker-compose exec backend alembic downgrade -1
```

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database connection
curl http://localhost:8000/health/db

# LLM service
curl http://localhost:8000/health/llm
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres
```

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U claims_user claims_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U claims_user claims_db < backup.sql
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose exec backend pytest tests/integration/
```

## Troubleshooting

### OAuth Redirect Issues

Ensure redirect URIs match exactly in both:
- EHR provider registration
- `.env` configuration

### Database Connection Errors

Check PostgreSQL is running:
```bash
docker-compose ps
docker-compose logs postgres
```

### LLM Service Unavailable

Verify local LLM is running:
```bash
curl http://localhost:8001/health
```

## Support

For deployment assistance or issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment configuration
3. Review security group/firewall rules
4. Consult FHIR provider documentation

## License

Proprietary - Hospital Internal Use Only

## Contributors

Built for healthcare providers who deserve better tools.

---

**⚠️ HIPAA Notice:** This system processes Protected Health Information (PHI). Ensure proper security controls, access management, and audit logging are in place before production deployment.
