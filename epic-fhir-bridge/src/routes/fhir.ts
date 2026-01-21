/**
 * FHIR API Routes
 * Proxies authenticated requests to Epic's FHIR API
 */

import { Router, Request, Response, NextFunction } from 'express';
import { createFHIRClient } from '../fhir/index.js';
import { fhirLogger } from '../logger.js';
import type { TokenSet } from '../types/index.js';
import { authStore } from './auth.js';

const router = Router();

/**
 * Middleware to ensure user is authenticated
 * Checks both session tokens AND global authStore (for cross-origin support)
 */
function requireAuth(req: Request, res: Response, next: NextFunction): void {
  // First try session tokens
  let tokens = req.session.tokens;
  
  // If no session tokens, try global authStore
  if (!tokens && authStore.accessToken && authStore.patientId) {
    tokens = {
      accessToken: authStore.accessToken,
      refreshToken: authStore.refreshToken,
      patientId: authStore.patientId!,
      expiresAt: authStore.expiresAt?.getTime() || Date.now() + 3600000,
      scope: authStore.scope || '',
    };
  }
  
  if (!tokens) {
    res.status(401).json({
      error: 'not_authenticated',
      message: 'Please authorize first at /auth/authorize',
    });
    return;
  }
  
  // Attach tokens to request for downstream use
  (req as Request & { tokens: TokenSet }).tokens = tokens;
  next();
}

/**
 * Helper to get FHIR client from request
 */
function getFHIRClient(req: Request) {
  const tokens = (req as Request & { tokens: TokenSet }).tokens;
  return createFHIRClient(tokens, {
    onTokenRefresh: (newTokenSet) => {
      req.session.tokens = newTokenSet;
    },
  });
}

// Apply auth middleware to all routes
router.use(requireAuth);

// ============================================
// Patient Endpoints
// ============================================

/**
 * GET /fhir/patient
 * Get the current patient (from launch context)
 */
router.get('/patient', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patient = await client.getPatient();
    res.json(patient);
  } catch (error) {
    handleFHIRError(res, error, 'fetch patient');
  }
});

/**
 * GET /fhir/patient/:id
 * Get a specific patient by ID
 */
router.get('/patient/:id', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.params['id'];
    if (!patientId) {
      res.status(400).json({ error: 'missing_patient_id', message: 'Patient ID is required' });
      return;
    }
    const patient = await client.getPatient(patientId);
    res.json(patient);
  } catch (error) {
    handleFHIRError(res, error, 'fetch patient');
  }
});

// ============================================
// Coverage Endpoints
// ============================================

/**
 * GET /fhir/coverage
 * Get all coverage records for the current patient
 */
router.get('/coverage', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const coverages = await client.getCoverages(patientId);
    res.json(coverages);
  } catch (error) {
    handleFHIRError(res, error, 'fetch coverages');
  }
});

/**
 * GET /fhir/coverage/active
 * Get active coverage records only
 */
router.get('/coverage/active', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const coverages = await client.getActiveCoverages(patientId);
    res.json(coverages);
  } catch (error) {
    handleFHIRError(res, error, 'fetch active coverages');
  }
});

/**
 * GET /fhir/coverage/:id
 * Get a specific coverage by ID
 */
router.get('/coverage/:id', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const coverageId = req.params['id'];
    if (!coverageId) {
      res.status(400).json({ error: 'missing_coverage_id', message: 'Coverage ID is required' });
      return;
    }
    const coverage = await client.getCoverage(coverageId);
    res.json(coverage);
  } catch (error) {
    handleFHIRError(res, error, 'fetch coverage');
  }
});

// ============================================
// Explanation of Benefit Endpoints
// ============================================

/**
 * GET /fhir/eob
 * Get all Explanation of Benefit records for the current patient
 */
router.get('/eob', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const eobs = await client.getExplanationOfBenefits(patientId);
    res.json(eobs);
  } catch (error) {
    handleFHIRError(res, error, 'fetch explanation of benefits');
  }
});

/**
 * GET /fhir/eob/:id
 * Get a specific EOB by ID
 */
