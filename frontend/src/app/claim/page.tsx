'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Upload,
  AlertTriangle,
  Check,
  X,
  ChevronRight,
  Sparkles,
  Shield,
  Link,
  BookOpen,
  FileSearch,
  Download,
  Eye,
  RefreshCw,
} from 'lucide-react'

import {
  CitationBadge,
  ProofChainViewer,
  UnsupportedWarning,
  CodeWithEvidence,
} from '@/components/EvidenceCitation'

// Types matching backend
interface EvidenceAtom {
  evidenceId: string
  evidenceType: string
  documentName: string
  contentExcerpt: string
  location: {
    page?: number
    lineRange?: string
    section?: string
  }
  confidence: number
  citation: string
}

interface ProofStep {
  stepNumber: number
  description: string
  evidenceIds: string[]
  hasEvidence: boolean
  policyReference?: string
  codebookReference?: string
}

interface ProofChain {
  chainId: string
  claimElement: string
  status: 'valid' | 'incomplete' | 'unsupported' | 'invalid'
  steps: ProofStep[]
  overallConfidence: number
  gaps: string[]
}

interface EvidenceBoundDiagnosis {
  code: string
  codeType: string
  description: string
  evidenceIds: string[]
  codebookReference: string
  confidence: number
  isSupported: boolean
  unsupportedReason?: string
  isPrimary: boolean
  sequence: number
  proofChain?: ProofChain
}

interface EvidenceBoundProcedure {
  code: string
  codeType: string
  description: string
  evidenceIds: string[]
  codebookReference: string
  payerPolicyReference?: string
  modifiers: string[]
  confidence: number
  isSupported: boolean
  unsupportedReason?: string
  proofChain: ProofChain
}

interface EvidenceBoundClaim {
  claimId: string
  patientId?: string
  encounterId?: string
  diagnoses: EvidenceBoundDiagnosis[]
  procedures: EvidenceBoundProcedure[]
  allEvidenceIds: string[]
  isValid: boolean
  isExportable: boolean
  unsupportedElements: string[]
}

// Mock data demonstrating evidence-bound claim
const mockEvidenceAtoms: Map<string, EvidenceAtom> = new Map([
  ['EV-A1B2C3D4E5F6', {
    evidenceId: 'EV-A1B2C3D4E5F6',
    evidenceType: 'clinical_note',
    documentName: 'Progress Note - Dr. Smith',
    contentExcerpt: 'Patient presents with elevated blood pressure readings of 145/92 on two separate occasions. History of hypertension confirmed. Currently on lisinopril 10mg daily.',
    location: { page: 1, section: 'HPI', lineRange: '15-18' },
    confidence: 0.95,
    citation: '[EV-A1B2C3D4E5F6] Progress Note - Dr. Smith, §HPI, lines 15-18',
  }],
  ['EV-B2C3D4E5F6G7', {
    evidenceId: 'EV-B2C3D4E5F6G7',
    evidenceType: 'clinical_note',
    documentName: 'Progress Note - Dr. Smith',
    contentExcerpt: 'Assessment: Essential hypertension, uncontrolled. Type 2 diabetes mellitus, stable on current regimen.',
    location: { page: 2, section: 'Assessment', lineRange: '45-47' },
    confidence: 0.98,
    citation: '[EV-B2C3D4E5F6G7] Progress Note - Dr. Smith, §Assessment, lines 45-47',
  }],
  ['EV-C3D4E5F6G7H8', {
    evidenceId: 'EV-C3D4E5F6G7H8',
    evidenceType: 'clinical_note',
    documentName: 'Progress Note - Dr. Smith',
    contentExcerpt: 'Plan: Increase lisinopril to 20mg daily. Review HbA1c results. Follow up in 2 weeks.',
    location: { page: 2, section: 'Plan', lineRange: '52-54' },
    confidence: 0.92,
    citation: '[EV-C3D4E5F6G7H8] Progress Note - Dr. Smith, §Plan, lines 52-54',
  }],
  ['EV-D4E5F6G7H8I9', {
    evidenceId: 'EV-D4E5F6G7H8I9',
    evidenceType: 'lab',
    documentName: 'Lab Results',
    contentExcerpt: 'HbA1c: 7.2% (Reference: <5.7% normal, 5.7-6.4% prediabetes, ≥6.5% diabetes)',
    location: { page: 1, section: 'Chemistry', lineRange: '8' },
    confidence: 1.0,
    citation: '[EV-D4E5F6G7H8I9] Lab Results, §Chemistry, line 8',
  }],
])

