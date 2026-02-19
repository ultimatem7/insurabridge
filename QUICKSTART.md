# Quick Start - Insurabridge Web Application

## 🚀 Run the Application (3 Steps)

### Step 1: Navigate to Web App

```bash
cd /Users/mingchuan/Desktop/insurabridge/claim-web-app
```

### Step 2: Run Quick Start Script

```bash
./quick-start.sh
```

This automatically:
- Starts PostgreSQL database
- Starts Redis session storage
- Starts FastAPI backend
- Shows you the access URLs

### Step 3: Access the Application

Open in your browser:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## ✅ That's It!

You now have a running web application backend with:
- ✅ Multi-EHR authentication system
- ✅ FHIR R4 integration
- ✅ Claim generation pipeline
- ✅ Complete REST API

---

## 📖 Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Test endpoints**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/auth/providers
   ```
3. **Configure EHR credentials** in `claim-web-app/.env`
4. **Build React frontend** (see claim-web-app/DEPLOYMENT.md)

---

## 🛑 Stop the Application

```bash
cd /Users/mingchuan/Desktop/insurabridge/claim-web-app
docker-compose down
```

---

## 📚 Documentation

All documentation is in the **claim-web-app/** folder:

- `claim-web-app/README.md` - Project overview
- `claim-web-app/DEPLOYMENT.md` - Complete guide
- `claim-web-app/PROJECT_SUMMARY.md` - Technical details

---

## 🐛 Troubleshooting

**Docker not running?**
```bash
open -a Docker
```

**Need to see logs?**
```bash
cd claim-web-app
docker-compose logs -f backend
```

**Want to restart?**
```bash
cd claim-web-app
docker-compose restart
```

---

**Questions?** Check the full documentation in `claim-web-app/DEPLOYMENT.md`
