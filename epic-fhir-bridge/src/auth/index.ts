/**
 * Authentication Module Exports
 * SMART-on-FHIR OAuth 2.0 with PKCE
 */

export {
  generateCodeVerifier,
  generateCodeChallenge,
  generatePKCEParams,
  generateState,
  validateCodeVerifier,
} from './pkce.js';

export {
  initiateAuthorization,
  getAuthState,
  clearAuthState,
  validateCallback,
  exchangeCodeForTokens,
  refreshAccessToken,
  isTokenExpired,
  getValidAccessToken,
} from './oauth.js';

