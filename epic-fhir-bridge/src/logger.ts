/**
 * Winston logger configuration for Epic FHIR Bridge
 * Structured logging for debugging OAuth flows and FHIR requests
 */

import winston from 'winston';

const { combine, timestamp, printf, colorize, errors } = winston.format;

// Custom format for development
const devFormat = printf(({ level, message, timestamp, ...metadata }) => {
  let msg = `${timestamp} [${level}]: ${message}`;
  if (Object.keys(metadata).length > 0) {
    // Don't log sensitive data in plain text
    const sanitized = sanitizeMetadata(metadata);
    msg += ` ${JSON.stringify(sanitized)}`;
  }
  return msg;
});

// Sanitize sensitive fields from logs
function sanitizeMetadata(obj: Record<string, unknown>): Record<string, unknown> {
  const sensitiveFields = [
    'access_token',
    'refresh_token',
    'id_token',
    'code_verifier',
    'code',
    'authorization',
    'Authorization',
    'accessToken',
    'refreshToken',
    'codeVerifier',
  ];
  
  const sanitized: Record<string, unknown> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    if (sensitiveFields.includes(key)) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeMetadata(value as Record<string, unknown>);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

const logLevel = process.env['LOG_LEVEL'] || 'info';

export const logger = winston.createLogger({
  level: logLevel,
  format: combine(
    errors({ stack: true }),
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }),
  ),
  transports: [
    new winston.transports.Console({
      format: combine(
        colorize(),
        devFormat
      ),
    }),
  ],
});

// Create child loggers for different modules
export const authLogger = logger.child({ module: 'auth' });
export const fhirLogger = logger.child({ module: 'fhir' });
export const serverLogger = logger.child({ module: 'server' });