const mockClaim: EvidenceBoundClaim = {
  claimId: 'CLM-EBG-2024-001',
  patientId: 'PT-12345',
  encounterId: 'ENC-67890',
  diagnoses: [
    {
      code: 'I10',
      codeType: 'ICD10CM',
      description: 'Essential (primary) hypertension',
      evidenceIds: ['EV-A1B2C3D4E5F6', 'EV-B2C3D4E5F6G7'],
      codebookReference: 'ICD-10-CM Guidelines Section I.C.9.a',
      confidence: 0.96,
      isSupported: true,
      isPrimary: true,
      sequence: 1,
      proofChain: {
        chainId: 'PROOF-DX001',
        claimElement: 'ICD-10 I10',
        status: 'valid',
        steps: [
          { stepNumber: 1, description: 'Diagnosis confirmed: Hypertension documented in assessment', evidenceIds: ['EV-B2C3D4E5F6G7'], hasEvidence: true },
          { stepNumber: 2, description: 'Clinical findings support: BP 145/92 on multiple readings', evidenceIds: ['EV-A1B2C3D4E5F6'], hasEvidence: true },
          { stepNumber: 3, description: 'Codebook guidance applied', evidenceIds: [], hasEvidence: true, codebookReference: 'ICD-10-CM Section I.C.9.a' },
        ],
        overallConfidence: 0.96,
        gaps: [],
      },
    },
    {
      code: 'E11.9',
      codeType: 'ICD10CM',
      description: 'Type 2 diabetes mellitus without complications',
      evidenceIds: ['EV-B2C3D4E5F6G7', 'EV-D4E5F6G7H8I9'],
      codebookReference: 'ICD-10-CM Guidelines Section I.C.4.a',
      confidence: 0.94,
      isSupported: true,
      isPrimary: false,
      sequence: 2,
    },
  ],
  procedures: [
    {
      code: '99214',
      codeType: 'CPT',
      description: 'Office visit, established patient, moderate complexity',
      evidenceIds: ['EV-A1B2C3D4E5F6', 'EV-B2C3D4E5F6G7', 'EV-C3D4E5F6G7H8'],
      codebookReference: 'CPT E/M Guidelines - MDM Moderate Complexity',
      payerPolicyReference: 'Medicare: MLN Evaluation and Management Services Guide',
      modifiers: [],
      confidence: 0.91,
      isSupported: true,
      proofChain: {
        chainId: 'PROOF-CPT001',
        claimElement: 'CPT 99214',
        status: 'valid',
        steps: [
          { stepNumber: 1, description: 'Diagnosis confirmed: 2 chronic conditions addressed', evidenceIds: ['EV-B2C3D4E5F6G7'], hasEvidence: true },
          { stepNumber: 2, description: 'Service documented: History, exam, and MDM present', evidenceIds: ['EV-A1B2C3D4E5F6', 'EV-B2C3D4E5F6G7'], hasEvidence: true },
          { stepNumber: 3, description: 'MDM supports moderate complexity: Prescription management', evidenceIds: ['EV-C3D4E5F6G7H8'], hasEvidence: true },
          { stepNumber: 4, description: 'Codebook guidance applied', evidenceIds: [], hasEvidence: true, codebookReference: 'CPT E/M Guidelines' },
          { stepNumber: 5, description: 'Policy compliance verified', evidenceIds: ['EV-A1B2C3D4E5F6'], hasEvidence: true, policyReference: 'Medicare MLN E/M Guide' },
        ],
        overallConfidence: 0.91,
        gaps: [],
      },
    },
  ],
  allEvidenceIds: ['EV-A1B2C3D4E5F6', 'EV-B2C3D4E5F6G7', 'EV-C3D4E5F6G7H8', 'EV-D4E5F6G7H8I9'],
  isValid: true,
  isExportable: true,
  unsupportedElements: [],
}

// Workflow Steps
type WorkflowStep = 'upload' | 'extract' | 'review' | 'export'

