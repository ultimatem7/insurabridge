/**
 * FHIR API Client for Epic
 * Authenticated requests to FHIR R4 endpoints
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { config } from '../config.js';
import { fhirLogger } from '../logger.js';
import { getValidAccessToken } from '../auth/index.js';
import type {
  TokenSet,
  FHIRBundle,
  Patient,
  Coverage,
  ExplanationOfBenefit,
  Condition,
  Observation,
  FHIRResource,
  FHIRClientError,
} from '../types/index.js';

/**
 * FHIR Client for making authenticated requests to Epic's FHIR API
 */
export class FHIRClient {
  private axiosInstance: AxiosInstance;
  private tokenSet: TokenSet;
  private onTokenRefresh?: (newTokenSet: TokenSet) => void;
  
  constructor(
    tokenSet: TokenSet,
    options?: {
      onTokenRefresh?: (newTokenSet: TokenSet) => void;
    }
  ) {
    this.tokenSet = tokenSet;
    this.onTokenRefresh = options?.onTokenRefresh;
    
    this.axiosInstance = axios.create({
      baseURL: config.epic.fhirBaseUrl,
      timeout: 30000,
      headers: {
        'Accept': 'application/fhir+json',
        'Content-Type': 'application/fhir+json',
      },
    });
    
    // Request interceptor for logging and token refresh
    this.axiosInstance.interceptors.request.use(
      async (reqConfig) => {
        // Ensure we have a valid token
        const validTokenSet = await getValidAccessToken(this.tokenSet);
        if (validTokenSet !== this.tokenSet) {
          this.tokenSet = validTokenSet;
          this.onTokenRefresh?.(validTokenSet);
        }
        
        // Add authorization header
        reqConfig.headers.Authorization = `Bearer ${this.tokenSet.accessToken}`;
        
        fhirLogger.debug('FHIR Request', {
          method: reqConfig.method?.toUpperCase(),
          url: reqConfig.url,
          params: reqConfig.params,
        });
        
        return reqConfig;
      },
      (error) => {
        fhirLogger.error('Request interceptor error', { error: error.message });
        return Promise.reject(error);
      }
    );
    
    // Response interceptor for logging
    this.axiosInstance.interceptors.response.use(
      (response) => {
        fhirLogger.debug('FHIR Response', {
          status: response.status,
          resourceType: response.data?.resourceType,
          total: response.data?.total,
        });
        return response;
      },
      (error: AxiosError) => {
        if (error.response) {
          fhirLogger.error('FHIR API Error', {
            status: error.response.status,
            statusText: error.response.statusText,
            data: error.response.data,
            url: error.config?.url,
          });
        } else if (error.request) {
          fhirLogger.error('FHIR Request Error (no response)', {
            message: error.message,
            url: error.config?.url,
          });
        } else {
          fhirLogger.error('FHIR Client Error', {
            message: error.message,
          });
        }
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Gets the current token set
   */
  getTokenSet(): TokenSet {
    return this.tokenSet;
  }
  
  /**
   * Gets the patient ID from the token set
   */
  getPatientId(): string | undefined {
    return this.tokenSet.patientId;
  }
  
  // ============================================
  // Generic FHIR Methods
  // ============================================
  
  /**
   * Read a resource by ID
   */
  async read<T extends FHIRResource>(
    resourceType: string,
    id: string
  ): Promise<T> {
    try {
      const response = await this.axiosInstance.get<T>(`/${resourceType}/${id}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `read ${resourceType}/${id}`);
    }
  }
  
  /**
   * Search for resources
   */
  async search<T extends FHIRResource>(
    resourceType: string,
    params?: Record<string, string | string[]>
  ): Promise<FHIRBundle<T>> {
    try {
      const response = await this.axiosInstance.get<FHIRBundle<T>>(`/${resourceType}`, {
        params,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error, `search ${resourceType}`);
    }
  }
  
  // ============================================
  // Patient Resource Methods
  // ============================================
  
  /**
   * Get patient by ID
   */
  async getPatient(patientId?: string): Promise<Patient> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching patient', { patientId: id });
    return this.read<Patient>('Patient', id);
  }
  
  /**
   * Search patients (if authorized)
   */
  async searchPatients(params: {
    name?: string;
    identifier?: string;
    birthdate?: string;
  }): Promise<FHIRBundle<Patient>> {
    fhirLogger.info('Searching patients', params);
    return this.search<Patient>('Patient', params as Record<string, string>);
  }
  
  // ============================================
  // Coverage (Insurance) Resource Methods
  // ============================================
  
  /**
   * Get all coverage records for a patient
   */
  async getCoverages(patientId?: string): Promise<FHIRBundle<Coverage>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching coverage records', { patientId: id });
    return this.search<Coverage>('Coverage', { patient: id });
  }
  
  /**
   * Get a specific coverage by ID
   */
  async getCoverage(coverageId: string): Promise<Coverage> {
    fhirLogger.info('Fetching coverage', { coverageId });
    return this.read<Coverage>('Coverage', coverageId);
  }
  
  /**
   * Get active coverages only
   */
  async getActiveCoverages(patientId?: string): Promise<FHIRBundle<Coverage>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching active coverage records', { patientId: id });
    return this.search<Coverage>('Coverage', { 
      patient: id,
      status: 'active',
    });
  }
  
  // ============================================
  // Explanation of Benefit (Claims) Methods
  // ============================================
  
  /**
   * Get all Explanation of Benefit records for a patient
   */
  async getExplanationOfBenefits(patientId?: string): Promise<FHIRBundle<ExplanationOfBenefit>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching Explanation of Benefits', { patientId: id });
    return this.search<ExplanationOfBenefit>('ExplanationOfBenefit', { patient: id });
  }
  
  /**
   * Get a specific EOB by ID
   */
  async getExplanationOfBenefit(eobId: string): Promise<ExplanationOfBenefit> {
    fhirLogger.info('Fetching Explanation of Benefit', { eobId });
    return this.read<ExplanationOfBenefit>('ExplanationOfBenefit', eobId);
  }
  
  /**
   * Get EOBs by date range
   */
  async getExplanationOfBenefitsByDate(
    patientId: string | undefined,
    startDate: string,
    endDate?: string
  ): Promise<FHIRBundle<ExplanationOfBenefit>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    const dateParam = endDate ? `ge${startDate}&date=le${endDate}` : `ge${startDate}`;
    
    fhirLogger.info('Fetching EOBs by date range', { patientId: id, startDate, endDate });
    return this.search<ExplanationOfBenefit>('ExplanationOfBenefit', {
      patient: id,
      created: dateParam,
    });
  }
  
  // ============================================
  // Condition (Diagnosis) Methods
  // ============================================
  
  /**
   * Get all conditions for a patient
   */
  async getConditions(patientId?: string): Promise<FHIRBundle<Condition>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching conditions', { patientId: id });
    return this.search<Condition>('Condition', { patient: id });
  }
  
  /**
   * Get active conditions only
   */
  async getActiveConditions(patientId?: string): Promise<FHIRBundle<Condition>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching active conditions', { patientId: id });
    return this.search<Condition>('Condition', {
      patient: id,
      'clinical-status': 'active',
    });
  }
  
  // ============================================
  // Observation (Labs, Vitals) Methods
  // ============================================
  
  /**
   * Get observations for a patient
   */
  async getObservations(
    patientId?: string,
    category?: 'vital-signs' | 'laboratory' | 'social-history'
  ): Promise<FHIRBundle<Observation>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    const params: Record<string, string> = { patient: id };
    if (category) {
      params['category'] = category;
    }
    
    fhirLogger.info('Fetching observations', { patientId: id, category });
    return this.search<Observation>('Observation', params);
  }
  
  /**
   * Get vital signs
   */
  async getVitalSigns(patientId?: string): Promise<FHIRBundle<Observation>> {
    return this.getObservations(patientId, 'vital-signs');
  }
  
  /**
   * Get lab results
   */
  async getLabResults(patientId?: string): Promise<FHIRBundle<Observation>> {
    return this.getObservations(patientId, 'laboratory');
  }
  
  // ============================================
  // Procedure Methods
  // ============================================
  
  /**
   * Get all procedures for a patient
   */
  async getProcedures(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching procedures', { patientId: id });
    return this.search<FHIRResource>('Procedure', { patient: id });
  }
  
  // ============================================
  // MedicationRequest Methods
  // ============================================
  
  /**
   * Get all medication requests for a patient
   */
  async getMedicationRequests(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching medication requests', { patientId: id });
    return this.search<FHIRResource>('MedicationRequest', { patient: id });
  }
  
  /**
   * Get active medications only
   */
  async getActiveMedications(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching active medications', { patientId: id });
    return this.search<FHIRResource>('MedicationRequest', {
      patient: id,
      status: 'active',
    });
  }
  
  // ============================================
  // Encounter Methods
  // ============================================
  
  /**
   * Get all encounters for a patient
   */
  async getEncounters(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching encounters', { patientId: id });
    return this.search<FHIRResource>('Encounter', { patient: id });
  }
  
  // ============================================
  // AllergyIntolerance Methods
  // ============================================
  
  /**
   * Get all allergies for a patient
   */
  async getAllergies(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching allergies', { patientId: id });
    return this.search<FHIRResource>('AllergyIntolerance', { patient: id });
  }
  
  // ============================================
  // Immunization Methods
  // ============================================
  
  /**
   * Get all immunizations for a patient
   */
  async getImmunizations(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching immunizations', { patientId: id });
    return this.search<FHIRResource>('Immunization', { patient: id });
  }
  
  // ============================================
  // DiagnosticReport Methods
  // ============================================
  
  /**
   * Get all diagnostic reports for a patient
   */
  async getDiagnosticReports(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching diagnostic reports', { patientId: id });
    return this.search<FHIRResource>('DiagnosticReport', { patient: id });
  }
  
  // ============================================
  // DocumentReference Methods
  // ============================================
  
  /**
   * Get all document references for a patient
   */
  async getDocumentReferences(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching document references', { patientId: id });
    return this.search<FHIRResource>('DocumentReference', { patient: id });
  }
  
  // ============================================
  // CarePlan Methods
  // ============================================
  
  /**
   * Get all care plans for a patient
   */
  async getCarePlans(patientId?: string): Promise<FHIRBundle<FHIRResource>> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching care plans', { patientId: id });
    return this.search<FHIRResource>('CarePlan', { patient: id });
  }
  
  // ============================================
  // Bulk Data Retrieval
  // ============================================
  
  /**
   * Get comprehensive patient data for insurance processing
   */
  async getPatientInsuranceData(patientId?: string): Promise<{
    patient: Patient;
    coverages: FHIRBundle<Coverage>;
    explanationOfBenefits: FHIRBundle<ExplanationOfBenefit>;
    conditions: FHIRBundle<Condition>;
  }> {
    const id = patientId || this.tokenSet.patientId;
    if (!id) {
      throw new Error('Patient ID is required');
    }
    
    fhirLogger.info('Fetching comprehensive patient insurance data', { patientId: id });
    
    // Fetch all resources in parallel
    const [patient, coverages, explanationOfBenefits, conditions] = await Promise.all([
      this.getPatient(id),
      this.getCoverages(id),
      this.getExplanationOfBenefits(id),
      this.getConditions(id),
    ]);
    
    return {
      patient,
      coverages,
      explanationOfBenefits,
      conditions,
    };
  }
  
  // ============================================
  // Error Handling
  // ============================================
  
  private handleError(error: unknown, operation: string): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      const status = axiosError.response?.status;
      const data = axiosError.response?.data;
      
      // Create a proper error with FHIR operation outcome if available
      const message = this.extractErrorMessage(data) || 
        `FHIR API error during ${operation}: ${axiosError.message}`;
      
      const fhirError = new Error(message) as Error & { 
        statusCode?: number; 
        response?: unknown;
        name: string;
      };
      fhirError.name = 'FHIRClientError';
      fhirError.statusCode = status;
      fhirError.response = data;
      
      return fhirError;
    }
    
    if (error instanceof Error) {
      return error;
    }
    
    return new Error(`Unknown error during ${operation}`);
  }
  
  private extractErrorMessage(data: unknown): string | null {
    if (!data || typeof data !== 'object') return null;
    
    // Check for FHIR OperationOutcome
    const outcome = data as { resourceType?: string; issue?: Array<{ diagnostics?: string; details?: { text?: string } }> };
    if (outcome.resourceType === 'OperationOutcome' && outcome.issue) {
      const firstIssue = outcome.issue[0];
      return firstIssue?.diagnostics || firstIssue?.details?.text || null;
    }
    
    // Check for simple error message
    const errorData = data as { error?: string; message?: string };
    return errorData.error || errorData.message || null;
  }
}

/**
 * Factory function to create a FHIR client
 */
export function createFHIRClient(
  tokenSet: TokenSet,
  options?: {
    onTokenRefresh?: (newTokenSet: TokenSet) => void;
  }
): FHIRClient {
  return new FHIRClient(tokenSet, options);
}

