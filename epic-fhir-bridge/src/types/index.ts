/**
 * Type definitions for Insurabridge Epic FHIR Bridge
 * SMART-on-FHIR OAuth 2.0 with PKCE
 */

// ============================================
// PKCE Types
// ============================================

export interface PKCEParams {
  /** Random string 43-128 chars using A-Z, a-z, 0-9, -, ., _, ~ */
  codeVerifier: string;
  /** SHA256 hash of codeVerifier, base64url encoded */
  codeChallenge: string;
  /** Always "S256" for SHA256 */
  codeChallengeMethod: 'S256';
}

// ============================================
// OAuth Types
// ============================================

export interface AuthorizationState {
  /** Random state string for CSRF protection */
  state: string;
  /** PKCE code verifier (stored for token exchange) */
  codeVerifier: string;
  /** Timestamp when this state was created */
  createdAt: number;
  /** Optional: redirect URL after successful auth */
  returnTo?: string;
}

export interface AuthorizationParams {
  responseType: 'code';
  clientId: string;
  redirectUri: string;
  scope: string;
  state: string;
  aud: string; // FHIR base URL
  codeChallenge: string;
  codeChallengeMethod: 'S256';
}

export interface TokenRequest {
  grantType: 'authorization_code' | 'refresh_token';
  code?: string;
  refreshToken?: string;
  redirectUri: string;
  clientId: string;
  codeVerifier?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'Bearer';
  expires_in: number;
  scope: string;
  /** FHIR Patient ID returned by Epic */
  patient?: string;
  /** Refresh token (if offline_access was requested) */
  refresh_token?: string;
  /** ID token (if openid scope was requested) */
  id_token?: string;
}

export interface TokenSet {
  accessToken: string;
  tokenType: string;
  expiresAt: number; // Unix timestamp
  scope: string;
  patientId?: string;
  refreshToken?: string;
  idToken?: string;
}

// ============================================
// FHIR Resource Types (Simplified for Insurance)
// ============================================

export interface FHIRResource {
  resourceType: string;
  id: string;
  meta?: {
    versionId?: string;
    lastUpdated?: string;
  };
}

export interface FHIRBundle<T extends FHIRResource = FHIRResource> {
  resourceType: 'Bundle';
  type: 'searchset' | 'batch' | 'transaction' | 'history' | 'collection';
  total?: number;
  link?: Array<{
    relation: string;
    url: string;
  }>;
  entry?: Array<{
    fullUrl?: string;
    resource: T;
  }>;
}

export interface Patient extends FHIRResource {
  resourceType: 'Patient';
  identifier?: Array<{
    system?: string;
    value?: string;
    type?: {
      coding?: Array<{ system?: string; code?: string; display?: string }>;
    };
  }>;
  name?: Array<{
    use?: string;
    family?: string;
    given?: string[];
    prefix?: string[];
    suffix?: string[];
  }>;
  gender?: 'male' | 'female' | 'other' | 'unknown';
  birthDate?: string;
  address?: Array<{
    use?: string;
    line?: string[];
    city?: string;
    state?: string;
    postalCode?: string;
    country?: string;
  }>;
  telecom?: Array<{
    system?: string;
    value?: string;
    use?: string;
  }>;
}

export interface Coverage extends FHIRResource {
  resourceType: 'Coverage';
  status: 'active' | 'cancelled' | 'draft' | 'entered-in-error';
  type?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
  subscriber?: {
    reference?: string;
  };
  beneficiary?: {
    reference?: string;
  };
  relationship?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
  period?: {
    start?: string;
    end?: string;
  };
  payor?: Array<{
    reference?: string;
    display?: string;
  }>;
  class?: Array<{
    type?: {
      coding?: Array<{ system?: string; code?: string; display?: string }>;
    };
    value?: string;
    name?: string;
  }>;
  network?: string;
  order?: number;
}

export interface ExplanationOfBenefit extends FHIRResource {
  resourceType: 'ExplanationOfBenefit';
  status: 'active' | 'cancelled' | 'draft' | 'entered-in-error';
  type: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
  use: 'claim' | 'preauthorization' | 'predetermination';
  patient: {
    reference: string;
  };
  billablePeriod?: {
    start?: string;
    end?: string;
  };
  created?: string;
  insurer?: {
    reference?: string;
    display?: string;
  };
  provider?: {
    reference?: string;
  };
  outcome?: 'queued' | 'complete' | 'error' | 'partial';
  disposition?: string;
  insurance?: Array<{
    focal?: boolean;
    coverage?: {
      reference?: string;
    };
  }>;
  item?: Array<{
    sequence?: number;
    productOrService?: {
      coding?: Array<{ system?: string; code?: string; display?: string }>;
    };
    servicedDate?: string;
    servicedPeriod?: {
      start?: string;
      end?: string;
    };
    adjudication?: Array<{
      category?: {
        coding?: Array<{ system?: string; code?: string; display?: string }>;
      };
      amount?: {
        value?: number;
        currency?: string;
      };
    }>;
  }>;
  total?: Array<{
    category?: {
      coding?: Array<{ system?: string; code?: string; display?: string }>;
    };
    amount?: {
      value?: number;
      currency?: string;
    };
  }>;
  payment?: {
    type?: {
      coding?: Array<{ system?: string; code?: string; display?: string }>;
    };
    date?: string;
    amount?: {
      value?: number;
      currency?: string;
    };
  };
}

export interface Condition extends FHIRResource {
  resourceType: 'Condition';
  clinicalStatus?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
  verificationStatus?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
  category?: Array<{
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  }>;
  code?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
    text?: string;
  };
  subject: {
    reference: string;
  };
  onsetDateTime?: string;
  recordedDate?: string;
}

export interface Observation extends FHIRResource {
  resourceType: 'Observation';
  status: 'registered' | 'preliminary' | 'final' | 'amended' | 'corrected' | 'cancelled' | 'entered-in-error' | 'unknown';
  category?: Array<{
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  }>;
  code: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
    text?: string;
  };
  subject?: {
    reference: string;
  };
  effectiveDateTime?: string;
  valueQuantity?: {
    value?: number;
    unit?: string;
    system?: string;
    code?: string;
  };
  valueString?: string;
  valueCodeableConcept?: {
    coding?: Array<{ system?: string; code?: string; display?: string }>;
  };
}

// ============================================
// Session Types
// ============================================

declare module 'express-session' {
  interface SessionData {
    authState?: AuthorizationState;
    tokens?: TokenSet;
  }
}

// ============================================
// Error Types
// ============================================

export interface OAuthError {
  error: string;
  error_description?: string;
  error_uri?: string;
}

export class FHIRClientError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message);
    this.name = 'FHIRClientError';
  }
}

export class AuthorizationError extends Error {
  constructor(
    message: string,
    public code: string,
    public description?: string
  ) {
    super(message);
    this.name = 'AuthorizationError';
  }
}

