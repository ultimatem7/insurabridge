# Insurabridge - Running Instructions

## Quick Start Guide

This guide will help you set up and run Insurabridge on Windows.

---

## Prerequisites

Before starting, ensure you have the following installed:

1. **Python 3.11+** - Download from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
3. **Ollama** - Download from [ollama.ai](https://ollama.ai)
4. **16GB RAM** (recommended) - Minimum 8GB

---

## Step 1: Verify Ollama and Gemma 4B Model

Since you already have Gemma 4B installed, you can skip this step. However, if you need to verify or reinstall:

```powershell
# Check if Gemma 4B is installed
ollama list

# If not installed, pull it:
ollama pull gemma:4b
```

**Note:** This project uses Gemma 4B by default. The configuration is set to use `gemma:4b`.

---

## Step 2: Run Setup Script (Recommended)

The easiest way to set up Insurabridge is using the provided setup script:

```powershell
cd C:\Users\krish\OneDrive\Documents\Insurabridge\Insurabridge
.\scripts\setup.ps1
```

This script will:
- Check prerequisites
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies
- Install Epic FHIR Bridge dependencies

---

## Step 3: Manual Setup (Alternative)

If you prefer to set up manually or the script doesn't work:

### 3.1 Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3.2 Frontend Setup

```powershell
# Navigate to frontend directory (in a new terminal or after deactivating venv)
cd frontend

# Install dependencies
npm install
```

### 3.3 Epic FHIR Bridge Setup (Optional)

```powershell
# Navigate to epic-fhir-bridge directory
cd epic-fhir-bridge

# Install dependencies
npm install

# Copy environment file
copy env.example .env

# Edit .env file with your Epic credentials (if needed)
```

---

## Step 4: Start the Application

You need to run **three services** in separate terminal windows:

### Terminal 1: Start Ollama (if not already running)

```powershell
ollama serve
```

Keep this terminal open. Ollama should be running on `http://localhost:11434`

### Terminal 2: Start Backend

```powershell
# Navigate to backend directory
cd C:\Users\krish\OneDrive\Documents\Insurabridge\Insurabridge\backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start the server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

### Terminal 3: Start Frontend

```powershell
# Navigate to frontend directory
cd C:\Users\krish\OneDrive\Documents\Insurabridge\Insurabridge\frontend

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3001` (note: port 3001, not 3000)

---

## Step 5: Access the Application

Open your web browser and navigate to:

**http://localhost:3001**

---

## Configuration (Optional)

### Backend Environment Variables

Create a `.env` file in the `backend` directory if you need to customize settings:

```env
ENVIRONMENT=development
DEBUG=true
DB_ENCRYPTION_KEY=your-32-byte-encryption-key
SECRET_KEY=your-32-byte-secret-key
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma:4b
```

**Note:** The default model is `gemma:4b`. If you're using a different model, update `OLLAMA_MODEL` accordingly.

**Important:** For production, you MUST change the default encryption keys!

### Frontend Configuration

The frontend is configured to connect to the backend at `http://localhost:8000` by default. This is set in `frontend/src/lib/api.ts`.

---

## Troubleshooting

### Issue: "Python not found"
- Make sure Python 3.11+ is installed
- Add Python to your PATH during installation
- Restart your terminal after installing Python

### Issue: "Node not found"
- Make sure Node.js 18+ is installed
- Restart your terminal after installing Node.js

### Issue: "Ollama connection refused"
- Make sure Ollama is running: `ollama serve`
- Check that Ollama is accessible: `curl http://localhost:11434/api/tags`

### Issue: "Port already in use"
- Backend uses port 8000 - make sure nothing else is using it
- Frontend uses port 3001 - make sure nothing else is using it
- You can change ports in the start commands if needed

### Issue: "Module not found" errors
- Make sure you activated the virtual environment: `.\venv\Scripts\Activate.ps1`
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue: Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check `frontend/src/lib/api.ts` for the correct API URL
- Check browser console for CORS errors

---

## Stopping the Application

To stop the application:

1. **Terminal 1 (Ollama):** Press `Ctrl+C` (optional - Ollama can keep running)
2. **Terminal 2 (Backend):** Press `Ctrl+C`
3. **Terminal 3 (Frontend):** Press `Ctrl+C`

---

## Next Steps

Once the application is running:

1. **Explore the UI** at http://localhost:3001
2. **Check API docs** at http://localhost:8000/docs
3. **Upload a document** to test claim generation
4. **Review the architecture** in `ARCHITECTURE.md`

---

## Development Tips

- The backend runs with `--reload` flag, so it will automatically restart on code changes
- The frontend uses Next.js hot reload, so changes appear automatically
- Check the terminal output for any errors or warnings
- Backend logs are stored in `~/.insurabridge/logs/`
- Database is stored in `~/.insurabridge/data/sentinel.db`

---

## Need Help?

- Check the main `README.md` for more details
- Review `ARCHITECTURE.md` for system design
- Check `docs/` folder for detailed documentation

