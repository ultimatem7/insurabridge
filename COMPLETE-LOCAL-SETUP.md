# Complete Local Development Setup - All Services

Run the entire Insurabridge stack locally. Everything stays on localhost - no production domains.

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────┐
│  Marketing Site (localhost:3002)        │
│  - Home, About, Demo, Contact           │
│  - "Login" button →                     │
└──────────────────┬──────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────┐
│  Frontend App (localhost:3000)          │
│  - Main application UI                  │
│  - Claim generation interface           │
│  - Connects to backend ↓                │
└──────────────────┬──────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────┐
│  Backend API (localhost:8000)           │
│  - FastAPI server                       │
│  - FHIR processing                      │
│  - Claim generation                     │
└─────────────────────────────────────────┘
```

---

## 🚀 Quick Start (All 3 Services)

### Terminal 1: Marketing Site

```bash
cd /Users/mingchuan/Desktop/insurabridge/marketing-site

# First time only
npm install

# Start dev server
npm run dev
```

✅ **Marketing at:** http://localhost:3002

---

### Terminal 2: Backend API

```bash
cd /Users/mingchuan/Desktop/insurabridge/Insurabridge/demo-backend

# First time only: create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# First time only: install dependencies
pip install fastapi uvicorn httpx pydantic

# Start backend
python main.py
```

✅ **API at:** http://localhost:8000
✅ **API Docs:** http://localhost:8000/docs

---

### Terminal 3: Frontend App

```bash
cd /Users/mingchuan/Desktop/insurabridge/frontend

# First time only
npm install

# Start dev server
npm run dev
```

✅ **App at:** http://localhost:3000

---

## 📋 Service Status Checklist

After starting all services, verify:

- [ ] Marketing site loads at http://localhost:3002
- [ ] Backend API responds at http://localhost:8000/docs
- [ ] Frontend app loads at http://localhost:3000
- [ ] No port conflicts (3002, 3000, 8000 all available)

---

## 🔗 How They Connect

### Marketing Site (3002)
- **Standalone** - works independently
- **Login button** → Opens http://localhost:3000 in new tab
- **Book Demo** → Contact form on same site
- **All pages** → Static content, no backend needed

### Frontend App (3000)
- **Connected to Backend** → Makes API calls to http://localhost:8000
- **Independent from Marketing** → Different port, different purpose
- **Full application** → Claim generation, FHIR processing

### Backend API (8000)
- **Serves Frontend** → Responds to API requests from port 3000
- **No connection to Marketing** → Marketing is static

---

## 🧪 Testing the Complete Flow

### 1. Browse Marketing Site
```
Open: http://localhost:3002
Click through: Home → How It Works → Security → Demo → Contact
```

### 2. Try Login Flow
```
On marketing site, click "Login" button
→ Opens http://localhost:3000 (frontend app)
```

### 3. Test Backend Connection
```
Open: http://localhost:8000/docs
Try API endpoints
```

### 4. Use Frontend App
```
Go to: http://localhost:3000
App communicates with backend at port 8000
```

---

## 🛠️ Troubleshooting

### Port Already in Use

**Marketing Site (3002):**
```bash
# Kill process
lsof -ti:3002 | xargs kill -9

# Or use different port
npm run dev -- -p 3003
```

**Frontend (3000):**
```bash
# Kill process
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

**Backend (8000):**
```bash
# Kill process
lsof -ti:8000 | xargs kill -9

# Or edit main.py to use port 8001
```

---

### Service Won't Start

**Marketing Site:**
```bash
cd marketing-site
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Backend:**
```bash
cd Insurabridge/demo-backend
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx pydantic
python main.py
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

### Services Can't Connect

**Check URLs:**
- Marketing: Uses localhost:3000 for Login button
- Frontend: Check `src/lib/api.ts` → should point to `http://localhost:8000`
- Backend: CORS should allow `http://localhost:3000`

**Check Backend CORS:**
In `main.py`, verify:
```python
allow_origins=["http://localhost:3000", "http://localhost:3001", "*"]
```

---

## 📊 Service Summary

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| Marketing | 3002 | ✅ Ready | Public-facing info site |
| Frontend | 3000 | ✅ Ready | Main application |
| Backend | 8000 | ✅ Ready | API server |

---

## 🎯 What to Run First

**Recommended order:**

1. **Just Marketing** → Run only marketing site to see static pages
2. **Backend + Frontend** → Run backend and frontend to test the app
3. **All Three** → Run everything to see complete flow

**Minimal for demo:**
- Marketing site only (no backend needed)

**Full application:**
- Backend + Frontend (marketing optional)

**Complete experience:**
- All three services

---

## 🔄 Stopping All Services

Press `Ctrl+C` in each terminal to stop services.

Or kill all at once:
```bash
# Kill all node processes
pkill -f "node.*dev"

# Kill Python process
pkill -f "python main.py"
```

---

## 📝 Environment Variables

### Marketing Site (.env.local)
```env
NEXT_PUBLIC_SITE_URL=http://localhost:3002
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (if using .env)
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma:4b
```

---

## 🚦 Current Status

✅ **All services configured for localhost**
✅ **No production domain references**
✅ **Login button → localhost:3000**
✅ **Ready for local development**

---

## 📚 Additional Documentation

- **Marketing Site:** `/marketing-site/README.md`
- **Local Dev:** `/marketing-site/LOCAL-DEVELOPMENT.md`
- **Original Instructions:** `/RUN_INSTRUCTIONS.md`
- **Complete Guide:** `/HOW-TO-RUN-EVERYTHING.md`

---

**Everything runs locally. No external dependencies. Simple and clean!** 🎉