router.get('/eob/:id', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const eobId = req.params['id'];
    if (!eobId) {
      res.status(400).json({ error: 'missing_eob_id', message: 'EOB ID is required' });
      return;
    }
    const eob = await client.getExplanationOfBenefit(eobId);
    res.json(eob);
  } catch (error) {
    handleFHIRError(res, error, 'fetch explanation of benefit');
  }
});

// ============================================
// Condition Endpoints
// ============================================

/**
 * GET /fhir/condition
 * Get all conditions for the current patient
 */
router.get('/condition', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const conditions = await client.getConditions(patientId);
    res.json(conditions);
  } catch (error) {
    handleFHIRError(res, error, 'fetch conditions');
  }
});

/**
 * GET /fhir/condition/active
 * Get active conditions only
 */
router.get('/condition/active', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const conditions = await client.getActiveConditions(patientId);
    res.json(conditions);
  } catch (error) {
    handleFHIRError(res, error, 'fetch active conditions');
  }
});

// ============================================
// Observation Endpoints
// ============================================

/**
 * GET /fhir/observation
 * Get observations for the current patient
 */
router.get('/observation', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const category = req.query['category'] as 'vital-signs' | 'laboratory' | 'social-history' | undefined;
    const observations = await client.getObservations(patientId, category);
    res.json(observations);
  } catch (error) {
    handleFHIRError(res, error, 'fetch observations');
  }
});

/**
 * GET /fhir/observation/vitals
 * Get vital signs
 */
router.get('/observation/vitals', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const vitals = await client.getVitalSigns(patientId);
    res.json(vitals);
  } catch (error) {
    handleFHIRError(res, error, 'fetch vital signs');
  }
});

/**
 * GET /fhir/observation/labs
 * Get lab results
 */
router.get('/observation/labs', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const labs = await client.getLabResults(patientId);
    res.json(labs);
  } catch (error) {
    handleFHIRError(res, error, 'fetch lab results');
  }
});

// ============================================
// Procedure Endpoints
// ============================================

/**
 * GET /fhir/procedure
 * Get all procedures for the current patient
 */
router.get('/procedure', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const procedures = await client.getProcedures(patientId);
    res.json(procedures);
  } catch (error) {
    handleFHIRError(res, error, 'fetch procedures');
  }
});

// ============================================
// MedicationRequest Endpoints
// ============================================

/**
 * GET /fhir/medication
 * Get all medication requests for the current patient
 */
router.get('/medication', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const medications = await client.getMedicationRequests(patientId);
    res.json(medications);
  } catch (error) {
    handleFHIRError(res, error, 'fetch medications');
  }
});

/**
 * GET /fhir/medication/active
 * Get active medications only
 */
router.get('/medication/active', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const medications = await client.getActiveMedications(patientId);
    res.json(medications);
  } catch (error) {
    handleFHIRError(res, error, 'fetch active medications');
  }
});

// ============================================
// Encounter Endpoints
// ============================================

/**
 * GET /fhir/encounter
 * Get all encounters for the current patient
 */
router.get('/encounter', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const encounters = await client.getEncounters(patientId);
    res.json(encounters);
  } catch (error) {
    handleFHIRError(res, error, 'fetch encounters');
  }
});

// ============================================
// AllergyIntolerance Endpoints
// ============================================

/**
 * GET /fhir/allergy
 * Get all allergies for the current patient
 */
router.get('/allergy', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const allergies = await client.getAllergies(patientId);
    res.json(allergies);
  } catch (error) {
    handleFHIRError(res, error, 'fetch allergies');
  }
});

// ============================================
// Immunization Endpoints
// ============================================

/**
 * GET /fhir/immunization
 * Get all immunizations for the current patient
 */
router.get('/immunization', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const immunizations = await client.getImmunizations(patientId);
    res.json(immunizations);
  } catch (error) {
    handleFHIRError(res, error, 'fetch immunizations');
  }
});

// ============================================
// DiagnosticReport Endpoints
// ============================================

/**
 * GET /fhir/diagnostic-report
 * Get all diagnostic reports for the current patient
 */
router.get('/diagnostic-report', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const reports = await client.getDiagnosticReports(patientId);
    res.json(reports);
  } catch (error) {
    handleFHIRError(res, error, 'fetch diagnostic reports');
  }
});

