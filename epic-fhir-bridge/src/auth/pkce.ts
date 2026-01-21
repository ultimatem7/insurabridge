/**
 * PKCE (Proof Key for Code Exchange) Implementation
 * RFC 7636 compliant for SMART-on-FHIR public clients
 * 
 * PKCE prevents authorization code interception attacks
 * by requiring a cryptographic proof during token exchange.
 */

import crypto from 'crypto';
import type { PKCEParams } from '../types/index.js';
import { authLogger } from '../logger.js';

// Characters allowed in code_verifier per RFC 7636
const CODE_VERIFIER_CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';

// Recommended length for code_verifier (max is 128, min is 43)
const CODE_VERIFIER_LENGTH = 64;

/**
 * Generates a cryptographically random code_verifier
 * Must be 43-128 characters using unreserved URI characters
 */
export function generateCodeVerifier(length: number = CODE_VERIFIER_LENGTH): string {
  if (length < 43 || length > 128) {
    throw new Error('code_verifier length must be between 43 and 128 characters');
  }
  
  const randomBytes = crypto.randomBytes(length);
  let verifier = '';
  
  for (let i = 0; i < length; i++) {
    const byte = randomBytes[i];
    if (byte !== undefined) {
      verifier += CODE_VERIFIER_CHARSET[byte % CODE_VERIFIER_CHARSET.length];
    }
  }
  
  authLogger.debug('Generated code_verifier', { length: verifier.length });
  return verifier;
}

/**
 * Generates code_challenge from code_verifier using S256 method
 * code_challenge = BASE64URL(SHA256(code_verifier))
 */
export function generateCodeChallenge(codeVerifier: string): string {
  // SHA256 hash of the code_verifier
  const hash = crypto.createHash('sha256').update(codeVerifier, 'ascii').digest();
  
  // Base64URL encode (no padding, URL-safe characters)
  const base64 = hash.toString('base64');
  const base64url = base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
  
  authLogger.debug('Generated code_challenge using S256');
  return base64url;
}

/**
 * Generates complete PKCE parameters for an authorization request
 */
export function generatePKCEParams(): PKCEParams {
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = generateCodeChallenge(codeVerifier);
  
  return {
    codeVerifier,
    codeChallenge,
    codeChallengeMethod: 'S256',
  };
}

/**
 * Generates a cryptographically random state parameter for CSRF protection
 */
export function generateState(): string {
  return crypto.randomBytes(32).toString('base64url');
}

/**
 * Validates that a code_verifier matches the expected format
 */
export function validateCodeVerifier(verifier: string): boolean {
  if (verifier.length < 43 || verifier.length > 128) {
    return false;
  }
  
  // Check all characters are in allowed charset
  for (const char of verifier) {
    if (!CODE_VERIFIER_CHARSET.includes(char)) {
      return false;
    }
  }
  
  return true;
}

