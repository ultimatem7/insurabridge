/**
 * Configuration management for Epic FHIR Bridge
 * Loads environment variables with validation
 */

import dotenv from 'dotenv';
import path from 'path';

// Load .env file
dotenv.config({ path: path.resolve(process.cwd(), '.env') });

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optionalEnv(name: string, defaultValue: string): string {
  return process.env[name] || defaultValue;
}

export const config = {
  // Server
  port: parseInt(optionalEnv('PORT', '3000'), 10),
  nodeEnv: optionalEnv('NODE_ENV', 'development'),

  // Session
  sessionSecret: requireEnv('SESSION_SECRET'),

  // Epic OAuth
  epic: {
    clientId: requireEnv('EPIC_CLIENT_ID'),
    fhirBaseUrl: requireEnv('EPIC_FHIR_BASE_URL'),
    authUrl: requireEnv('EPIC_AUTH_URL'),
    tokenUrl: requireEnv('EPIC_TOKEN_URL'),
    redirectUri: requireEnv('REDIRECT_URI'),
    scopes: optionalEnv(
      'FHIR_SCOPES',
      'launch/patient patient/Patient.read patient/Coverage.read patient/ExplanationOfBenefit.read patient/Procedure.read patient/Condition.read patient/Immunization.read patient/Encounter.read patient/MedicationRequest.read patient/DiagnosticReport.read patient/Observation.read patient/AllergyIntolerance.read openid profile offline_access'
    ),
  },

  // Logging
  logLevel: optionalEnv('LOG_LEVEL', 'info'),

  // CORS
  corsOrigins: optionalEnv('CORS_ORIGINS', 'http://localhost:3001').split(','),
} as const;

export type Config = typeof config;

