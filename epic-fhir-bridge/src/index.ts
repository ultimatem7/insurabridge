/**
 * Insurabridge Epic FHIR Bridge
 * SMART-on-FHIR OAuth 2.0 server with PKCE support
 * 
 * This service handles Epic authentication and provides
 * authenticated FHIR API access for the Insurabridge platform.
 */

import express from 'express';
import session from 'express-session';
import cors from 'cors';
import { config } from './config.js';
import { serverLogger } from './logger.js';
import { authRoutes, fhirRoutes } from './routes/index.js';

// Create Express app
const app = express();

// Import authStore from routes for cross-origin access
import { authStore } from './routes/auth.js';

// ============================================
// Middleware Configuration
// ============================================

// CORS - Allow frontend and backend to communicate
app.use(cors({
  origin: [
    'http://localhost:3001',  // Next.js frontend
    'http://localhost:3002',  // Next.js frontend (alternate port)
    'http://localhost:3000',  // Self
    'http://localhost:8000',  // Python backend
    ...config.corsOrigins,
  ],
  credentials: true,
}));

// JSON body parser
app.use(express.json());

// URL-encoded body parser
app.use(express.urlencoded({ extended: true }));

// Session configuration
app.use(session({
  secret: config.sessionSecret,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: false, // Allow non-HTTPS for development
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    sameSite: 'lax', // Works for same-origin and top-level navigations
  },
  name: 'insurabridge.sid',
}));

// Trust first proxy (needed for cookies behind reverse proxy)
app.set('trust proxy', 1);

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    serverLogger.debug(`${req.method} ${req.path}`, {
      status: res.statusCode,
      duration: `${duration}ms`,
    });
  });
  
  next();
});

// ============================================
// Routes
// ============================================

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'insurabridge-epic-fhir-bridge',
    timestamp: new Date().toISOString(),
  });
});

// Quick status check at root level (for frontend convenience)
app.get('/status', (req, res) => {
  // Check both session AND global authStore (for cross-origin support)
  const session = req.session as any;
  const isAuthenticatedSession = !!(session?.accessToken && session?.patientId);
  const isAuthenticatedStore = !!(authStore.accessToken && authStore.patientId);
  const isAuthenticated = isAuthenticatedSession || isAuthenticatedStore;
  
  // Disable caching so we always get fresh status
  res.set('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.set('Pragma', 'no-cache');
  res.set('Expires', '0');
  
  res.json({
    authenticated: isAuthenticated,
    patientId: session?.patientId || authStore.patientId || null,
    scope: session?.scope || authStore.scope || null,
    expiresAt: session?.expiresAt || authStore.expiresAt || null,
  });
});

// API info
app.get('/', (req, res) => {
  res.json({
    name: 'Insurabridge Epic FHIR Bridge',
    version: '1.0.0',
    description: 'SMART-on-FHIR OAuth 2.0 gateway for Epic integration',
    endpoints: {
      auth: {
        authorize: 'GET /auth/authorize - Start authorization flow',
        callback: 'GET /auth/callback - OAuth callback (handled automatically)',
        status: 'GET /auth/status - Check authentication status',
        refresh: 'POST /auth/refresh - Refresh access token',
        logout: 'POST /auth/logout - Clear session',
      },
      fhir: {
        patient: 'GET /fhir/patient - Get current patient',
        coverage: 'GET /fhir/coverage - Get insurance coverage',
        eob: 'GET /fhir/eob - Get explanation of benefits',
        conditions: 'GET /fhir/condition - Get conditions',
        observations: 'GET /fhir/observation - Get observations',
        insuranceData: 'GET /fhir/insurance-data - Get comprehensive insurance data',
      },
    },
    documentation: 'See README.md for setup and usage instructions',
  });
});

// Mount routers
app.use('/auth', authRoutes);
app.use('/fhir', fhirRoutes);

// IMPORTANT: Epic redirects to /callback directly, not /auth/callback
// Add a redirect to handle this
app.get('/callback', (req, res) => {
  // Forward the callback to the auth router with all query params
  const queryString = new URLSearchParams(req.query as Record<string, string>).toString();
  res.redirect(`/auth/callback?${queryString}`);
});

// Also handle root path as callback (simpler redirect URI option)
app.get('/', (req, res, next) => {
  // If this is an OAuth callback (has code or error param), handle it
  if (req.query['code'] || req.query['error']) {
    const queryString = new URLSearchParams(req.query as Record<string, string>).toString();
    return res.redirect(`/auth/callback?${queryString}`);
  }
  // Otherwise show the API info
  next();
});

// ============================================
// Error Handling
// ============================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'not_found',
    message: `Route ${req.method} ${req.path} not found`,
  });
});

// Global error handler
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  serverLogger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
  });
  
  res.status(500).json({
    error: 'internal_error',
    message: config.nodeEnv === 'development' ? err.message : 'An unexpected error occurred',
  });
});

// ============================================
// Server Startup
// ============================================

const server = app.listen(config.port, () => {
  serverLogger.info(`🚀 Insurabridge Epic FHIR Bridge started`, {
    port: config.port,
    environment: config.nodeEnv,
    fhirBaseUrl: config.epic.fhirBaseUrl,
  });
  
  serverLogger.info(`📋 Authorization URL: http://localhost:${config.port}/auth/authorize`);
  serverLogger.info(`📋 Callback URL: ${config.epic.redirectUri}`);
});

// Graceful shutdown
const shutdown = () => {
  serverLogger.info('Shutting down server...');
  server.close(() => {
    serverLogger.info('Server closed');
    process.exit(0);
  });
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

export default app;

