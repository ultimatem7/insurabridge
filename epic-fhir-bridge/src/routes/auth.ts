/**
 * OAuth Authentication Routes
 * Handles SMART-on-FHIR authorization flow with PKCE
 */

import { Router, Request, Response, NextFunction } from 'express';
import {
  initiateAuthorization,
  validateCallback,
  exchangeCodeForTokens,
  clearAuthState,
  refreshAccessToken,
  isTokenExpired,
} from '../auth/index.js';
import { authLogger } from '../logger.js';

// Global auth store for cross-origin access (development only)
export const authStore: {
  accessToken?: string;
  refreshToken?: string;
  patientId?: string;
  expiresAt?: Date;
  scope?: string;
} = {};

const router = Router();

/**
 * GET /auth/authorize
 * Initiates the SMART-on-FHIR authorization flow
 * Redirects user to Epic's authorization endpoint
 */
router.get('/authorize', (req: Request, res: Response) => {
  try {
    // Optional: where to redirect after successful auth
    const returnTo = req.query['returnTo'] as string | undefined;
    
    // Generate PKCE params and authorization URL
    const { authorizationUrl, state } = initiateAuthorization(returnTo);
    
    // Store state in session for verification
    req.session.authState = {
      state,
      codeVerifier: '', // Will be set by initiateAuthorization internally
      createdAt: Date.now(),
      returnTo,
    };
    
    authLogger.info('Redirecting to Epic authorization', {
      state: state.substring(0, 8) + '...',
    });
    
    // Log full authorization URL for debugging
    authLogger.info('FULL AUTHORIZATION URL:', { url: authorizationUrl });
    
    res.redirect(authorizationUrl);
  } catch (error) {
    authLogger.error('Failed to initiate authorization', { error });
    res.status(500).json({
      error: 'authorization_failed',
      message: 'Failed to initiate authorization flow',
    });
  }
});

/**
 * GET /auth/callback
 * Handles OAuth callback from Epic
 * Exchanges authorization code for tokens
 */
router.get('/callback', async (req: Request, res: Response) => {
  try {
    const code = req.query['code'] as string | undefined;
    const state = req.query['state'] as string | undefined;
    const error = req.query['error'] as string | undefined;
    const errorDescription = req.query['error_description'] as string | undefined;
    
    // Validate callback parameters
    const validationResult = validateCallback(code, state, error, errorDescription);
    
    if (!validationResult.valid) {
      authLogger.warn('Callback validation failed', { 
        error: validationResult.error.code 
      });
      
      return res.status(400).json({
        error: validationResult.error.code,
        message: validationResult.error.message,
        description: validationResult.error.description,
      });
    }
    
    const { code: authCode, authState } = validationResult;
    
    // Exchange code for tokens
    const tokenSet = await exchangeCodeForTokens(authCode, authState.codeVerifier);
    
    // Clear the used authorization state
    clearAuthState(authState.state);
    
    // Store tokens in session
    req.session.tokens = tokenSet;
    
    // Also store in global authStore for cross-origin access
    authStore.accessToken = tokenSet.accessToken;
    authStore.refreshToken = tokenSet.refreshToken;
    authStore.patientId = tokenSet.patientId;
    authStore.expiresAt = new Date(tokenSet.expiresAt);
    authStore.scope = tokenSet.scope;
    
    authLogger.info('Authorization successful', {
      patientId: tokenSet.patientId,
      hasRefreshToken: !!tokenSet.refreshToken,
    });
    
    // Redirect back to frontend with success message
    // If returnTo is provided, use it; otherwise redirect to frontend pipeline page
    const frontendUrl = process.env['FRONTEND_URL'] || 'http://localhost:3001';
    const redirectUrl = authState.returnTo || `${frontendUrl}/pipeline?auth=success`;
    res.redirect(redirectUrl);
    
  } catch (error) {
    authLogger.error('Callback processing failed', { 
      error: error instanceof Error ? error.message : 'Unknown error' 
    });
    
    res.status(500).json({
      error: 'token_exchange_failed',
      message: error instanceof Error ? error.message : 'Failed to exchange authorization code',
    });
  }
});

/**
 * GET /auth/success
 * Success page after authorization
 * Returns token info (without sensitive data)
 */
router.get('/success', (req: Request, res: Response) => {
  const tokens = req.session.tokens;
  
  if (!tokens) {
    return res.status(401).json({
      error: 'not_authenticated',
      message: 'No active session. Please authorize first.',
    });
  }
  
  res.json({
    message: 'Authorization successful!',
    patientId: tokens.patientId,
    scope: tokens.scope,
    expiresAt: new Date(tokens.expiresAt).toISOString(),
    hasRefreshToken: !!tokens.refreshToken,
  });
});

