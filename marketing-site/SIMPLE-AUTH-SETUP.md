# Simple Authentication Setup (JSON Database)

This uses a **simple JSON file** for the database instead of SQLite. No compilation needed!

---

## ✅ Setup (3 Commands)

```bash
cd /Users/mingchuan/Desktop/insurabridge/marketing-site

# 1. Install dependencies (simpler now!)
npm install

# 2. Initialize database
npm run init-db

# 3. Start the server
npm run dev
```

---

## 🎯 Test Login

1. Go to **http://localhost:3002**
2. Click **"Login"** in header
3. Enter:
   - **Email:** `demo@insura.bridge`
   - **Password:** `demo1234`
4. Click "Sign In"
5. **Redirects to:** http://localhost:3000 (your product app)

---

## 📁 Database Location

The database is stored as a simple JSON file:

**Location:** `marketing-site/data/users.json`

You can open it and see the users:

```bash
cat data/users.json
```

Example:
```json
{
  "users": [
    {
      "id": 1,
      "email": "demo@insura.bridge",
      "password": "$2a$10$...",
      "name": "Demo User",
      "created_at": "2024-02-17T10:30:00.000Z",
      "last_login": "2024-02-17T10:35:00.000Z"
    }
  ],
  "nextId": 2
}
```

---

## 🆕 Create New User

### Via Registration Page

1. Go to http://localhost:3002/register
2. Fill in form
3. Submit
4. Redirects to product app

### Manually Add to JSON

Edit `data/users.json`:

```json
{
  "users": [
    {
      "id": 2,
      "email": "newuser@example.com",
      "password": "$2a$10$yourhashedpassword",
      "name": "New User",
      "created_at": "2024-02-17T10:30:00.000Z",
      "last_login": null
    }
  ],
  "nextId": 3
}
```

---

## 🔍 View All Users

```bash
# Pretty print JSON
cat data/users.json | python -m json.tool

# Count users
cat data/users.json | grep -c "email"
```

---

## 🗑️ Reset Database

```bash
# Delete database
rm data/users.json

# Reinitialize
npm run init-db
```

---

## ✨ Benefits of JSON Database

✅ **No compilation** - Works on any system
✅ **Easy to read** - Just open the JSON file
✅ **Easy to edit** - Modify directly if needed
✅ **Simple backup** - Just copy the JSON file
✅ **Portable** - Works everywhere Node.js runs

---

## 🔒 Security

- ✅ Passwords are hashed with bcrypt
- ✅ JWT tokens for sessions
- ✅ HttpOnly cookies
- ✅ 7-day token expiry

---

## 📊 What's Different?

**Before (SQLite):**
- Required native compilation
- Could fail on some systems
- Needed better-sqlite3 package

**Now (JSON):**
- Pure JavaScript
- Works everywhere
- No extra dependencies

---

## 🚀 Production Notes

For production with many users, consider:
- PostgreSQL (external database)
- MongoDB
- Supabase (managed database)

But for development and small deployments, JSON works great!

---

## 🔧 Troubleshooting

### Can't create users

Check file permissions:
```bash
ls -la data/
```

### Database corrupted

Reset it:
```bash
rm data/users.json
npm run init-db
```

### Module errors

Reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

---

**Much simpler! No compilation issues.** 🎉