// ============================================
// DocumentReference Endpoints
// ============================================

/**
 * GET /fhir/document
 * Get all document references for the current patient
 */
router.get('/document', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const documents = await client.getDocumentReferences(patientId);
    res.json(documents);
  } catch (error) {
    handleFHIRError(res, error, 'fetch documents');
  }
});

// ============================================
// CarePlan Endpoints
// ============================================

/**
 * GET /fhir/careplan
 * Get all care plans for the current patient
 */
router.get('/careplan', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const carePlans = await client.getCarePlans(patientId);
    res.json(carePlans);
  } catch (error) {
    handleFHIRError(res, error, 'fetch care plans');
  }
});

// ============================================
// Bulk Data Endpoints
// ============================================

/**
 * GET /fhir/all
 * Get ALL available clinical data for the patient (for claims processing)
 */
router.get('/all', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    
    // Fetch all resources in parallel, catching individual errors
    const results = await Promise.allSettled([
      client.getPatient(patientId),
      client.getConditions(patientId),
      client.getProcedures(patientId),
      client.getMedicationRequests(patientId),
      client.getObservations(patientId),
      client.getEncounters(patientId),
      client.getAllergies(patientId),
      client.getImmunizations(patientId),
      client.getDiagnosticReports(patientId),
      client.getCoverages(patientId),
    ]);
    
    const [
      patientResult,
      conditionsResult,
      proceduresResult,
      medicationsResult,
      observationsResult,
      encountersResult,
      allergiesResult,
      immunizationsResult,
      diagnosticReportsResult,
      coveragesResult,
    ] = results;
    
    res.json({
      patient: patientResult.status === 'fulfilled' ? patientResult.value : null,
      conditions: conditionsResult.status === 'fulfilled' ? conditionsResult.value : null,
      procedures: proceduresResult.status === 'fulfilled' ? proceduresResult.value : null,
      medications: medicationsResult.status === 'fulfilled' ? medicationsResult.value : null,
      observations: observationsResult.status === 'fulfilled' ? observationsResult.value : null,
      encounters: encountersResult.status === 'fulfilled' ? encountersResult.value : null,
      allergies: allergiesResult.status === 'fulfilled' ? allergiesResult.value : null,
      immunizations: immunizationsResult.status === 'fulfilled' ? immunizationsResult.value : null,
      diagnosticReports: diagnosticReportsResult.status === 'fulfilled' ? diagnosticReportsResult.value : null,
      coverages: coveragesResult.status === 'fulfilled' ? coveragesResult.value : null,
      _errors: results
        .map((r, i) => {
          if (r.status === 'rejected') {
            const resources = ['patient', 'conditions', 'procedures', 'medications', 'observations', 'encounters', 'allergies', 'immunizations', 'diagnosticReports', 'coverages'];
            return { resource: resources[i], error: r.reason?.message || 'Unknown error' };
          }
          return null;
        })
        .filter(Boolean),
    });
  } catch (error) {
    handleFHIRError(res, error, 'fetch all clinical data');
  }
});

/**
 * GET /fhir/insurance-data
 * Get comprehensive patient insurance data
 */
router.get('/insurance-data', async (req: Request, res: Response) => {
  try {
    const client = getFHIRClient(req);
    const patientId = req.query['patient'] as string | undefined;
    const data = await client.getPatientInsuranceData(patientId);
    res.json(data);
  } catch (error) {
    handleFHIRError(res, error, 'fetch insurance data');
  }
});

// ============================================
// Error Handling
// ============================================

function handleFHIRError(res: Response, error: unknown, operation: string): void {
  fhirLogger.error(`Failed to ${operation}`, { 
    error: error instanceof Error ? error.message : 'Unknown error' 
  });
  
  if (error instanceof Error && 'statusCode' in error) {
    const fhirError = error as Error & { statusCode: number; response?: unknown };
    res.status(fhirError.statusCode || 500).json({
      error: 'fhir_error',
      message: error.message,
      details: fhirError.response,
    });
    return;
  }
  
  res.status(500).json({
    error: 'fhir_error',
    message: error instanceof Error ? error.message : `Failed to ${operation}`,
  });
}

export default router;

