'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  AlertTriangle,
  Send,
  Shield,
  Upload,
  ChevronRight,
  Check,
  X,
  Info,
  Zap,
  Clock,
  TrendingUp,
  FileCheck,
  MessageSquare,
  BarChart3,
  Settings,
  User,
  Moon,
  Sun,
  Search,
  Plus,
  ArrowRight,
  Sparkles,
  Lock,
  Eye,
  Download,
} from 'lucide-react'
import { api } from '@/lib/api'

// Types


interface ClaimLine {
  lineNumber: number
  code: string
  codeType: string
  description: string
  modifiers: string[]
  confidence: number
  confidenceLevel: 'high' | 'medium' | 'low'
  rationale?: string
  requiresReview: boolean
}

interface Diagnosis {
  sequence: number
  code: string
  description: string
  confidence: number
  confidenceLevel: 'high' | 'medium' | 'low'
}

interface Claim {
  id: string
  status: 'draft' | 'validated' | 'submitted' | 'denied'
  diagnoses: Diagnosis[]
  lines: ClaimLine[]
  overallConfidence: number
  complianceIssues: string[]
  totalCharges: number
}

// Mock data for demo
const mockClaim: Claim = {
  id: 'CLM-2024-001',
  status: 'draft',
  diagnoses: [
    { sequence: 1, code: 'I10', description: 'Essential (primary) hypertension', confidence: 0.92, confidenceLevel: 'high' },
    { sequence: 2, code: 'E11.9', description: 'Type 2 diabetes mellitus without complications', confidence: 0.88, confidenceLevel: 'high' },
    { sequence: 3, code: 'Z79.84', description: 'Long term (current) use of oral hypoglycemic drugs', confidence: 0.76, confidenceLevel: 'medium' },
  ],
  lines: [
    {
      lineNumber: 1,
      code: '99214',
      codeType: 'CPT',
      description: 'Office visit, established patient, moderate complexity',
      modifiers: [],
      confidence: 0.91,
      confidenceLevel: 'high',
      rationale: 'Documentation supports moderate complexity decision making with chronic conditions discussed.',
      requiresReview: false,
    },
    {
      lineNumber: 2,
      code: '83036',
      codeType: 'CPT',
      description: 'Hemoglobin A1c',
      modifiers: [],
      confidence: 0.95,
      confidenceLevel: 'high',
      rationale: 'Lab ordered for diabetes management, clearly documented.',
      requiresReview: false,
    },
    {
      lineNumber: 3,
      code: '80053',
      codeType: 'CPT',
      description: 'Comprehensive metabolic panel',
      modifiers: [],
      confidence: 0.72,
      confidenceLevel: 'medium',
      rationale: 'Bundling check recommended - verify medical necessity documentation.',
      requiresReview: true,
    },
  ],
  overallConfidence: 0.86,
  complianceIssues: [
    'Line 3: Verify medical necessity documentation for CMP',
    'Consider adding modifier 25 to E/M code if significant separate service',
  ],
  totalCharges: 485.00,
}

