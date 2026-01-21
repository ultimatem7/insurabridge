/**
 * OAuth 2.0 Authorization Flow for SMART-on-FHIR
 * Implements the authorization code flow with PKCE for Epic integration
 */

import axios, { AxiosError } from 'axios';
import { config } from '../config.js';
import { authLogger } from '../logger.js';
import { generatePKCEParams, generateState } from './pkce.js';
import type {
  AuthorizationState,
  TokenResponse,
  TokenSet,
  OAuthError,
  AuthorizationError,
} from '../types/index.js';

// In-memory store for authorization states (use Redis in production)
const authStates = new Map<string, AuthorizationState>();

// State expiration time (10 minutes)
const STATE_TTL_MS = 10 * 60 * 1000;

/**
 * Cleans up expired authorization states
 */
function cleanupExpiredStates(): void {
  const now = Date.now();
  for (const [state, data] of authStates.entries()) {
    if (now - data.createdAt > STATE_TTL_MS) {
      authStates.delete(state);
      authLogger.debug('Cleaned up expired state', { state: state.substring(0, 8) });
    }
  }
}

// Cleanup every 5 minutes
setInterval(cleanupExpiredStates, 5 * 60 * 1000);

/**
 * Initiates the authorization flow by generating PKCE params and building the auth URL
 * @returns Object containing the authorization URL and state for tracking
 */
export function initiateAuthorization(returnTo?: string): {
  authorizationUrl: string;
  state: string;
} {
  // Generate PKCE parameters
  const { codeVerifier, codeChallenge, codeChallengeMethod } = generatePKCEParams();
  
  // Generate state for CSRF protection
  const state = generateState();
  
  // Store state with code_verifier for later token exchange
  const authState: AuthorizationState = {
    state,
    codeVerifier,
    createdAt: Date.now(),
    returnTo,
  };
  authStates.set(state, authState);
  
  // Build authorization URL
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: config.epic.clientId,
    redirect_uri: config.epic.redirectUri,
    scope: config.epic.scopes,
    state,
    aud: config.epic.fhirBaseUrl,
    code_challenge: codeChallenge,
    code_challenge_method: codeChallengeMethod,
  });
  
  const authorizationUrl = `${config.epic.authUrl}?${params.toString()}`;
  
  authLogger.info('Initiated authorization flow', {
    state: state.substring(0, 8) + '...',
    scopes: config.epic.scopes,
    redirectUri: config.epic.redirectUri,
  });
  
  return { authorizationUrl, state };
}

/**
 * Retrieves stored authorization state by state parameter
 */
export function getAuthState(state: string): AuthorizationState | undefined {
  return authStates.get(state);
}

/**
 * Removes authorization state after use
 */
export function clearAuthState(state: string): void {
  authStates.delete(state);
}

/**
 * Validates the callback parameters from Epic's authorization response
 */
export function validateCallback(
  code: string | undefined,
  state: string | undefined,
  error: string | undefined,
  errorDescription: string | undefined
): { valid: true; code: string; authState: AuthorizationState } | { valid: false; error: AuthorizationError } {
  // Check for OAuth error response
  if (error) {
    authLogger.warn('OAuth error in callback', { error, errorDescription });
    const authError = {
      name: 'AuthorizationError',
      message: errorDescription || error,
      code: error,
      description: errorDescription,
    } as AuthorizationError;
    return { valid: false, error: authError };
  }
  
  // Validate required parameters
  if (!code) {
    const authError = {
      name: 'AuthorizationError',
      message: 'Missing authorization code in callback',
      code: 'missing_code',
    } as AuthorizationError;
    return { valid: false, error: authError };
  }
  
  if (!state) {
    const authError = {
      name: 'AuthorizationError',
      message: 'Missing state parameter in callback',
      code: 'missing_state',
    } as AuthorizationError;
    return { valid: false, error: authError };
  }
  
  // Validate state matches stored state (CSRF protection)
  const authState = authStates.get(state);
  if (!authState) {
    authLogger.warn('Invalid or expired state in callback', { 
      state: state.substring(0, 8) + '...' 
    });
    const authError = {
      name: 'AuthorizationError',
      message: 'Invalid or expired state parameter',
      code: 'invalid_state',
    } as AuthorizationError;
    return { valid: false, error: authError };
  }
  
  // Check if state has expired
  if (Date.now() - authState.createdAt > STATE_TTL_MS) {
    authStates.delete(state);
    const authError = {
      name: 'AuthorizationError',
      message: 'Authorization state has expired',
      code: 'expired_state',
    } as AuthorizationError;
    return { valid: false, error: authError };
  }
  
  authLogger.debug('Callback validation successful', {
    state: state.substring(0, 8) + '...',
  });
  
  return { valid: true, code, authState };
}

