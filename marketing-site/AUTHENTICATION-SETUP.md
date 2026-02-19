# Authentication Setup Guide

The marketing site now has a complete authentication system with login, registration, and session management.

---

## Features

✅ **User Registration** - Create new accounts
✅ **User Login** - Sign in with email/password
✅ **Password Hashing** - Secure bcrypt hashing
✅ **JWT Tokens** - Session management with cookies
✅ **Redirect to Product** - After login, users go to localhost:3000
✅ **SQLite Database** - Simple file-based database

---

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Users/mingchuan/Desktop/insurabridge/marketing-site

# Install new authentication dependencies
npm install
```

### 2. Initialize Database

```bash
# Create database and add demo user
npm run init-db
```

This creates:
- Database file at `data/users.db`
- Demo user: `demo@insura.bridge` / `demo1234`

### 3. Start the Server

```bash
npm run dev
```

---

## How to Use

### Login

1. Go to http://localhost:3002
2. Click "Login" in the header
3. Use demo credentials:
   - **Email:** demo@insura.bridge
   - **Password:** demo1234
4. Click "Sign In"
5. **Redirects to:** http://localhost:3000 (your product app)

### Register New User

1. Go to http://localhost:3002/register
2. Fill in:
   - Full Name
   - Email
   - Password (min 8 characters)
   - Confirm Password
3. Click "Create Account"
4. **Redirects to:** http://localhost:3000 (your product app)

---

## API Endpoints

### POST /api/auth/register
Create new user account
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

### POST /api/auth/login
Authenticate user
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

### POST /api/auth/logout
Log out current user

### GET /api/auth/me
Get current authenticated user

---

## Database Structure

### users table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,  -- bcrypt hashed
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_login DATETIME
)
```

### sessions table
```sql
CREATE TABLE sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
)
```

---

## Security Features

✅ **Password Hashing** - bcrypt with salt rounds
✅ **JWT Tokens** - Signed with secret key
✅ **HttpOnly Cookies** - Prevents XSS attacks
✅ **7-day Expiry** - Tokens expire after 1 week
✅ **Email Validation** - Regex pattern matching
✅ **Password Length** - Minimum 8 characters

---

## File Structure

```
marketing-site/
├── data/
│   └── users.db              # SQLite database (auto-created)
├── src/
│   ├── lib/
│   │   ├── db.ts            # Database connection
│   │   ├── auth.ts          # Authentication functions
│   │   └── init-db.ts       # Database initialization script
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx     # Login page
│   │   ├── register/
│   │   │   └── page.tsx     # Registration page
│   │   └── api/
│   │       └── auth/
│   │           ├── login/route.ts
│   │           ├── register/route.ts
│   │           ├── logout/route.ts
│   │           └── me/route.ts
│   └── components/
│       └── Header.tsx        # Updated with Login link
```

---

## Testing

### Test Demo Login

```bash
# 1. Start marketing site
npm run dev

# 2. Open browser
open http://localhost:3002

# 3. Click "Login"

# 4. Enter credentials:
#    Email: demo@insura.bridge
#    Password: demo1234

# 5. Should redirect to localhost:3000
```

### Test Registration

```bash
# 1. Go to http://localhost:3002/register

# 2. Fill form:
#    Name: Test User
#    Email: test@example.com
#    Password: test1234
#    Confirm: test1234

# 3. Submit

# 4. Should redirect to localhost:3000
```

---

## Environment Variables

Add to `.env.local`:

```env
# JWT Secret (change in production!)
JWT_SECRET=insurabridge-secret-key-change-in-production

# Product app URL (where to redirect after login)
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Customization

### Change Redirect URL

Edit `.env.local`:
```env
NEXT_PUBLIC_APP_URL=http://localhost:3001
```

### Change Token Expiry

Edit `src/lib/auth.ts`:
```typescript
.setExpirationTime('7d')  // Change to '1d', '30d', etc.
```

### Add More User Fields

1. Update database schema in `src/lib/db.ts`
2. Update User interface in `src/lib/auth.ts`
3. Update registration form in `src/app/register/page.tsx`

---

## Adding Users Manually

You can add users programmatically:

```typescript
import { createUser } from '@/lib/auth'

// Create user
await createUser(
  'newuser@example.com',
  'password123',
  'New User'
)
```

Or use SQL directly:

```bash
# Access database
sqlite3 data/users.db

# View users
SELECT * FROM users;

# Check password hashes
SELECT email, password FROM users;
```

---

## Troubleshooting

### "Database locked" error

SQLite can only handle one write at a time. This is normal for concurrent requests. The app will retry.

### "Module not found" errors

```bash
rm -rf node_modules package-lock.json
npm install
```

### Demo user doesn't work

```bash
# Reinitialize database
npm run init-db
```

### Can't redirect to localhost:3000

Make sure your frontend app is running:
```bash
cd ../frontend
npm run dev
```

---

## Security Best Practices (Production)

Before deploying to production:

1. **Change JWT Secret**
   ```env
   JWT_SECRET=your-very-long-random-secret-key
   ```

2. **Use HTTPS**
   - Set `secure: true` in cookie options
   - Only works with HTTPS

3. **Use PostgreSQL**
   - SQLite is great for development
   - Use PostgreSQL for production

4. **Add Rate Limiting**
   - Prevent brute force attacks
   - Limit login attempts

5. **Add Email Verification**
   - Send confirmation emails
   - Verify email before activating account

6. **Add Password Reset**
   - Email-based password reset
   - Temporary reset tokens

---

## Next Steps

1. ✅ Users can register
2. ✅ Users can login
3. ✅ Login redirects to product app
4. 🔄 Make product app check auth status
5. 🔄 Add logout functionality to product app
6. 🔄 Add "My Account" page

---

**Authentication is ready!** Users can now create accounts and log in from the marketing site. 🎉
