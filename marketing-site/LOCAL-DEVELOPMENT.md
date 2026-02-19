# Local Development Setup

This marketing site is configured for **local development only**. All links point to localhost.

---

## Port Configuration

The project uses these ports:

| Service | Port | URL |
|---------|------|-----|
| **Marketing Site** | 3002 | http://localhost:3002 |
| **Frontend App** | 3000 | http://localhost:3000 |
| **Backend API** | 8000 | http://localhost:8000 |

---

## Running Everything Together

### 1. Start Marketing Site

```bash
cd /Users/mingchuan/Desktop/insurabridge/marketing-site
npm run dev
```

**Access:** http://localhost:3002

### 2. Start Demo Backend

```bash
cd /Users/mingchuan/Desktop/insurabridge/Insurabridge/demo-backend
source venv/bin/activate
python main.py
```

**Access:** http://localhost:8000

### 3. Start Frontend App

```bash
cd /Users/mingchuan/Desktop/insurabridge/frontend
npm run dev
```

**Access:** http://localhost:3000

---

## What Links to What

### Marketing Site (port 3002)

- **Login button** → http://localhost:3000 (frontend app)
- **Book Demo** → Contact form (same site)
- **All other pages** → Same site navigation

### Frontend App (port 3000)

- Connects to backend at http://localhost:8000
- This is your actual application

---

## Testing the Flow

1. **Open marketing site:** http://localhost:3002
2. **Browse pages:** Home, How It Works, Security, Demo, Contact
3. **Click "Login":** Opens http://localhost:3000 (your app)
4. **Use the app:** Frontend communicates with backend

---

## Current Configuration

✅ All localhost URLs
✅ No production domain references
✅ Login button opens frontend app
✅ Backend API endpoints ready

---

## When You're Ready for Production

To deploy to actual domains later:

1. Update `.env.production`:
   ```env
   NEXT_PUBLIC_SITE_URL=https://insura.bridge
   NEXT_PUBLIC_APP_URL=https://app.insura.bridge
   NEXT_PUBLIC_API_URL=https://app.insura.bridge/api
   ```

2. The Header component already uses environment variables, so it will automatically use production URLs when deployed.

---

## Notes

- Marketing site is completely separate from the app
- Login button opens in new tab (doesn't navigate away)
- All services run independently
- No authentication needed for marketing site
- Contact form works locally (logs to console)

---

**Ready to go!** Just run the marketing site and click around. The "Login" button will open your frontend app when it's running.
