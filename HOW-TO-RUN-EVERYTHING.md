# How to Run Insurabridge - Complete Guide

You have **3 different applications** in this project. Here's how to run each one:

---

## 🎯 Quick Decision Guide

**What do you want to run?**

1. **Marketing Website** (new) → See [Option 1](#option-1-marketing-website-new) ⭐ **START HERE**
2. **Original Demo App** (frontend + demo backend) → See [Option 2](#option-2-original-demo-application)
3. **Production Web App** (claim-web-app) → See [Option 3](#option-3-production-web-app)

---

## Option 1: Marketing Website (NEW) ⭐

**What it is:** Public-facing marketing site at root domain
**Best for:** Showcasing product to potential customers
**Location:** `/marketing-site/`

### Run It

```bash
cd /Users/mingchuan/Desktop/insurabridge/marketing-site

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Access at:** http://localhost:3002

**Pages:**
- Home (hero, features)
- How It Works
- Security
- Demo
- Contact (with form)
- Privacy & Terms

**Status:** ✅ Production-ready, fully built

---

## Option 2: Original Demo Application

**What it is:** Full demo with frontend + FastAPI backend
**Best for:** Testing the FHIR-to-claim pipeline
**Location:** `/frontend/` + `/Insurabridge/demo-backend/`

### Step 1: Start Demo Backend

```bash
cd /Users/mingchuan/Desktop/insurabridge/Insurabridge/demo-backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (first time only)
pip install fastapi uvicorn httpx pydantic

# Run the backend
python main.py
```

**Backend runs at:** http://localhost:8000

### Step 2: Start Frontend

Open a **new terminal**:

```bash
cd /Users/mingchuan/Desktop/insurabridge/frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend runs at:** http://localhost:3000

### Using the Demo

1. Go to http://localhost:3000
2. The frontend connects to the backend at http://localhost:8000
3. Test the claim generation features

---

## Option 3: Production Web App

**What it is:** Full production app with PostgreSQL, Redis
**Best for:** Production deployment with all EHR integrations
**Location:** `/claim-web-app/`

### Prerequisites

- Docker and Docker Compose installed
- PostgreSQL running
- Redis running
- Local LLM service (Ollama)

### Run It

```bash
cd /Users/mingchuan/Desktop/insurabridge/claim-web-app

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start with Docker
docker-compose up -d

# Or run backend directly
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Backend runs at:** http://localhost:8000

---

## 🆘 Troubleshooting

### Backend Won't Start

**Error: "No module named 'fastapi'"**

```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# OR for demo backend:
pip install fastapi uvicorn httpx pydantic
```

### Frontend Won't Start

**Error: "Cannot find module"**

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Port Already in Use

**Backend (8000):**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --reload --port 8001
```

**Frontend (3000):**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

---

## 📋 Summary

| Application | Location | Ports | Status |
|------------|----------|-------|--------|
| **Marketing Site** | `/marketing-site/` | 3002 | ✅ Ready |
| **Demo Backend** | `/Insurabridge/demo-backend/` | 8000 | ✅ Ready |
| **Demo Frontend** | `/frontend/` | 3000 | ✅ Ready |
| **Production App** | `/claim-web-app/` | 8000 | ⚙️ Needs config |

---

## 🎯 Recommended: Run Marketing Site First

If you're new to this project, **start with the marketing website**:

```bash
cd marketing-site
npm install
npm run dev
```

Visit http://localhost:3002 to see the complete marketing site with all pages working.

---

## 📚 More Documentation

- **Marketing Site:** See `/marketing-site/README.md`
- **Original Demo:** See `/RUN_INSTRUCTIONS.md`
- **Production App:** See `/claim-web-app/DEPLOYMENT.md`

---

## ⚡ Quick Start Scripts

### All-in-One Demo (Backend + Frontend)

Create this script: `start-demo.sh`

```bash
#!/bin/bash

# Start backend in background
cd /Users/mingchuan/Desktop/insurabridge/Insurabridge/demo-backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
cd /Users/mingchuan/Desktop/insurabridge/frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

Make it executable:
```bash
chmod +x start-demo.sh
./start-demo.sh
```

---

**Need help? Check the README files in each directory!** 📖
