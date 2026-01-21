# Insurabridge Data Schemas

## Overview

This document describes the data models and schemas used in Insurabridge. All schemas are designed for:
- FHIR R4 compatibility
- HIPAA compliance (encrypted at rest)
- Audit traceability
- Efficient processing

---

## Core Entities

### Patient

```typescript
interface Patient {
  // Internal identifier
  id: string                  // UUID, internal
  
  // External references
  fhir_id: string | null      // FHIR Patient resource ID
  mrn: string | null          // Medical Record Number
  
  // Demographics (encrypted)
  first_name: string
  last_name: string
  date_of_birth: string       // YYYY-MM-DD
  gender: string | null       // male | female | other | unknown
  
  // Contact (encrypted)
  address_line1: string | null
  address_line2: string | null
  city: string | null
  state: string | null
  zip_code: string | null
  phone: string | null
  
  // Insurance reference
  primary_insurance_id: string | null
  
  // Metadata
  created_at: datetime
  updated_at: datetime
}
```

### Encounter

```typescript
interface Encounter {
  id: string
  patient_id: string          // FK to Patient
  fhir_id: string | null
  
  // Type
  encounter_type: "inpatient" | "outpatient" | "emergency" | "observation"
  status: "planned" | "in-progress" | "finished" | "cancelled"
  
  // Timing
  start_date: datetime
  end_date: datetime | null
  
  // Provider
  attending_provider_id: string | null
  facility_id: string | null
  place_of_service: string | null  // CMS POS code (2 digits)
  
  // Clinical content (encrypted)
  clinical_notes: text | null      // Full clinical documentation
  
  created_at: datetime
  updated_at: datetime
}
```

### Claim

```typescript
interface Claim {
  id: string
  encounter_id: string        // FK to Encounter
  patient_id: string          // FK to Patient
  
  // Identification
  claim_number: string | null // External claim number
  claim_type: "professional" | "institutional"
  
  // Status tracking
  status: "draft" | "validated" | "submitted" | "paid" | "denied"
  
  // Financial
  total_charges: number | null
  allowed_amount: number | null
  paid_amount: number | null
  
  // Payer
  payer_id: string | null
  payer_name: string | null
  
  // Dates
  service_date_start: datetime | null
  service_date_end: datetime | null
  submission_date: datetime | null
  
  // Claim data (full structure)
  claim_data: ClaimData
  
  // Reasoning (audit trail)
  reasoning_chain: ReasoningChain | null
  confidence_score: number | null   // 0-1
  
  // Flags
  requires_review: boolean
  review_notes: text | null
  
  created_at: datetime
  updated_at: datetime
}

interface ClaimData {
  diagnoses: Diagnosis[]
  lines: ClaimLine[]
  provider: ProviderInfo
  subscriber: SubscriberInfo
}

interface Diagnosis {
  sequence: number           // 1-12
  code: string              // ICD-10 code
  description: string
  is_primary: boolean
  is_admitting: boolean
  
  // Evidence
  confidence_level: "high" | "medium" | "low"
  confidence_score: number   // 0-1
  supporting_evidence: string[]
}

interface ClaimLine {
  line_number: number
  
  // Service
  service_date: datetime
  place_of_service: string   // 2-digit CMS code
  
  // Codes
  cpt_code: string | null
  hcpcs_code: string | null
  modifiers: string[]        // Up to 4
  
  // Diagnosis pointers
  diagnosis_pointers: number[] // References to diagnosis sequence
  
  // Units and charges
  units: number
  charge_amount: number
  
  // Evidence
  description: string
  supporting_evidence: Evidence[]
  code_rationale: string | null
  confidence_score: number | null
}
```

### Denial

```typescript
interface Denial {
  id: string
  claim_id: string           // FK to Claim
  
  // Denial details
  denial_date: datetime
  denial_code: string | null  // CARC/RARC code
  denial_reason: text
  
  // Classification
  denial_category: 
    | "medical_necessity"
    | "coding"
    | "coverage"
    | "authorization"
    | "documentation"
    | "timely_filing"
    | "duplicate"
    | "other"
  
  // Amount
  denied_amount: number
  
  // Analysis
  ai_analysis: DenialAnalysis | null
  appeal_likelihood: number | null  // 0-1
  
  created_at: datetime
  updated_at: datetime
}

interface DenialAnalysis {
  category: string
  category_confidence: number
  root_cause: string
  policy_references: string[]
  is_appealable: boolean
  appeal_likelihood: number
  appeal_rationale: string
  recommended_actions: string[]
  required_documentation: string[]
}
```

