# Insurabridge - Healthcare Claims Automation Platform

**Production-Grade Web Application for EHR-Integrated Insurance Claim Generation**

---

## 🎯 What This Is

A **HIPAA-conscious web application** that automates insurance claim generation from EHR (Electronic Health Record) data. Designed for on-premise hospital deployment.

### Key Features

- ✅ **Multi-EHR Authentication** - OAuth2/SMART on FHIR (Epic, Cerner, etc.)
- ✅ **FHIR R4 Integration** - Extract patient, encounter, and clinical data
- ✅ **AI-Powered Claim Generation** - Local LLM processes clinical notes
- ✅ **Evidence-Based** - Every code linked to supporting documentation
- ✅ **HIPAA Compliant** - All PHI stays on-premise
- ✅ **Docker Deployment** - One-command setup

---

## 📁 Project Structure

```
insurabridge/
├── claim-web-app/              # Main web application
│   ├── backend/                # FastAPI backend
│   ├── frontend/               # React frontend (to be built)
│   ├── docker-compose.yml      # Service orchestration
│   └── README.md               # Detailed documentation
│
├── Insurabridge/demo-backend/  # Demo/testing backend
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- EHR provider credentials (Epic/Cerner) OR use mock mode

### Run the Application

```bash
cd claim-web-app
./quick-start.sh
```

This will:
- Start PostgreSQL database
- Start Redis (session storage)
- Start FastAPI backend
- Show you the API documentation URL

**Access Points:**
- API Documentation: http://localhost:8000/docs
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

---

## 📖 Full Documentation

Complete documentation is in the **claim-web-app/** folder:

- **claim-web-app/README.md** - Project overview
- **claim-web-app/DEPLOYMENT.md** - Complete deployment guide
- **claim-web-app/PROJECT_SUMMARY.md** - Technical deep-dive

---

## 🔧 Development Setup

```bash
cd claim-web-app

# Copy configuration
cp .env.example .env

# Edit with your settings
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## 🏥 How It Works

### 1. Authentication
User authenticates with their EHR system (Epic, Cerner, etc.) using OAuth2

### 2. Data Extraction
System fetches FHIR resources:
- Patient demographics
- Encounter details
- Conditions (diagnoses)
- Procedures
- Clinical notes
- Lab results

### 3. Claim Generation
Local LLM processes clinical data and generates:
- ICD-10 diagnosis codes
- CPT/HCPCS procedure codes
- Evidence citations
- Confidence scores

### 4. Review & Export
Claims are presented for human review before submission

---

## 🔒 Security & Compliance

### HIPAA Compliance
- ✅ All data processing on-premise
- ✅ Encrypted database connections
- ✅ Audit logging for all PHI access
- ✅ Session timeouts (15 minutes)
- ✅ No external API calls with PHI

### Security Features
- JWT token authentication
- OAuth2 with PKCE (for Epic)
- Password hashing (bcrypt)
- SQL injection prevention
- CORS configuration
- Security headers

---

## 📊 API Endpoints

### Authentication
- `GET /auth/providers` - List available EHR providers
- `GET /auth/{provider}/login` - Initiate OAuth flow
- `GET /auth/{provider}/callback` - OAuth callback
- `POST /auth/logout` - End session

### FHIR Resources
- `GET /fhir/patients` - Get current patient
- `GET /fhir/encounters` - List patient encounters
- `GET /fhir/encounters/{id}` - Get encounter details
- `GET /fhir/conditions` - List diagnoses
- `GET /fhir/procedures` - List procedures

### Claims
- `POST /claims/generate` - Generate claim from encounter
- `GET /claims/{id}` - Retrieve claim
- `GET /claims` - List claims
- `POST /claims/{id}/export` - Export claim

### Health
- `GET /health` - Basic health check
- `GET /health/ready` - Comprehensive readiness check

Full API documentation: http://localhost:8000/docs

---

## 🎓 Technology Stack

### Backend
- **Python 3.11** - Runtime
- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Database
- **Redis** - Session storage
- **HTTPX** - Async HTTP client

### EHR Integration
- **SMART on FHIR** - OAuth2 authentication
- **FHIR R4** - Healthcare data standard
- **Epic SDK** - Epic integration
- **Cerner SDK** - Cerner integration

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Service orchestration
- **Nginx** - Reverse proxy (production)

---

## 🧪 Testing

```bash
cd claim-web-app

# View API documentation (interactive testing)
open http://localhost:8000/docs

# Test health
curl http://localhost:8000/health

# List EHR providers
curl http://localhost:8000/auth/providers

# Check all systems
curl http://localhost:8000/health/ready
```

---

## 🚢 Production Deployment

### 1. Configure Environment

```bash
cd claim-web-app
cp .env.example .env
```

Edit `.env` with production values:
- Secure secrets
- Database credentials
- EHR provider OAuth credentials
- LLM service URL

### 2. Deploy with Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Configure SSL/TLS

Use nginx reverse proxy with Let's Encrypt certificates.

### 4. Set Up Monitoring

- Health checks: `/health/ready`
- Logs: `docker-compose logs -f`
- Metrics: Prometheus/Grafana (optional)

See **claim-web-app/DEPLOYMENT.md** for complete instructions.

---

## 🔧 Configuration

### Environment Variables

Key configuration in `.env`:

```env
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<your-secret-key>

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/claims_db

# Epic EHR
EPIC_CLIENT_ID=your_epic_client_id
EPIC_CLIENT_SECRET=your_epic_secret
EPIC_REDIRECT_URI=http://localhost:8000/auth/epic/callback

# Local LLM
LLM_SERVICE_URL=http://localhost:8001

# Security
SESSION_TIMEOUT_MINUTES=15
CORS_ORIGINS=http://localhost:3000
```

---

## 📈 Roadmap

### ✅ Completed (MVP)
- Multi-provider OAuth2 authentication
- FHIR R4 data extraction
- Claim generation pipeline
- Database models and persistence
- Security middleware
- Audit logging
- Docker deployment

### 🔄 In Progress
- React frontend UI
- CMS-1500 export format
- Claim editing workflow

### 📋 Planned
- Additional EHR providers (Athenahealth, Meditech, eClinicalWorks)
- X12 837 EDI generation
- Claim submission tracking
- Analytics dashboard
- User management UI
- Multi-payer policy database

---

## 🆘 Support & Troubleshooting

### Common Issues

**Services won't start:**
```bash
docker-compose logs -f backend
docker-compose restart
```

**Database connection failed:**
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U claims_user -d claims_db
```

**OAuth redirect not working:**
- Verify redirect URI matches exactly in EHR provider settings
- Check CORS_ORIGINS in .env

### Get Help

- Check API docs: http://localhost:8000/docs
- View logs: `docker-compose logs -f`
- Read: claim-web-app/DEPLOYMENT.md
- Review: claim-web-app/PROJECT_SUMMARY.md

---

## 📝 License

Proprietary - For authorized use only

---

## 🙏 Credits

Built for healthcare providers who deserve better tools.

Designed with HIPAA compliance and patient privacy as top priorities.

---

## 🔗 Quick Links

- **Main Application**: `/claim-web-app/`
- **API Documentation**: http://localhost:8000/docs
- **Deployment Guide**: `/claim-web-app/DEPLOYMENT.md`
- **Technical Summary**: `/claim-web-app/PROJECT_SUMMARY.md`

---

**To get started:** `cd claim-web-app && ./quick-start.sh`