/**
 * Exchanges authorization code for access and refresh tokens
 */
export async function exchangeCodeForTokens(
  code: string,
  codeVerifier: string
): Promise<TokenSet> {
  authLogger.info('Exchanging authorization code for tokens');
  
  // Build token request body (x-www-form-urlencoded)
  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: config.epic.redirectUri,
    client_id: config.epic.clientId,
    code_verifier: codeVerifier,
  });
  
  try {
    const response = await axios.post<TokenResponse>(
      config.epic.tokenUrl,
      params.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
        },
        timeout: 30000,
      }
    );
    
    const tokenResponse = response.data;
    
    // Convert to internal token set format
    const tokenSet: TokenSet = {
      accessToken: tokenResponse.access_token,
      tokenType: tokenResponse.token_type,
      expiresAt: Date.now() + (tokenResponse.expires_in * 1000),
      scope: tokenResponse.scope,
      patientId: tokenResponse.patient,
      refreshToken: tokenResponse.refresh_token,
      idToken: tokenResponse.id_token,
    };
    
    authLogger.info('Token exchange successful', {
      patientId: tokenSet.patientId,
      expiresIn: tokenResponse.expires_in,
      hasRefreshToken: !!tokenSet.refreshToken,
      scopes: tokenSet.scope,
    });
    
    return tokenSet;
    
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<OAuthError>;
      const oauthError = axiosError.response?.data;
      
      authLogger.error('Token exchange failed', {
        status: axiosError.response?.status,
        error: oauthError?.error,
        description: oauthError?.error_description,
      });
      
      throw new Error(
        oauthError?.error_description || 
        oauthError?.error || 
        'Token exchange failed'
      );
    }
    throw error;
  }
}

/**
 * Refreshes an access token using a refresh token
 */
export async function refreshAccessToken(refreshToken: string): Promise<TokenSet> {
  authLogger.info('Refreshing access token');
  
  const params = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
    client_id: config.epic.clientId,
  });
  
  try {
    const response = await axios.post<TokenResponse>(
      config.epic.tokenUrl,
      params.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
        },
        timeout: 30000,
      }
    );
    
    const tokenResponse = response.data;
    
    const tokenSet: TokenSet = {
      accessToken: tokenResponse.access_token,
      tokenType: tokenResponse.token_type,
      expiresAt: Date.now() + (tokenResponse.expires_in * 1000),
      scope: tokenResponse.scope,
      patientId: tokenResponse.patient,
      refreshToken: tokenResponse.refresh_token || refreshToken, // Keep old if not returned
      idToken: tokenResponse.id_token,
    };
    
    authLogger.info('Token refresh successful', {
      patientId: tokenSet.patientId,
      expiresIn: tokenResponse.expires_in,
    });
    
    return tokenSet;
    
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<OAuthError>;
      const oauthError = axiosError.response?.data;
      
      authLogger.error('Token refresh failed', {
        status: axiosError.response?.status,
        error: oauthError?.error,
        description: oauthError?.error_description,
      });
      
      throw new Error(
        oauthError?.error_description || 
        oauthError?.error || 
        'Token refresh failed'
      );
    }
    throw error;
  }
}

/**
 * Checks if a token set has expired or is about to expire
 * @param bufferSeconds - Buffer time before actual expiration (default: 60s)
 */
export function isTokenExpired(tokenSet: TokenSet, bufferSeconds: number = 60): boolean {
  return Date.now() >= (tokenSet.expiresAt - (bufferSeconds * 1000));
}

/**
 * Gets a valid access token, refreshing if necessary
 */
export async function getValidAccessToken(tokenSet: TokenSet): Promise<TokenSet> {
  if (!isTokenExpired(tokenSet)) {
    return tokenSet;
  }
  
  if (!tokenSet.refreshToken) {
    throw new Error('Access token expired and no refresh token available');
  }
  
  authLogger.info('Access token expired, refreshing...');
  return refreshAccessToken(tokenSet.refreshToken);
}