### Appeal

```typescript
interface Appeal {
  id: string
  denial_id: string          // FK to Denial
  claim_id: string           // FK to Claim
  
  // Appeal details
  appeal_level: number       // 1, 2, 3...
  status: "draft" | "submitted" | "in_review" | "won" | "lost"
  
  // Generated content
  appeal_letter: text | null
  supporting_arguments: Argument[]
  citations: Citation[]
  
  // Tracking
  submission_date: datetime | null
  response_date: datetime | null
  outcome: string | null
  
  created_at: datetime
  updated_at: datetime
}

interface Citation {
  source_type: "document" | "policy" | "guideline" | "code_book"
  source_id: string
  source_title: string
  location: string | null     // page, section
  quoted_text: string | null
  relevance: string
}
```

---

## Reasoning Schemas

### ReasoningChain

```typescript
interface ReasoningChain {
  chain_id: string
  created_at: datetime
  
  // Context
  encounter_id: string | null
  task_type: "claim_generation" | "validation" | "denial_analysis" | "audit"
  
  // Steps
  steps: ReasoningStep[]
  
  // Outputs
  diagnoses: CodeSuggestion[]
  procedures: CodeSuggestion[]
  
  // Overall assessment
  overall_confidence: "high" | "medium" | "low" | "uncertain"
  overall_score: number       // 0-1
  
  // Compliance
  compliance_issues: string[]
  recommendations: string[]
  
  // Human review
  requires_human_review: boolean
  review_priority: "low" | "normal" | "high" | "urgent"
}

interface ReasoningStep {
  step_number: number
  step_type: 
    | "evidence_extraction"
    | "diagnosis_mapping"
    | "procedure_mapping"
    | "policy_alignment"
    | "compliance_check"
    | "confidence_assessment"
  input_summary: string
  output_summary: string
  reasoning: string
  citations: Citation[]
  duration_ms: number
}

interface Evidence {
  evidence_type: 
    | "diagnosis"
    | "procedure"
    | "lab_result"
    | "vital_sign"
    | "medication"
    | "imaging"
    | "provider_attestation"
    | "history"
  content: string
  extracted_value: string | null
  date: datetime | null
  provider: string | null
  citation: Citation
  confidence: number
}

interface CodeSuggestion {
  code: string
  code_type: "ICD10CM" | "ICD10PCS" | "CPT" | "HCPCS"
  description: string
  
  // Evidence chain
  supporting_evidence: Evidence[]
  policy_citations: Citation[]
  guideline_citations: Citation[]
  
  // Medical necessity
  medical_necessity_met: boolean
  medical_necessity_rationale: string | null
  
  // Confidence
  confidence_level: "high" | "medium" | "low"
  confidence_score: number
  uncertainty_factors: string[]
  
  // Compliance
  requires_modifier: boolean
  suggested_modifiers: string[]
  bundling_notes: string | null
  
  // Human review
  requires_review: boolean
  review_reason: string | null
}
```

---

## Knowledge Schemas

### Code References

```typescript
interface ICD10Code {
  code: string               // Primary key
  description: string
  long_description: string | null
  
  code_type: "CM" | "PCS"
  chapter: string | null
  category: string | null
  
  is_billable: boolean
  effective_date: date | null
  end_date: date | null
  
  version_year: number       // 2024
}

interface CPTCode {
  code: string               // 5 digits
  description: string
  long_description: string | null
  
  section: string | null
  subsection: string | null
  
  // RVUs
  work_rvu: number | null
  facility_pe_rvu: number | null
  non_facility_pe_rvu: number | null
  mp_rvu: number | null
  
  common_modifiers: string[] | null
  
  version_year: number
}

interface HCPCSCode {
  code: string               // Letter + 4 digits
  description: string
  long_description: string | null
  
  category: string | null
  pricing_indicator: string | null
  status_code: string | null
  
  version_year: number
}

interface NCCIEdit {
  id: number
  column_1_code: string
  column_2_code: string
  
  edit_type: "0" | "1" | "9"
  // 0 = not allowed
  // 1 = allowed with modifier
  // 9 = not applicable
  
  effective_date: date | null
  deletion_date: date | null
}

interface MUEValue {
  code: string
  practitioner_mue: number | null
  outpatient_hospital_mue: number | null
  
  rationale: "A" | "C" | "D" | "E" | null
  // A = anatomic
  // C = code descriptor
  // D = DME
  // E = per encounter
  
  effective_date: date | null
}
```