/**
 * POST /auth/refresh
 * Refreshes the access token using the refresh token
 */
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const tokens = req.session.tokens;
    
    if (!tokens) {
      return res.status(401).json({
        error: 'not_authenticated',
        message: 'No active session',
      });
    }
    
    if (!tokens.refreshToken) {
      return res.status(400).json({
        error: 'no_refresh_token',
        message: 'No refresh token available. Re-authorization required.',
      });
    }
    
    const newTokenSet = await refreshAccessToken(tokens.refreshToken);
    req.session.tokens = newTokenSet;
    
    res.json({
      message: 'Token refreshed successfully',
      patientId: newTokenSet.patientId,
      expiresAt: new Date(newTokenSet.expiresAt).toISOString(),
    });
    
  } catch (error) {
    authLogger.error('Token refresh failed', { 
      error: error instanceof Error ? error.message : 'Unknown error' 
    });
    
    res.status(500).json({
      error: 'refresh_failed',
      message: error instanceof Error ? error.message : 'Failed to refresh token',
    });
  }
});

/**
 * GET /auth/status
 * Returns current authentication status
 */
router.get('/status', (req: Request, res: Response) => {
  const tokens = req.session.tokens;
  
  if (!tokens) {
    return res.json({
      authenticated: false,
    });
  }
  
  const expired = isTokenExpired(tokens);
  const canRefresh = !!tokens.refreshToken;
  
  res.json({
    authenticated: !expired || canRefresh,
    patientId: tokens.patientId,
    scope: tokens.scope,
    tokenExpired: expired,
    expiresAt: new Date(tokens.expiresAt).toISOString(),
    canRefresh,
  });
});

/**
 * POST /auth/logout
 * Clears the session and tokens
 */
router.post('/logout', (req: Request, res: Response) => {
  req.session.destroy((err) => {
    if (err) {
      authLogger.error('Logout failed', { error: err });
      return res.status(500).json({
        error: 'logout_failed',
        message: 'Failed to clear session',
      });
    }
    
    res.json({
      message: 'Logged out successfully',
    });
  });
});

/**
 * GET /auth/test-url
 * Generates a test authorization URL without PKCE for debugging
 */
router.get('/test-url', (req: Request, res: Response) => {
  const clientId = process.env['EPIC_CLIENT_ID'] || '';
  const redirectUri = process.env['REDIRECT_URI'] || '';
  const fhirBaseUrl = process.env['EPIC_FHIR_BASE_URL'] || '';
  const authUrl = process.env['EPIC_AUTH_URL'] || '';
  const scopes = process.env['FHIR_SCOPES'] || '';
  
  // Build a simple authorization URL WITHOUT PKCE for testing
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: clientId,
    redirect_uri: redirectUri,
    scope: scopes,
    state: 'test-state-123',
    aud: fhirBaseUrl,
  });
  
  const testUrl = `${authUrl}?${params.toString()}`;
  
  res.json({
    message: 'Test Authorization URL (without PKCE)',
    instructions: 'Copy this URL and paste it in your browser to test Epic directly',
    testUrl,
    note: 'If this URL also fails, the issue is with your Epic app configuration',
  });
});

/**
 * GET /auth/debug
 * Shows current OAuth configuration for debugging
 */
router.get('/debug', (req: Request, res: Response) => {
  // Import config here to avoid circular dependency issues
  const epicConfig = {
    clientId: process.env['EPIC_CLIENT_ID'] || 'NOT SET',
    fhirBaseUrl: process.env['EPIC_FHIR_BASE_URL'] || 'NOT SET',
    authUrl: process.env['EPIC_AUTH_URL'] || 'NOT SET',
    tokenUrl: process.env['EPIC_TOKEN_URL'] || 'NOT SET',
    redirectUri: process.env['REDIRECT_URI'] || 'NOT SET',
    scopes: process.env['FHIR_SCOPES'] || 'NOT SET',
  };
  
  // Mask client ID for security (show first 8 chars)
  const maskedClientId = epicConfig.clientId.length > 8 
    ? epicConfig.clientId.substring(0, 8) + '...' 
    : epicConfig.clientId;
  
  res.json({
    message: 'Epic OAuth Configuration',
    config: {
      clientId: maskedClientId,
      clientIdLength: epicConfig.clientId.length,
      fhirBaseUrl: epicConfig.fhirBaseUrl,
      authUrl: epicConfig.authUrl,
      tokenUrl: epicConfig.tokenUrl,
      redirectUri: epicConfig.redirectUri,
      scopes: epicConfig.scopes,
    },
    instructions: {
      step1: 'Ensure EPIC_CLIENT_ID is a valid Epic client ID',
      step2: 'For testing, use Epic Open Sandbox client: 6c12dff4-24e7-4475-a742-b08972c4ea27',
      step3: 'Redirect URI must exactly match what is registered in Epic',
      step4: 'Visit /auth/authorize to start the OAuth flow',
    },
    epicSandboxNote: 'Epic Open Sandbox: https://fhir.epic.com/ - Use "Try the API" to get a working client ID',
  });
});

export default router;