export default function ClaimGenerationPage() {
  const [step, setStep] = useState<WorkflowStep>('review') // Start at review for demo
  const [claim, setClaim] = useState<EvidenceBoundClaim | null>(mockClaim)
  const [isProcessing, setIsProcessing] = useState(false)
  
  const handleUpload = useCallback(async (files: FileList) => {
    setIsProcessing(true)
    setStep('extract')
    
    // Simulate processing
    await new Promise(r => setTimeout(r, 3000))
    
    setClaim(mockClaim)
    setStep('review')
    setIsProcessing(false)
  }, [])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background-secondary">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
                <Shield className="w-5 h-5 text-accent-foreground" />
              </div>
              <div>
                <h1 className="font-semibold text-foreground">Insurabridge - Evidence-Bound Claims</h1>
                <p className="text-xs text-foreground-muted">Every code traceable to source documentation</p>
              </div>
            </div>
            
            {/* Workflow indicator */}
            <div className="flex items-center gap-2">
              {(['upload', 'extract', 'review', 'export'] as WorkflowStep[]).map((s, i) => (
                <div key={s} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                    step === s 
                      ? 'bg-accent text-accent-foreground'
                      : i < ['upload', 'extract', 'review', 'export'].indexOf(step)
                        ? 'bg-success text-success-foreground'
                        : 'bg-background-tertiary text-foreground-muted'
                  }`}>
                    {i < ['upload', 'extract', 'review', 'export'].indexOf(step) ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      i + 1
                    )}
                  </div>
                  {i < 3 && (
                    <ChevronRight className="w-4 h-4 text-foreground-muted mx-1" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {/* Upload Step */}
          {step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-2xl mx-auto"
            >
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold text-foreground mb-2">
                  Upload Clinical Documentation
                </h2>
                <p className="text-foreground-secondary">
                  Your documents will be converted to immutable evidence atoms
                </p>
              </div>
              
              <div
                className="border-2 border-dashed border-border rounded-xl p-12 text-center hover:border-accent/50 transition-colors cursor-pointer"
                onClick={() => document.getElementById('file-input')?.click()}
              >
                <Upload className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
                <p className="text-lg text-foreground mb-2">Drop files here or click to upload</p>
                <p className="text-sm text-foreground-muted">PDF, DOCX, or text files</p>
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf,.docx,.txt"
                  multiple
                  className="hidden"
                  onChange={(e) => e.target.files && handleUpload(e.target.files)}
                />
              </div>
              
              <div className="mt-6 p-4 bg-accent/5 border border-accent/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-accent mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Evidence-Bound Processing</p>
                    <p className="text-xs text-foreground-secondary mt-1">
                      Documents are chunked into citation-safe units, hashed for integrity,
                      and stored immutably. Every claim will trace back to these evidence atoms.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Extracting Step */}
          {step === 'extract' && (
            <motion.div
              key="extract"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-2xl mx-auto text-center py-12"
            >
              <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
                <RefreshCw className="w-8 h-8 text-accent animate-spin" />
              </div>
              <h2 className="text-xl font-semibold text-foreground mb-2">
                Extracting Evidence
              </h2>
              <p className="text-foreground-secondary mb-8">
                Creating immutable evidence atoms from your documentation...
              </p>
              
              <div className="space-y-3 text-left max-w-md mx-auto">
                {['Parsing document structure', 'Chunking into citation units', 'Computing integrity hashes', 'Extracting literal facts'].map((task, i) => (
                  <motion.div
                    key={task}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.5 }}
                    className="flex items-center gap-3 p-3 bg-background-secondary rounded-lg"
                  >
                    <Check className="w-4 h-4 text-success" />
                    <span className="text-sm text-foreground">{task}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Review Step */}
          {step === 'review' && claim && (
            <motion.div
              key="review"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Claim header */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold text-foreground">{claim.claimId}</h2>
                    {claim.isValid ? (
                      <span className="badge-success">
                        <Check className="w-3 h-3" />
                        VALIDATED
                      </span>
                    ) : (
                      <span className="badge-danger">
                        <X className="w-3 h-3" />
                        UNSUPPORTED
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-foreground-muted mt-1">
                    {claim.diagnoses.length} diagnoses · {claim.procedures.length} procedures · {claim.allEvidenceIds.length} evidence atoms
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="btn-secondary">
                    <Eye className="w-4 h-4" />
                    View Evidence
                  </button>
                  <button 
                    className={`btn-primary ${!claim.isExportable && 'opacity-50 cursor-not-allowed'}`}
                    disabled={!claim.isExportable}
                  >
                    <Download className="w-4 h-4" />
                    Export Claim
                  </button>
                </div>
              </div>

              {/* Unsupported warning */}
              {claim.unsupportedElements.length > 0 && (
                <UnsupportedWarning elements={claim.unsupportedElements} />
              )}

              {/* Diagnoses */}
              <div className="card">
                <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Diagnosis Codes
                </h3>
                <div className="space-y-3">
                  {claim.diagnoses.map(dx => (
                    <CodeWithEvidence
                      key={dx.code}
                      code={dx.code}
                      codeType={dx.codeType}
                      description={dx.description}
                      evidenceIds={dx.evidenceIds}
                      evidenceMap={mockEvidenceAtoms}
                      codebookReference={dx.codebookReference}
                      confidence={dx.confidence}
                      isSupported={dx.isSupported}
                      unsupportedReason={dx.unsupportedReason}
                    />
                  ))}
                </div>
              </div>

              {/* Procedures */}
              <div className="card">
                <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Procedure Codes
                </h3>
                <div className="space-y-3">
                  {claim.procedures.map(proc => (
                    <CodeWithEvidence
                      key={proc.code}
                      code={proc.code}
                      codeType={proc.codeType}
                      description={proc.description}
                      evidenceIds={proc.evidenceIds}
                      evidenceMap={mockEvidenceAtoms}
                      codebookReference={proc.codebookReference}
                      confidence={proc.confidence}
                      isSupported={proc.isSupported}
                      unsupportedReason={proc.unsupportedReason}
                    />
                  ))}
                </div>
              </div>

              {/* Proof Chains */}
              <div className="card">
                <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Proof Chains
                </h3>
                <div className="space-y-3">
                  {claim.diagnoses
                    .filter(dx => dx.proofChain)
                    .map(dx => (
                      <ProofChainViewer
                        key={dx.proofChain!.chainId}
                        proofChain={dx.proofChain!}
                        evidenceMap={mockEvidenceAtoms}
                      />
                    ))}
                  {claim.procedures.map(proc => (
                    <ProofChainViewer
                      key={proc.proofChain.chainId}
                      proofChain={proc.proofChain}
                      evidenceMap={mockEvidenceAtoms}
                    />
                  ))}
                </div>
              </div>

              {/* Evidence atoms */}
              <div className="card">
                <h3 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Source Evidence ({claim.allEvidenceIds.length} atoms)
                </h3>
                <div className="space-y-2">
                  {claim.allEvidenceIds.map(eid => {
                    const atom = mockEvidenceAtoms.get(eid)
                    if (!atom) return null
                    return (
                      <div key={eid} className="p-3 bg-background-tertiary rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <CitationBadge evidenceId={eid} />
                          <span className="text-xs text-foreground-muted">{atom.evidenceType}</span>
                          <span className="text-xs text-foreground-muted">·</span>
                          <span className="text-xs text-foreground-secondary">{atom.documentName}</span>
                        </div>
                        <p className="text-sm text-foreground line-clamp-2">
                          "{atom.contentExcerpt}"
                        </p>
                        <div className="flex items-center gap-2 mt-2 text-2xs text-foreground-muted">
                          <FileSearch className="w-3 h-3" />
                          {atom.location.section && <span>§{atom.location.section}</span>}
                          {atom.location.page && <span>p.{atom.location.page}</span>}
                          {atom.location.lineRange && <span>lines {atom.location.lineRange}</span>}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* EBG explanation */}
              <div className="p-4 bg-accent/5 border border-accent/20 rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-accent" />
                  <h3 className="font-medium text-foreground">Evidence-Bound Generation</h3>
                </div>
                <p className="text-sm text-foreground-secondary">
                  Every code on this claim is bound to source evidence. Click any citation badge to view 
                  the exact documentation. Codes without evidence cannot be exported. This claim has 
                  complete proof chains for all elements, making it fully auditable and defensible.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}