---

## Audit Schema

```typescript
interface AuditEntry {
  id: string
  timestamp: datetime
  
  // Event
  event_type: AuditEventType
  event_description: string
  
  // Actor
  user_id: string | null
  user_role: string | null
  session_id: string | null
  
  // Request context
  request_id: string | null
  ip_address: string | null   // Hashed
  user_agent: string | null
  
  // Resource
  resource_type: string | null
  resource_id: string | null
  
  // Details (no PHI)
  details: object
  
  // Outcome
  success: boolean
  error_message: string | null
  
  // Chain
  previous_hash: string | null
  entry_hash: string
}

type AuditEventType = 
  | "auth.login.success"
  | "auth.login.failure"
  | "auth.logout"
  | "auth.token.refresh"
  | "auth.password.change"
  | "user.create"
  | "user.update"
  | "user.delete"
  | "user.role.change"
  | "phi.view"
  | "phi.create"
  | "phi.update"
  | "phi.delete"
  | "phi.export"
  | "claim.create"
  | "claim.update"
  | "claim.validate"
  | "claim.submit"
  | "claim.delete"
  | "denial.review"
  | "appeal.generate"
  | "appeal.submit"
  | "audit.query"
  | "audit.export"
  | "system.config.change"
  | "system.error"
  | "llm.inference"
  | "llm.reasoning"
```

---

## FHIR Mappings

### Patient
| FHIR Field | Internal Field |
|------------|----------------|
| Patient.id | fhir_id |
| Patient.identifier[MR] | mrn |
| Patient.name[0].given[0] | first_name |
| Patient.name[0].family | last_name |
| Patient.birthDate | date_of_birth |
| Patient.gender | gender |
| Patient.address[0] | address_* |
| Patient.telecom[phone] | phone |

### Encounter
| FHIR Field | Internal Field |
|------------|----------------|
| Encounter.id | fhir_id |
| Encounter.class.code | encounter_type |
| Encounter.status | status |
| Encounter.period.start | start_date |
| Encounter.period.end | end_date |
| Encounter.participant[0].individual | attending_provider_id |
| Encounter.serviceProvider | facility_id |

### Condition
| FHIR Field | Internal Field |
|------------|----------------|
| Condition.id | fhir_id |
| Condition.code.coding[0].code | code |
| Condition.code.coding[0].system | code_system |
| Condition.code.coding[0].display | display |
| Condition.clinicalStatus | clinical_status |
| Condition.onsetDateTime | onset_date |

---

## Database Indexes

```sql
-- Patients
CREATE INDEX ix_patients_mrn ON patients(mrn);
CREATE INDEX ix_patients_fhir_id ON patients(fhir_id);

-- Encounters
CREATE INDEX ix_encounters_patient_id ON encounters(patient_id);
CREATE INDEX ix_encounters_start_date ON encounters(start_date);

-- Claims
CREATE INDEX ix_claims_encounter_id ON claims(encounter_id);
CREATE INDEX ix_claims_patient_id ON claims(patient_id);
CREATE INDEX ix_claims_status ON claims(status);

-- Denials
CREATE INDEX ix_denials_claim_id ON denials(claim_id);
CREATE INDEX ix_denials_denial_category ON denials(denial_category);

-- Code lookups (FTS5)
CREATE VIRTUAL TABLE icd10_fts USING fts5(code, description, content=icd10_codes);
CREATE VIRTUAL TABLE cpt_fts USING fts5(code, description, content=cpt_codes);

-- NCCI
CREATE INDEX ix_ncci_column1 ON ncci_edits(column_1_code);
CREATE INDEX ix_ncci_column2 ON ncci_edits(column_2_code);
```