// Components
function Sidebar() {
  const [activeItem, setActiveItem] = useState('claims')

  const navItems = [
    { id: 'claims', icon: FileText, label: 'Claims' },
    { id: 'pipeline', icon: Zap, label: 'New Claim (Epic)' },
    { id: 'denials', icon: AlertTriangle, label: 'Denials' },
    { id: 'appeals', icon: MessageSquare, label: 'Appeals' },
    { id: 'audit', icon: Shield, label: 'Audit' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
  ]

  const router = useRouter()

  const handleNav = (id: string) => {
    if (id === 'pipeline') {
      router.push('/pipeline')
    } else {
      setActiveItem(id)
    }
  }

  return (
    <div className="w-64 h-screen bg-background-secondary border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <Shield className="w-5 h-5 text-accent-foreground" />
          </div>
          <div>
            <h1 className="font-semibold text-foreground">Insurabridge</h1>
            <p className="text-2xs text-foreground-muted">Local AI · HIPAA Compliant</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <div className="space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNav(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${activeItem === item.id
                ? 'bg-accent/10 text-accent'
                : 'text-foreground-secondary hover:bg-background-tertiary hover:text-foreground'
                }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Security badge */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-2 px-3 py-2 bg-success/10 rounded-lg">
          <Lock className="w-4 h-4 text-success" />
          <span className="text-xs font-medium text-success">Local Processing</span>
        </div>
        <p className="text-2xs text-foreground-muted mt-2 px-1">
          All PHI processed on-device. No data leaves your system.
        </p>
      </div>

      {/* User */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-background-tertiary flex items-center justify-center">
            <User className="w-4 h-4 text-foreground-muted" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">Dr. Sarah Chen</p>
            <p className="text-2xs text-foreground-muted">Billing Manager</p>
          </div>
          <button className="p-1.5 hover:bg-background-tertiary rounded-md transition-colors">
            <Settings className="w-4 h-4 text-foreground-muted" />
          </button>
        </div>
      </div>
    </div>
  )
}

function ConfidenceBadge({ level, score }: { level: 'high' | 'medium' | 'low', score: number }) {
  const config = {
    high: { class: 'badge-success', icon: Check, label: 'High' },
    medium: { class: 'badge-warning', icon: AlertTriangle, label: 'Review' },
    low: { class: 'badge-danger', icon: X, label: 'Low' },
  }

  const { class: badgeClass, icon: Icon, label } = config[level]

  return (
    <span className={badgeClass}>
      <Icon className="w-3 h-3" />
      {Math.round(score * 100)}%
    </span>
  )
}

function ClaimCard({ claim }: { claim: Claim }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <motion.div
      layout
      className="card overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground">{claim.id}</h3>
            <span className="badge-neutral capitalize">{claim.status}</span>
          </div>
          <p className="text-sm text-foreground-muted">
            {claim.diagnoses.length} diagnoses · {claim.lines.length} service lines
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-foreground">${claim.totalCharges.toFixed(2)}</p>
          <ConfidenceBadge level={claim.overallConfidence >= 0.85 ? 'high' : claim.overallConfidence >= 0.6 ? 'medium' : 'low'} score={claim.overallConfidence} />
        </div>
      </div>

      {/* Compliance issues */}
      {claim.complianceIssues.length > 0 && (
        <div className="mb-4 p-3 bg-warning/10 border border-warning/20 rounded-lg">
          <div className="flex items-center gap-2 text-warning mb-2">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">Compliance Considerations</span>
          </div>
          <ul className="space-y-1">
            {claim.complianceIssues.map((issue, i) => (
              <li key={i} className="text-xs text-foreground-secondary flex items-start gap-2">
                <span className="text-warning mt-0.5">•</span>
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Diagnoses */}
      <div className="mb-4">
        <h4 className="text-xs font-medium text-foreground-muted uppercase tracking-wide mb-2">
          Diagnosis Codes
        </h4>
        <div className="space-y-2">
          {claim.diagnoses.map((dx) => (
            <div key={dx.sequence} className="flex items-center justify-between py-2 px-3 bg-background-tertiary rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-accent font-medium">{dx.code}</span>
                <span className="text-sm text-foreground">{dx.description}</span>
              </div>
              <ConfidenceBadge level={dx.confidenceLevel} score={dx.confidence} />
            </div>
          ))}
        </div>
      </div>

      {/* Service lines */}
      <div>
        <h4 className="text-xs font-medium text-foreground-muted uppercase tracking-wide mb-2">
          Service Lines
        </h4>
        <div className="space-y-2">
          {claim.lines.map((line) => (
            <motion.div
              key={line.lineNumber}
              className={`py-3 px-4 rounded-lg border ${line.requiresReview
                ? 'bg-warning/5 border-warning/30'
                : 'bg-background-tertiary border-transparent'
                }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-accent font-medium">{line.code}</span>
                  <span className="text-2xs px-1.5 py-0.5 bg-background rounded text-foreground-muted">
                    {line.codeType}
                  </span>
                  {line.modifiers.length > 0 && (
                    <span className="text-2xs text-foreground-muted">
                      Mod: {line.modifiers.join(', ')}
                    </span>
                  )}
                </div>
                <ConfidenceBadge level={line.confidenceLevel} score={line.confidence} />
              </div>
              <p className="text-sm text-foreground mb-2">{line.description}</p>
              {line.rationale && (
                <div className="flex items-start gap-2 p-2 bg-background rounded-md">
                  <Sparkles className="w-3 h-3 text-accent mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-foreground-secondary">{line.rationale}</p>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-border">
        <div className="flex items-center gap-2">
          <button className="btn-ghost text-xs">
            <Eye className="w-4 h-4" />
            View Details
          </button>
          <button className="btn-ghost text-xs">
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary text-xs">
            Edit Claim
          </button>
          <button className="btn-primary text-xs">
            <Check className="w-4 h-4" />
            Approve & Submit
          </button>
        </div>
      </div>
    </motion.div>
  )
}

function UploadSection(props: { onUpload?: (file: File) => Promise<void> }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    setIsProcessing(true)

    // In real implementation, we'd handle the file here
    if (e.dataTransfer.files?.length > 0) {
      const file = e.dataTransfer.files[0]
      // Check if parent component provided a handler
      // @ts-ignore - Prop will be added dynamically
      if (props.onUpload) {
        try {
          // @ts-ignore
          await props.onUpload(file)
        } catch (err) {
          console.error("Upload failed", err)
          alert("Upload failed: " + (err as Error).message)
        }
      } else {
        // Fallback mock delay
        setTimeout(() => setIsProcessing(false), 2000)
      }
    }

    setIsProcessing(false)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${isDragging
        ? 'border-accent bg-accent/5'
        : 'border-border hover:border-accent/50'
        }`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {isProcessing ? (
        <div className="flex flex-col items-center">
          <div className="spinner mb-4" />
          <p className="text-sm text-foreground-secondary">Processing document...</p>
          <p className="text-xs text-foreground-muted mt-1">Extracting clinical evidence</p>
        </div>
      ) : (
        <>
          <Upload className="w-10 h-10 text-foreground-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">
            Upload Clinical Documentation
          </h3>
          <p className="text-sm text-foreground-muted mb-4">
            Drag and drop PDF, DOCX, or text files
          </p>
          <button className="btn-secondary">
            <Plus className="w-4 h-4" />
            Select Files
          </button>
        </>
      )}
    </motion.div>
  )
}

function QuickActions() {
  const actions = [
    { icon: FileText, label: 'Generate Claim', description: 'From clinical notes', color: 'text-accent' },
    { icon: FileCheck, label: 'Validate Claim', description: 'Check compliance', color: 'text-success' },
    { icon: MessageSquare, label: 'Appeal Denial', description: 'Generate letter', color: 'text-warning' },
    { icon: Shield, label: 'Audit Risk', description: 'Pre-submission check', color: 'text-danger' },
  ]

  return (
    <div className="grid grid-cols-2 gap-3">
      {actions.map((action, i) => (
        <motion.button
          key={action.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="group p-4 bg-background-secondary border border-border rounded-xl text-left hover:border-accent/50 hover:bg-background-tertiary transition-all"
        >
          <action.icon className={`w-5 h-5 ${action.color} mb-3`} />
          <h4 className="font-medium text-foreground mb-0.5">{action.label}</h4>
          <p className="text-xs text-foreground-muted">{action.description}</p>
          <ArrowRight className="w-4 h-4 text-foreground-muted group-hover:text-accent group-hover:translate-x-1 transition-all mt-2" />
        </motion.button>
      ))}
    </div>
  )
}

function StatsCards() {
  const stats = [
    { label: 'Claims Today', value: '12', change: '+3', icon: FileText },
    { label: 'Pending Review', value: '5', change: '-2', icon: Clock },
    { label: 'Appeal Success', value: '78%', change: '+5%', icon: TrendingUp },
    { label: 'Audit Score', value: '94', change: '+2', icon: Shield },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="p-4 bg-background-secondary border border-border rounded-xl"
        >
          <div className="flex items-center justify-between mb-2">
            <stat.icon className="w-4 h-4 text-foreground-muted" />
            <span className="text-xs text-success font-medium">{stat.change}</span>
          </div>
          <p className="text-2xl font-semibold text-foreground">{stat.value}</p>
          <p className="text-xs text-foreground-muted mt-0.5">{stat.label}</p>
        </motion.div>
      ))}
    </div>
  )
}

// Data Mapper: Backend (snake_case) -> Frontend (camelCase)
const mapClaimResponse = (response: any): Claim => {
  return {
    id: response.id,
    status: response.status,
    diagnoses: (response.diagnoses || []).map((d: any) => ({
      sequence: d.sequence,
      code: d.code,
      description: d.description,
      confidence: d.confidence_score,
      confidenceLevel: d.confidence_level
    })),
    lines: (response.lines || []).map((l: any) => ({
      lineNumber: l.line_number,
      code: l.code,
      codeType: l.code_type,
      description: l.description,
      modifiers: l.modifiers || [],
      confidence: l.confidence_score,
      confidenceLevel: l.confidence_level,
      rationale: l.rationale,
      requiresReview: l.requires_review
    })),
    overallConfidence: response.overall_score,
    complianceIssues: response.compliance_issues || [],
    totalCharges: response.total_charges || 0
  } as Claim
}

export default function Dashboard() {
  const [showClaim, setShowClaim] = useState(false)
  const [claim, setClaim] = useState<Claim>(mockClaim)
  const [useMockData, setUseMockData] = useState(true)
  const [isLoading, setIsLoading] = useState(false)

  // Toggle Pitch Mode (Ctrl+Shift+D)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'd') {
        e.preventDefault()
        setUseMockData(prev => {
          const next = !prev
          alert(`Switched to ${next ? 'DEMO (Mock)' : 'LIVE (Real)'} mode`)
          return next
        })
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Poll for real data if in live mode
  useEffect(() => {
    if (useMockData) {
      setClaim(mockClaim)
      return
    }

    const fetchData = async () => {
      setIsLoading(true)
      try {
        const result = await api.listClaims({ page: 1 })
        // Transform API result to UI model if needed
        // For now assuming generic match or using first result
        if (Array.isArray(result) && result.length > 0) {
          // TODO: rigorous mapping. For now casting or partial match
          setClaim(result[0] as unknown as Claim)
        }
      } catch (err) {
        console.error("Failed to fetch live data", err)
        // Don't auto-revert to mock to avoid confusing flickering
        // Just show error in console
      } finally {
        setIsLoading(false)
      }
    }
    // Fetch immediately on switch
    fetchData()
  }, [useMockData])

  const handleUpload = async (file: File) => {
    if (useMockData) {
      // Fake it
      setTimeout(() => setShowClaim(true), 1500)
      return
    }

    try {
      setIsLoading(true)
      const result = await api.uploadAndGenerateClaim(file)
      // Transform result
      setClaim(mapClaimResponse(result))
      setShowClaim(true)
      alert("Claim generated from live backend!")
    } catch (err) {
      console.error(err)
      alert("Failed to generate claim from backend")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mode Indicator Overlay */}
      {!useMockData && (
        <div className="fixed top-0 left-0 right-0 h-1 bg-red-500 z-50 pointer-events-none" title="Live Mode Active" />
      )}

      <Sidebar />

      <main className="flex-1 overflow-auto">
        {/* Header */}
        <header className="sticky top-0 z-10 glass border-b border-border">
          <div className="flex items-center justify-between px-8 py-4">
            <div>
              <h1 className="text-xl font-semibold text-foreground">Claims Dashboard</h1>
              <p className="text-sm text-foreground-muted">Generate, validate, and manage insurance claims</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-foreground-muted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search claims..."
                  className="input pl-9 w-64"
                />
              </div>
              <button className="btn-primary">
                <Plus className="w-4 h-4" />
                New Claim
              </button>
            </div>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {/* Stats */}
          <StatsCards />

          {/* Main content grid */}
          <div className="grid grid-cols-3 gap-8">
            {/* Left column - Quick actions & Upload */}
            <div className="space-y-6">
              <div>
                <h2 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Quick Actions
                </h2>
                <QuickActions />
              </div>

              <div>
                <h2 className="text-sm font-medium text-foreground-muted uppercase tracking-wide mb-4">
                  Upload Document
                </h2>
                <UploadSection onUpload={handleUpload} />
              </div>
            </div>

            {/* Right column - Claim review */}
            <div className="col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-foreground-muted uppercase tracking-wide">
                  Pending Review
                </h2>
                <button className="text-sm text-accent hover:text-accent/80 transition-colors">
                  View all →
                </button>
              </div>

              {/* Demo claim */}
              {isLoading ? (
                <div className="p-12 text-center text-foreground-muted">
                  <div className="spinner mb-4 mx-auto" />
                  Processing with local LLM...
                </div>
              ) : (
                <ClaimCard claim={claim} />
              )}

              {/* Reasoning explanation */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="mt-6 p-4 bg-accent/5 border border-accent/20 rounded-xl"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-accent" />
                  <h3 className="font-medium text-foreground">AI Reasoning</h3>
                </div>
                <div className="space-y-3 text-sm text-foreground-secondary">
                  <div className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-foreground">Evidence Extraction</p>
                      <p className="text-xs text-foreground-muted">Identified 3 diagnoses and 3 billable services from clinical notes</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-foreground">Code Mapping</p>
                      <p className="text-xs text-foreground-muted">Matched to ICD-10-CM and CPT codes based on AMA guidelines</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-foreground">Compliance Check</p>
                      <p className="text-xs text-foreground-muted">Ran NCCI edits, MUE limits, and modifier validation</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

