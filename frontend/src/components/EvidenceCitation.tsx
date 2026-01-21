'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Link,
  AlertTriangle,
  Check,
  X,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Quote,
  BookOpen,
  FileSearch,
} from 'lucide-react'

// Types
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

// Citation Badge Component
export function CitationBadge({
  evidenceId,
  onClick,
  variant = 'default',
}: {
  evidenceId: string
  onClick?: () => void
  variant?: 'default' | 'unsupported' | 'warning'
}) {
  const variantStyles = {
    default: 'bg-accent/20 text-accent border-accent/30 hover:bg-accent/30',
    unsupported: 'bg-danger/20 text-danger border-danger/30',
    warning: 'bg-warning/20 text-warning border-warning/30',
  }

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-2xs font-mono rounded border transition-colors ${variantStyles[variant]}`}
      title={`View evidence: ${evidenceId}`}
    >
      <Link className="w-2.5 h-2.5" />
      {evidenceId}
    </button>
  )
}

// Evidence Popover Component
export function EvidencePopover({
  evidence,
  onClose,
}: {
  evidence: EvidenceAtom
  onClose: () => void
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 5 }}
      className="absolute z-50 w-96 bg-background-secondary border border-border rounded-lg shadow-xl overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-background-tertiary">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent" />
          <span className="font-mono text-sm text-accent">{evidence.evidenceId}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-background rounded-md transition-colors"
        >
          <X className="w-4 h-4 text-foreground-muted" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Source */}
        <div>
          <div className="text-2xs uppercase tracking-wide text-foreground-muted mb-1">
            Source
          </div>
          <div className="flex items-center gap-2">
            <FileSearch className="w-4 h-4 text-foreground-muted" />
            <span className="text-sm text-foreground">{evidence.documentName}</span>
          </div>
          {evidence.location.section && (
            <div className="text-xs text-foreground-secondary mt-1">
              Section: {evidence.location.section}
              {evidence.location.page && ` | Page ${evidence.location.page}`}
              {evidence.location.lineRange && ` | Lines ${evidence.location.lineRange}`}
            </div>
          )}
        </div>

        {/* Excerpt */}
        <div>
          <div className="text-2xs uppercase tracking-wide text-foreground-muted mb-1">
            Evidence Content
          </div>
          <div className="relative p-3 bg-background rounded-md border border-border">
            <Quote className="absolute -top-2 -left-2 w-4 h-4 text-accent/50" />
            <p className="text-sm text-foreground leading-relaxed">
              {evidence.contentExcerpt}
            </p>
          </div>
        </div>

        {/* Confidence */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <span className="text-xs text-foreground-muted">Extraction Confidence</span>
          <span className={`text-sm font-medium ${
            evidence.confidence >= 0.9 ? 'text-success' :
            evidence.confidence >= 0.7 ? 'text-warning' :
            'text-danger'
          }`}>
            {Math.round(evidence.confidence * 100)}%
          </span>
        </div>
      </div>
    </motion.div>
  )
}

// Inline Citation Component (for use within text)
export function InlineCitation({
  evidenceId,
  evidence,
}: {
  evidenceId: string
  evidence?: EvidenceAtom
}) {
  const [showPopover, setShowPopover] = useState(false)

  return (
    <span className="relative inline-block">
      <CitationBadge
        evidenceId={evidenceId}
        onClick={() => setShowPopover(!showPopover)}
      />
      <AnimatePresence>
        {showPopover && evidence && (
          <div className="absolute left-0 top-full mt-1">
            <EvidencePopover
              evidence={evidence}
              onClose={() => setShowPopover(false)}
            />
          </div>
        )}
      </AnimatePresence>
    </span>
  )
}

// Proof Chain Visualization
export function ProofChainViewer({
  proofChain,
  evidenceMap,
}: {
  proofChain: ProofChain
  evidenceMap: Map<string, EvidenceAtom>
}) {
  const [expanded, setExpanded] = useState(false)

  const statusColors = {
    valid: 'text-success bg-success/10 border-success/30',
    incomplete: 'text-warning bg-warning/10 border-warning/30',
    unsupported: 'text-danger bg-danger/10 border-danger/30',
    invalid: 'text-danger bg-danger/10 border-danger/30',
  }

  const statusIcons = {
    valid: Check,
    incomplete: AlertTriangle,
    unsupported: X,
    invalid: X,
  }

  const StatusIcon = statusIcons[proofChain.status]

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-background-tertiary transition-colors"
      >
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-accent" />
          <div className="text-left">
            <div className="font-medium text-foreground">
              Proof Chain: {proofChain.claimElement}
            </div>
            <div className="text-xs text-foreground-muted">
              {proofChain.steps.length} steps · {proofChain.steps.filter(s => s.hasEvidence).length} with evidence
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${statusColors[proofChain.status]}`}>
            <StatusIcon className="w-3 h-3" />
            {proofChain.status.toUpperCase()}
          </span>
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-foreground-muted" />
          ) : (
            <ChevronRight className="w-4 h-4 text-foreground-muted" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {/* Steps */}
              <div className="space-y-2">
                {proofChain.steps.map((step, index) => (
                  <div
                    key={step.stepNumber}
                    className={`relative pl-6 py-2 ${
                      index < proofChain.steps.length - 1 ? 'border-l-2 border-border ml-2' : ''
                    }`}
                  >
                    {/* Step indicator */}
                    <div className={`absolute left-0 top-2 w-4 h-4 rounded-full flex items-center justify-center ${
                      step.hasEvidence
                        ? 'bg-success text-success-foreground'
                        : 'bg-danger text-danger-foreground'
                    }`}>
                      {step.hasEvidence ? (
                        <Check className="w-2.5 h-2.5" />
                      ) : (
                        <X className="w-2.5 h-2.5" />
                      )}
                    </div>

                    {/* Step content */}
                    <div className="ml-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-foreground-muted">
                          Step {step.stepNumber}
                        </span>
                        {!step.hasEvidence && (
                          <span className="badge-danger">UNSUPPORTED</span>
                        )}
                      </div>
                      <p className="text-sm text-foreground mt-1">
                        {step.description}
                      </p>

                      {/* Evidence citations */}
                      {step.evidenceIds.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {step.evidenceIds.map(eid => (
                            <CitationBadge key={eid} evidenceId={eid} />
                          ))}
                        </div>
                      )}

                      {/* References */}
                      {(step.policyReference || step.codebookReference) && (
                        <div className="flex flex-wrap gap-2 mt-2 text-xs text-foreground-secondary">
                          {step.policyReference && (
                            <span className="flex items-center gap-1">
                              <ExternalLink className="w-3 h-3" />
                              {step.policyReference}
                            </span>
                          )}
                          {step.codebookReference && (
                            <span className="flex items-center gap-1">
                              <BookOpen className="w-3 h-3" />
                              {step.codebookReference}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Gaps */}
              {proofChain.gaps.length > 0 && (
                <div className="p-3 bg-danger/10 border border-danger/30 rounded-lg">
                  <div className="flex items-center gap-2 text-danger mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm font-medium">Documentation Gaps</span>
                  </div>
                  <ul className="space-y-1">
                    {proofChain.gaps.map((gap, i) => (
                      <li key={i} className="text-xs text-foreground-secondary flex items-start gap-2">
                        <span className="text-danger mt-0.5">•</span>
                        {gap}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confidence */}
              <div className="flex items-center justify-between pt-3 border-t border-border">
                <span className="text-sm text-foreground-muted">Overall Confidence</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-background-tertiary rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        proofChain.overallConfidence >= 0.8 ? 'bg-success' :
                        proofChain.overallConfidence >= 0.5 ? 'bg-warning' :
                        'bg-danger'
                      }`}
                      style={{ width: `${proofChain.overallConfidence * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-foreground">
                    {Math.round(proofChain.overallConfidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Unsupported Warning Banner
export function UnsupportedWarning({
  elements,
  onResolve,
}: {
  elements: string[]
  onResolve?: () => void
}) {
  if (elements.length === 0) return null

  return (
    <div className="p-4 bg-danger/10 border border-danger/30 rounded-lg">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-danger mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="font-medium text-danger mb-2">
            Unsupported Elements Detected
          </h4>
          <p className="text-sm text-foreground-secondary mb-3">
            The following elements cannot be exported due to missing evidence:
          </p>
          <ul className="space-y-1 mb-4">
            {elements.map((el, i) => (
              <li key={i} className="text-sm text-foreground flex items-start gap-2">
                <X className="w-4 h-4 text-danger mt-0.5 flex-shrink-0" />
                {el}
              </li>
            ))}
          </ul>
          <div className="flex items-center gap-2">
            <span className="text-xs text-foreground-muted">
              Add supporting documentation to resolve these issues.
            </span>
            {onResolve && (
              <button
                onClick={onResolve}
                className="btn-secondary text-xs"
              >
                Add Evidence
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Code with Evidence Display
export function CodeWithEvidence({
  code,
  codeType,
  description,
  evidenceIds,
  evidenceMap,
  codebookReference,
  confidence,
  isSupported,
  unsupportedReason,
}: {
  code: string
  codeType: string
  description: string
  evidenceIds: string[]
  evidenceMap: Map<string, EvidenceAtom>
  codebookReference?: string
  confidence: number
  isSupported: boolean
  unsupportedReason?: string
}) {
  const [showEvidence, setShowEvidence] = useState(false)

  return (
    <div className={`p-4 rounded-lg border ${
      isSupported
        ? 'bg-background-tertiary border-transparent'
        : 'bg-danger/5 border-danger/30'
    }`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm font-medium text-accent">{code}</span>
          <span className="text-2xs px-1.5 py-0.5 bg-background rounded text-foreground-muted">
            {codeType}
          </span>
          {!isSupported && (
            <span className="badge-danger">UNSUPPORTED</span>
          )}
        </div>
        <span className={`text-sm font-medium ${
          confidence >= 0.85 ? 'text-success' :
          confidence >= 0.6 ? 'text-warning' :
          'text-danger'
        }`}>
          {Math.round(confidence * 100)}%
        </span>
      </div>

      <p className="text-sm text-foreground mb-3">{description}</p>

      {unsupportedReason && (
        <div className="flex items-center gap-2 p-2 bg-danger/10 rounded text-xs text-danger mb-3">
          <AlertTriangle className="w-3 h-3" />
          {unsupportedReason}
        </div>
      )}

      {/* Evidence section */}
      <div>
        <button
          onClick={() => setShowEvidence(!showEvidence)}
          className="flex items-center gap-2 text-xs text-foreground-secondary hover:text-foreground transition-colors"
        >
          {showEvidence ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          <span>{evidenceIds.length} evidence citation{evidenceIds.length !== 1 ? 's' : ''}</span>
        </button>

        <AnimatePresence>
          {showEvidence && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-2 space-y-2 overflow-hidden"
            >
              {evidenceIds.map(eid => {
                const evidence = evidenceMap.get(eid)
                return (
                  <div key={eid} className="p-2 bg-background rounded border border-border">
                    <div className="flex items-center gap-2 mb-1">
                      <CitationBadge evidenceId={eid} />
                      {evidence && (
                        <span className="text-xs text-foreground-muted">
                          {evidence.documentName}
                        </span>
                      )}
                    </div>
                    {evidence && (
                      <p className="text-xs text-foreground-secondary line-clamp-2">
                        "{evidence.contentExcerpt.substring(0, 150)}..."
                      </p>
                    )}
                  </div>
                )
              })}

              {codebookReference && (
                <div className="flex items-center gap-2 text-xs text-foreground-secondary">
                  <BookOpen className="w-3 h-3" />
                  <span>Codebook: {codebookReference}</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

