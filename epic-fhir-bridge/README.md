# Insurabridge Epic FHIR Bridge

SMART-on-FHIR OAuth 2.0 gateway for Epic integration with full PKCE support. This service provides secure, authenticated access to Epic's FHIR R4 API for the Insurabridge healthcare insurance intelligence platform.

## Features

- ✅ **SMART-on-FHIR v2 Compliant** - Full OAuth 2.0 authorization code flow
- ✅ **PKCE Support** - Proof Key for Code Exchange for public clients (no client secret)
- ✅ **Epic App Orchard Ready** - Compatible with Epic's sandbox and production environments
- ✅ **Token Management** - Automatic token refresh with offline_access
- ✅ **FHIR R4 Client** - Type-safe access to Patient, Coverage, ExplanationOfBenefit, and more
- ✅ **Session Management** - Secure session-based token storage
- ✅ **Comprehensive Logging** - Structured logging with sensitive data redaction

## Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn
- Epic App Orchard account with registered application
- Epic Sandbox access (for testing)

## Quick Start

### 1. Install Dependencies

```bash
cd epic-fhir-bridge
npm install
```

### 2. Register Your App with Epic

1. Go to [Epic App Orchard](https://appmarket.epic.com/)
2. Create a developer account if you don't have one
3. Register a new application:
   - **Application Type**: Patient-facing app (Public Client)
   - **FHIR Version**: R4
   - **Redirect URI**: `http://localhost:3000/callback` (for development)
   - **Scopes**: Select the scopes you need (see Configuration below)
4. Note your **Client ID** (you won't have a client secret for public clients)

### 3. Configure Environment

Copy the example environment file and fill in your values:

```bash
cp env.example .env
```

Edit `.env`:

```env
# Server
PORT=3000
NODE_ENV=development
SESSION_SECRET=generate-a-random-32-char-string-here

# Epic OAuth - Get these from Epic App Orchard
EPIC_CLIENT_ID=your-client-id-from-epic
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_AUTH_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
REDIRECT_URI=http://localhost:3000/callback

# Scopes (space-separated)
FHIR_SCOPES=launch/patient patient/Patient.read patient/Coverage.read patient/ExplanationOfBenefit.read patient/Condition.read patient/Observation.read openid profile offline_access

# Logging
LOG_LEVEL=debug
```

### 4. Start the Server

Development mode (with hot reload):

```bash
npm run dev
```

Production mode:

```bash
npm run build
npm start
```

### 5. Test the Authorization Flow

1. Open your browser to: `http://localhost:3000/auth/authorize`
2. You'll be redirected to Epic's login page
3. Log in with an Epic sandbox test account
4. Select a test patient when prompted
5. Authorize the requested scopes
6. You'll be redirected back with your session authenticated

### 6. Access FHIR Data

Once authenticated, you can access FHIR resources:

```bash
# Get current patient
curl http://localhost:3000/fhir/patient -H "Cookie: insurabridge.sid=your-session-cookie"

# Get insurance coverage
curl http://localhost:3000/fhir/coverage

# Get explanation of benefits (claims)
curl http://localhost:3000/fhir/eob

# Get all conditions
curl http://localhost:3000/fhir/condition

# Get comprehensive insurance data
curl http://localhost:3000/fhir/insurance-data
```

## API Reference

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/authorize` | Initiates OAuth flow, redirects to Epic |
| GET | `/auth/callback` | OAuth callback handler (automatic) |
| GET | `/auth/success` | Success page with token info |
| GET | `/auth/status` | Check authentication status |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Clear session and tokens |

### FHIR Endpoints

All FHIR endpoints require authentication. Include your session cookie.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fhir/patient` | Get current patient from launch context |
| GET | `/fhir/patient/:id` | Get specific patient by ID |
| GET | `/fhir/coverage` | Get all coverage records |
| GET | `/fhir/coverage/active` | Get active coverages only |
| GET | `/fhir/coverage/:id` | Get specific coverage |
| GET | `/fhir/eob` | Get all Explanation of Benefits |
| GET | `/fhir/eob/:id` | Get specific EOB |
| GET | `/fhir/condition` | Get all conditions |
| GET | `/fhir/condition/active` | Get active conditions |
| GET | `/fhir/observation` | Get observations (optional: ?category=vital-signs) |
| GET | `/fhir/observation/vitals` | Get vital signs |
| GET | `/fhir/observation/labs` | Get lab results |
| GET | `/fhir/insurance-data` | Get comprehensive patient insurance data |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/` | API information |

## PKCE Implementation Details

This implementation follows [RFC 7636](https://tools.ietf.org/html/rfc7636) for Proof Key for Code Exchange:

1. **Code Verifier**: Random 64-character string using `A-Z`, `a-z`, `0-9`, `-`, `.`, `_`, `~`
2. **Code Challenge**: SHA256 hash of verifier, base64url encoded (S256 method)
3. **State Parameter**: Random 32-byte string for CSRF protection

The code verifier is stored server-side and never exposed to the client browser.

## Epic Sandbox Test Accounts

Epic provides test patient accounts for sandbox testing:

1. After authorizing, you'll see the Epic patient selection screen
2. Common test patients:
   - **Camila Lopez** - Adult with coverage
   - **Derrick Lin** - Adult with medications
   - **Theodore Crona** - Pediatric patient

See [Epic's FHIR Documentation](https://fhir.epic.com/) for the full list.

## Security Considerations

- **No Client Secret**: This is a public client implementation (PKCE-only)
- **Session Storage**: Tokens are stored in server-side sessions, never exposed to browser
- **HTTPS Required**: In production, always use HTTPS
- **Token Refresh**: Access tokens expire; use refresh tokens for long sessions
- **Scope Minimization**: Only request scopes you actually need

## Troubleshooting

### "Invalid or expired state parameter"

The authorization state expired (10 minutes) or was already used. Restart the flow.

### "Token exchange failed"

Common causes:
- Redirect URI mismatch (must exactly match Epic registration)
- Invalid client ID
- Authorization code already used
- Code verifier doesn't match challenge

### "No refresh token"

Ensure `offline_access` scope is requested and approved.

### CORS Errors

Update `CORS_ORIGINS` in `.env` to include your frontend URL.

## Project Structure

```
epic-fhir-bridge/
├── src/
│   ├── auth/
│   │   ├── index.ts       # Auth module exports
│   │   ├── pkce.ts        # PKCE implementation
│   │   └── oauth.ts       # OAuth flow handlers
│   ├── fhir/
│   │   ├── index.ts       # FHIR module exports
│   │   └── client.ts      # FHIR API client
│   ├── routes/
│   │   ├── index.ts       # Route exports
│   │   ├── auth.ts        # Auth endpoints
│   │   └── fhir.ts        # FHIR endpoints
│   ├── types/
│   │   └── index.ts       # TypeScript definitions
│   ├── config.ts          # Configuration loader
│   ├── logger.ts          # Winston logger
│   └── index.ts           # Main application
├── env.example            # Environment template
├── package.json
├── tsconfig.json
└── README.md
```

## Integration with Insurabridge Backend

The Epic FHIR Bridge can be integrated with the main Insurabridge Python backend:

1. **Direct Integration**: Call FHIR endpoints from Python using the session cookie
2. **Token Forwarding**: Pass tokens to Python backend for direct FHIR calls
3. **Webhook/Events**: Emit events when new FHIR data is received

Example Python integration:

```python
import requests

# After user completes OAuth flow in the Node bridge
session_cookie = "insurabridge.sid=..."

# Fetch insurance data
response = requests.get(
    "http://localhost:3000/fhir/insurance-data",
    cookies={"insurabridge.sid": session_cookie}
)
insurance_data = response.json()

# Process with Insurabridge evidence pipeline
```

## License

Proprietary - Insurabridge Inc.

