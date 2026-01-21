"use client";

import React, { useState, useEffect } from "react";
import {
  NarrativeSection,
  EvidenceLibrary,
  EvidenceAtom as EvidenceAtomType,
} from "@/components/CitationViewer";

interface PatientData {
  id: string;
  name: string;
  birthDate?: string;
  gender?: string;
  address?: string;
}

interface EvidenceAtom {
  evidence_id: string;
  evidence_type: string;
  content_excerpt: string;
  source_system: string;
  confidence: number;
}

interface ClaimField {
  field_name: string;
  value: string;
  evidence_ids: string[];
  confidence: number;
  status: string;
}

interface ClaimDiagnosis {
  code: string;
  display: string;
  evidence_ids: string[];
  confidence: number;
  is_primary: boolean;
  has_evidence?: boolean;
  evidence_status?: "verified" | "unsupported" | "partial";
  confidence_level?: "high" | "medium" | "low";
}

interface ClaimLine {
  line_number: number;
  code: string;
  code_type: string;
  description: string;
  charge_amount: number;
  confidence: number;
  supporting_evidence: string[];
  rationale: string;
  has_evidence?: boolean;
  evidence_status?: "verified" | "unsupported" | "partial";
  confidence_level?: "high" | "medium" | "low";
  requires_review?: boolean;
}

interface GeneratedClaim {
  claim_id: string;
  status: string;
  patient: Record<string, ClaimField>;
  diagnoses: ClaimDiagnosis[];
  lines: ClaimLine[];
  total_charges: number;
  validation_errors: string[];
  validation_warnings: string[];
  can_submit: boolean;
  all_evidence_ids: string[];
}

interface CitedSection {
  section_title: string;
  content: string;
  evidence_ids: string[];
}

interface NarrativeClaim {
  claim_id: string;
  title: string;
  summary: string;
  patient_section: CitedSection;
  diagnoses_section: CitedSection;
  procedures_section: CitedSection;
  medical_necessity_section: CitedSection;
  billing_summary_section: CitedSection;
  evidence_atoms: EvidenceAtom[];
  total_charges: number;
  status: string;
  requires_review: boolean;
  review_reasons: string[];
  generated_at: string;
  llm_model: string;
}

interface DataPreview {
  conditions: number;
  procedures: number;
  medications: number;
  observations: number;
  encounters: number;
  allergies: number;
  immunizations: number;
  diagnosticReports: number;
  coverages: number;
  errors: string[];
}

interface PipelineState {
  step: number;
  epicConnected: boolean;
  patientData: PatientData | null;
  dataPreview: DataPreview | null;
  evidenceAtoms: EvidenceAtom[];
  claim: GeneratedClaim | null;
  narrativeClaim: NarrativeClaim | null;
  showNarrative: boolean;
  loading: boolean;
  error: string | null;
}

// Epic Sandbox Test Patients - VERIFIED WORKING CREDENTIALS
const TEST_PATIENTS = [
  { username: "fhircamila", password: "epicepic1", name: "Camila Lopez", description: "✅ Verified - Adult female patient", hasRichData: true },
  { username: "fhirjason", password: "epicepic1", name: "Jason Argonaut", description: "✅ Verified - Adult male patient", hasRichData: true },
  { username: "fhirderrick", password: "epicepic1", name: "Derrick Lin", description: "✅ Verified - Adult male patient", hasRichData: true },
  { username: "FHIRBRADY", password: "EPICEPIC1", name: "Brady Johnson", description: "Pediatric patient", hasRichData: false },
  { username: "FHIRTERRY", password: "EPICEPIC1", name: "Terry Baker", description: "Adult patient", hasRichData: false },
  { username: "FHIRAMY", password: "EPICEPIC1", name: "Amy Taylor", description: "Adult female patient", hasRichData: false },
];

export default function PipelinePage() {
  const [state, setState] = useState<PipelineState>({
    step: 0,
    epicConnected: false,
    patientData: null,
    dataPreview: null,
    evidenceAtoms: [],
    claim: null,
    narrativeClaim: null,
    showNarrative: false,
    loading: false,
    error: null,
  });
  const [showTestPatients, setShowTestPatients] = useState(false);
  const [showDataPreview, setShowDataPreview] = useState(false);
  const [showDemoMode, setShowDemoMode] = useState(false);
  const [demoPatients, setDemoPatients] = useState<any[]>([]);
  const [selectedDemoPatient, setSelectedDemoPatient] = useState<string | null>(null);

  const EPIC_BRIDGE_URL = "http://localhost:3000";
  const BACKEND_URL = "http://localhost:8001";

  // Check Epic connection on load and fetch demo patients
  useEffect(() => {
    checkEpicConnection();
    fetchDemoPatients();
    
    // Check if we're returning from Epic authorization
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
      // Clear the auth parameter from URL
      window.history.replaceState({}, '', '/pipeline');
      // Check connection status after a short delay
      setTimeout(() => {
        checkEpicConnection();
      }, 500);
      // If this is a popup window, close it after auth completes
      if (window.opener) {
        setTimeout(() => {
          window.close();
        }, 1500);
      }
    }
  }, []);

  const checkEpicConnection = async () => {
    try {
      const response = await fetch(`${EPIC_BRIDGE_URL}/status`, { credentials: "include" });
      const data = await response.json();
      setState((prev) => ({
        ...prev,
        epicConnected: data.authenticated,
        step: data.authenticated ? 1 : 0,
      }));
    } catch {
      setState((prev) => ({ ...prev, epicConnected: false, step: 0 }));
    }
  };

  const connectToEpic = () => {
    // Open in popup window and monitor for completion
    const popup = window.open(
      `${EPIC_BRIDGE_URL}/auth/authorize?returnTo=${encodeURIComponent(window.location.origin + '/pipeline?auth=success')}`,
      "Epic Authorization",
      "width=800,height=600"
    );
    
    // Poll for popup closure or check connection status
    const checkInterval = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkInterval);
        // Check connection status after popup closes
        setTimeout(() => {
          checkEpicConnection();
        }, 1000);
      }
    }, 500);
    
    // Also listen for focus event (user might have manually closed)
    window.addEventListener('focus', () => {
      setTimeout(() => {
        checkEpicConnection();
      }, 500);
    }, { once: true });
  };

  const logoutFromEpic = async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      await fetch(`${EPIC_BRIDGE_URL}/auth/logout`, { credentials: "include" });
      setState({
        step: 0,
        epicConnected: false,
        patientData: null,
        dataPreview: null,
        evidenceAtoms: [],
        claim: null,
        narrativeClaim: null,
        showNarrative: false,
        loading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: "Failed to logout",
      }));
    }
  };

  const switchPatient = () => {
    // Clear current state and open Epic login
    setState({
      step: 0,
      epicConnected: false,
      patientData: null,
      dataPreview: null,
      evidenceAtoms: [],
      claim: null,
      narrativeClaim: null,
      showNarrative: false,
      loading: false,
      error: null,
    });
    // First logout, then redirect to authorize
    fetch(`${EPIC_BRIDGE_URL}/auth/logout`, { credentials: "include" })
      .then(() => {
        window.open(`${EPIC_BRIDGE_URL}/auth/authorize`, "_blank");
      })
      .catch(() => {
        window.open(`${EPIC_BRIDGE_URL}/auth/authorize`, "_blank");
      });
  };

  const fetchPatientData = async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await fetch(`${EPIC_BRIDGE_URL}/fhir/patient`, { credentials: "include" });
      
      if (!response.ok) {
        throw new Error("Failed to fetch patient. Please authenticate first.");
      }
      
      const data = await response.json();
      
      const patient: PatientData = {
        id: data.id,
        name: data.name?.[0]?.text || `${data.name?.[0]?.given?.join(" ")} ${data.name?.[0]?.family}`,
        birthDate: data.birthDate,
        gender: data.gender,
        address: data.address?.[0]?.text,
      };
      
      setState((prev) => ({
        ...prev,
        patientData: patient,
        step: 2,
        loading: false,
      }));

      // Also fetch data preview in background
      fetchDataPreview();
    } catch (err: unknown) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to fetch patient",
        loading: false,
      }));
    }
  };

  const fetchDemoPatients = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/demo/patients`);
      if (response.ok) {
        const data = await response.json();
        setDemoPatients(data.patients || []);
      }
    } catch {
      // Demo patients not available
    }
  };

  const loadDemoPatient = async (patientId: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    setSelectedDemoPatient(patientId);

    try {
      // Fetch demo patient data
      const patientResponse = await fetch(`${BACKEND_URL}/demo/patient/${patientId}`);
      if (!patientResponse.ok) throw new Error("Failed to load demo patient");
      const patientData = await patientResponse.json();

      // Fetch all data for preview
      const allDataResponse = await fetch(`${BACKEND_URL}/demo/patient/${patientId}/all`);
      const allData = await allDataResponse.json();

      const patient: PatientData = {
        id: patientData.id,
        name: patientData.name?.[0]?.text || "Demo Patient",
        birthDate: patientData.birthDate,
        gender: patientData.gender,
        address: patientData.address?.[0]?.text,
      };

      const countEntries = (bundle: any) => bundle?.entry?.length || 0;

      const preview: DataPreview = {
        conditions: countEntries(allData.conditions),
        procedures: countEntries(allData.procedures),
        medications: countEntries(allData.medications),
        observations: countEntries(allData.observations),
        encounters: countEntries(allData.encounters),
        allergies: countEntries(allData.allergies),
        immunizations: countEntries(allData.immunizations),
        diagnosticReports: countEntries(allData.diagnosticReports),
        coverages: countEntries(allData.coverages),
        errors: [],
      };

      setState((prev) => ({
        ...prev,
        patientData: patient,
        dataPreview: preview,
        step: 2,
        loading: false,
        epicConnected: true, // Fake connection for demo mode
      }));
      setShowDataPreview(true);
      setShowDemoMode(false);
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to load demo patient",
        loading: false,
      }));
    }
  };

  const generateDemoClaim = async () => {
    if (!selectedDemoPatient) return;

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const response = await fetch(`${BACKEND_URL}/demo/generate-claim/${selectedDemoPatient}`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate demo claim");
      }

      const backendClaim = await response.json();
      const atoms: EvidenceAtom[] = backendClaim.evidence_atoms || [];

      const mappedClaim: GeneratedClaim = {
        claim_id: backendClaim.id,
        status: backendClaim.status,
        patient: {
          name: { field_name: "Name", value: backendClaim.patient_name || "", evidence_ids: [], confidence: 1.0, status: "valid" },
          id: { field_name: "Patient ID", value: backendClaim.patient_id || "", evidence_ids: [], confidence: 1.0, status: "valid" },
        },
        diagnoses: backendClaim.diagnoses?.map((d: any) => ({
          code: d.code,
          display: d.description,
          evidence_ids: d.evidence_ids || d.supporting_evidence || [],
          confidence: d.confidence,
          is_primary: d.sequence === 1,
          has_evidence: d.has_evidence ?? ((d.evidence_ids?.length || 0) > 0 || (d.supporting_evidence?.length || 0) > 0),
          evidence_status: d.evidence_status || "unsupported",
          confidence_level: d.confidence_level || (d.confidence >= 0.9 ? "high" : d.confidence >= 0.7 ? "medium" : "low"),
        })) || [],
        lines: backendClaim.lines?.map((l: any) => ({
          line_number: l.line_number,
          code: l.code,
          code_type: l.code_type,
          description: l.description,
          charge_amount: l.charge_amount,
          confidence: l.confidence,
          supporting_evidence: l.evidence_ids || l.supporting_evidence || [],
          rationale: l.rationale,
          has_evidence: l.has_evidence ?? ((l.evidence_ids?.length || 0) > 0 || (l.supporting_evidence?.length || 0) > 0),
          evidence_status: l.evidence_status || "unsupported",
          confidence_level: l.confidence_level || (l.confidence >= 0.9 ? "high" : l.confidence >= 0.7 ? "medium" : "low"),
          requires_review: l.requires_review ?? false,
        })) || [],
        total_charges: backendClaim.total_charges || 0,
        validation_errors: [],
        validation_warnings: backendClaim.review_reasons || [],
        can_submit: !backendClaim.requires_review,
        all_evidence_ids: atoms.map((a) => a.evidence_id),
      };

      setState((prev) => ({
        ...prev,
        claim: mappedClaim,
        evidenceAtoms: atoms,
        step: 3,
        loading: false,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to generate demo claim",
        loading: false,
      }));
    }
  };

  const fetchDataPreview = async () => {
    try {
      const response = await fetch(`${EPIC_BRIDGE_URL}/fhir/all`, { credentials: "include" });
      
      if (!response.ok) {
        return; // Silently fail - preview is optional
      }
      
      const data = await response.json();
      
      const countEntries = (bundle: any) => {
        if (!bundle) return 0;
        if (bundle.entry) return bundle.entry.length;
        if (bundle.total !== undefined) return bundle.total;
        return 0;
      };

      const preview: DataPreview = {
        conditions: countEntries(data.conditions),
        procedures: countEntries(data.procedures),
        medications: countEntries(data.medications),
        observations: countEntries(data.observations),
        encounters: countEntries(data.encounters),
        allergies: countEntries(data.allergies),
        immunizations: countEntries(data.immunizations),
        diagnosticReports: countEntries(data.diagnosticReports),
        coverages: countEntries(data.coverages),
        errors: data._errors?.map((e: any) => e.resource) || [],
      };

      setState((prev) => ({
        ...prev,
        dataPreview: preview,
      }));
      setShowDataPreview(true);
    } catch {
      // Silently fail - preview is optional
    }
  };

  const generateClaim = async () => {
    if (!state.patientData) return;
    
    setState((prev) => ({ ...prev, loading: true, error: null }));
    
    try {
      // Fetch ALL FHIR data (patient + conditions + procedures + etc.) for comprehensive claim generation
      const allDataResponse = await fetch(`${EPIC_BRIDGE_URL}/fhir/all`, { credentials: "include" });
      
      if (!allDataResponse.ok) {
        throw new Error("Failed to fetch FHIR data. Please authenticate first.");
      }
      
      const allFhirData = await allDataResponse.json();
      
      // Send to backend for processing
      const response = await fetch(`${BACKEND_URL}/pipeline/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fhir_data: allFhirData }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate claim");
      }
      
      const backendClaim = await response.json();
      
      // Extract evidence atoms from the backend response
      const atoms: EvidenceAtom[] = backendClaim.evidence_atoms || [];
      
      // Map backend response to frontend format
      const mappedClaim: GeneratedClaim = {
        claim_id: backendClaim.id,
        status: backendClaim.status,
        patient: {
          name: { field_name: "Name", value: backendClaim.patient_name || "", evidence_ids: atoms.filter(a => a.evidence_type === "patient_name").map(a => a.evidence_id), confidence: 1.0, status: "valid" },
          id: { field_name: "Patient ID", value: backendClaim.patient_id || "", evidence_ids: atoms.filter(a => a.evidence_type === "fhir_patient").map(a => a.evidence_id), confidence: 1.0, status: "valid" },
          dob: { field_name: "Date of Birth", value: atoms.find(a => a.evidence_type === "patient_dob")?.content_excerpt?.split(": ")[1] || "", evidence_ids: atoms.filter(a => a.evidence_type === "patient_dob").map(a => a.evidence_id), confidence: 1.0, status: "valid" },
          gender: { field_name: "Gender", value: atoms.find(a => a.evidence_type === "patient_gender")?.content_excerpt?.split(": ")[1] || "", evidence_ids: atoms.filter(a => a.evidence_type === "patient_gender").map(a => a.evidence_id), confidence: 1.0, status: "valid" },
        },
        diagnoses: backendClaim.diagnoses?.map((d: any) => ({
          code: d.code,
          display: d.description,
          evidence_ids: d.evidence_ids || d.supporting_evidence || [],
          confidence: d.confidence,
          is_primary: d.sequence === 1,
          has_evidence: d.has_evidence ?? ((d.evidence_ids?.length || 0) > 0 || (d.supporting_evidence?.length || 0) > 0),
          evidence_status: d.evidence_status || "unsupported",
          confidence_level: d.confidence_level || (d.confidence >= 0.9 ? "high" : d.confidence >= 0.7 ? "medium" : "low"),
        })) || [],
        lines: backendClaim.lines?.map((l: any) => ({
          line_number: l.line_number,
          code: l.code,
          code_type: l.code_type,
          description: l.description,
          charge_amount: l.charge_amount,
          confidence: l.confidence,
          supporting_evidence: l.evidence_ids || l.supporting_evidence || [],
          rationale: l.rationale,
          has_evidence: l.has_evidence ?? ((l.evidence_ids?.length || 0) > 0 || (l.supporting_evidence?.length || 0) > 0),
          evidence_status: l.evidence_status || "unsupported",
          confidence_level: l.confidence_level || (l.confidence >= 0.9 ? "high" : l.confidence >= 0.7 ? "medium" : "low"),
          requires_review: l.requires_review ?? false,
        })) || [],
        total_charges: backendClaim.total_charges || 0,
        validation_errors: [],
        validation_warnings: backendClaim.review_reasons || [],
        can_submit: !backendClaim.requires_review,
        all_evidence_ids: atoms.map(a => a.evidence_id),
      };
      
      setState((prev) => ({
        ...prev,
        claim: mappedClaim,
        evidenceAtoms: atoms,
        step: 3,
        loading: false,
      }));
    } catch (err: unknown) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to generate claim",
        loading: false,
      }));
    }
  };

  const generateNarrative = async () => {
    if (!state.claim) return;  // Only require claim data, evidence atoms are optional

    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      // Send claim data to generate narrative with Ollama
      const response = await fetch(`${BACKEND_URL}/narrative/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: state.claim.claim_id,
          status: state.claim.status,
          patient_id: state.claim.patient.id?.value || "",
          patient_name: state.claim.patient.name?.value || "",
          total_charges: state.claim.total_charges,
          diagnoses: state.claim.diagnoses.map((d) => ({
            sequence: d.is_primary ? 1 : 2,
            code: d.code,
            description: d.display,
            confidence: d.confidence,
            supporting_evidence: d.evidence_ids,
          })),
          lines: state.claim.lines.map((l) => ({
            line_number: l.line_number,
            code: l.code,
            code_type: l.code_type,
            description: l.description,
            charge_amount: l.charge_amount,
            confidence: l.confidence,
            supporting_evidence: l.supporting_evidence,
            rationale: l.rationale,
          })),
          evidence_atoms: state.evidenceAtoms.map((a) => ({
            evidence_id: a.evidence_id,
            evidence_type: a.evidence_type,
            source_system: a.source_system,
            document_name: a.source_system,
            content_excerpt: a.content_excerpt,
            confidence: a.confidence,
          })),
          created_at: new Date().toISOString(),
          requires_review: !state.claim.can_submit,
          review_reasons: state.claim.validation_warnings,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate narrative");
      }

      const narrative = await response.json();

      setState((prev) => ({
        ...prev,
        narrativeClaim: narrative,
        showNarrative: true,
        loading: false,
      }));
    } catch (err: unknown) {
      setState((prev) => ({
        ...prev,
        error: err instanceof Error ? err.message : "Failed to generate narrative",
        loading: false,
      }));
    }
  };

  const StepIndicator = ({ currentStep }: { currentStep: number }) => (
    <div className="flex items-center justify-center mb-8">
      {["Connect Epic", "Fetch Patient", "Generate Claim", "Review"].map((label, idx) => (
        <React.Fragment key={idx}>
          <div className="flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                idx < currentStep
                  ? "bg-emerald-500 text-white"
                  : idx === currentStep
                  ? "bg-blue-500 text-white ring-4 ring-blue-500/30"
                  : "bg-gray-700 text-gray-400"
              }`}
            >
              {idx < currentStep ? "✓" : idx + 1}
            </div>
            <span className={`mt-2 text-xs ${idx <= currentStep ? "text-gray-200" : "text-gray-500"}`}>
              {label}
            </span>
          </div>
          {idx < 3 && (
            <div
              className={`w-16 h-1 mx-2 rounded transition-all duration-300 ${
                idx < currentStep ? "bg-emerald-500" : "bg-gray-700"
              }`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center">
                <span className="text-white font-bold text-lg">I</span>
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Insurabridge</h1>
                <p className="text-xs text-gray-400">Epic FHIR → Claims Pipeline</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  state.epicConnected
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "bg-red-500/20 text-red-400 border border-red-500/30"
                }`}
              >
                {state.epicConnected ? "● Epic Connected" : "○ Not Connected"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <StepIndicator currentStep={state.step} />

        {/* Error Display */}
        {state.error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            <strong>Error:</strong> {state.error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Actions */}
          <div className="space-y-6">
            {/* Step 1: Epic Connection */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400">1</span>
                Connect to Epic
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Authenticate with Epic&apos;s FHIR sandbox to access patient data.
              </p>
              
              {!state.epicConnected ? (
                <>
                  <button
                    onClick={connectToEpic}
                    className="w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 bg-blue-500 hover:bg-blue-600 text-white"
                  >
                    Connect to Epic →
                  </button>
                  <button
                    onClick={() => setShowTestPatients(!showTestPatients)}
                    className="mt-2 w-full text-sm text-blue-400 hover:text-blue-300 flex items-center justify-center gap-1"
                  >
                    {showTestPatients ? "▼" : "▶"} View Test Patient Credentials
                  </button>
                </>
              ) : (
                <>
                  <div className="bg-emerald-500/20 text-emerald-400 py-3 px-4 rounded-xl text-center font-medium mb-3">
                    ✓ Connected to Epic
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={switchPatient}
                      className="flex-1 py-2 px-3 rounded-lg font-medium transition-all duration-200 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 text-sm"
                    >
                      🔄 Switch Patient
                    </button>
                    <button
                      onClick={logoutFromEpic}
                      className="flex-1 py-2 px-3 rounded-lg font-medium transition-all duration-200 bg-red-500/20 hover:bg-red-500/30 text-red-400 text-sm"
                    >
                      🚪 Logout
                    </button>
                  </div>
                </>
              )}

              {/* Test Patients Panel */}
              {showTestPatients && !state.epicConnected && (
                <div className="mt-4 bg-gray-900/50 rounded-xl p-4 border border-gray-700">
                  <h3 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                    <span className="text-lg">🧪</span> Epic Sandbox Test Patients
                  </h3>
                  <p className="text-xs text-emerald-400 mb-3">⭐ = Rich clinical data (conditions, meds, procedures)</p>
                  <div className="space-y-2 max-h-72 overflow-y-auto">
                    {TEST_PATIENTS.map((patient) => (
                      <div
                        key={patient.username}
                        className={`rounded-lg p-3 transition-colors ${
                          patient.hasRichData 
                            ? "bg-emerald-900/20 border border-emerald-500/30 hover:bg-emerald-900/30" 
                            : "bg-gray-800/50 hover:bg-gray-800"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className={`font-medium ${patient.hasRichData ? "text-emerald-300" : "text-white"}`}>
                              {patient.name}
                            </span>
                            <p className={`text-xs ${patient.hasRichData ? "text-emerald-400/70" : "text-gray-500"}`}>
                              {patient.description}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-400 font-mono bg-gray-800 px-2 py-0.5 rounded">{patient.username}</p>
                            <p className="text-xs text-gray-500 font-mono mt-1">{patient.password}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-3 text-center">
                    Click &quot;Connect to Epic&quot; then use any credentials above
                  </p>
                </div>
              )}

              <button
                onClick={checkEpicConnection}
                className="mt-3 w-full text-sm text-gray-500 hover:text-gray-300"
              >
                ↻ Refresh connection status
              </button>

              {/* Demo Mode Divider */}
              <div className="mt-4 pt-4 border-t border-gray-700">
                <button
                  onClick={() => setShowDemoMode(!showDemoMode)}
                  className="w-full text-sm text-amber-400 hover:text-amber-300 flex items-center justify-center gap-2"
                >
                  <span className="text-lg">🧪</span>
                  {showDemoMode ? "Hide Demo Mode" : "Try Demo Mode (Rich Synthetic Data)"}
                </button>
              </div>

              {/* Demo Mode Panel */}
              {showDemoMode && demoPatients.length > 0 && (
                <div className="mt-4 bg-amber-900/20 rounded-xl p-4 border border-amber-500/30">
                  <h3 className="text-sm font-medium text-amber-300 mb-3 flex items-center gap-2">
                    <span className="text-lg">✨</span> Synthetic Demo Patients (Complex Cases)
                  </h3>
                  <p className="text-xs text-amber-400/70 mb-3">
                    Rich clinical data with 60-85 evidence atoms each - no Epic login required!
                  </p>
                  <div className="space-y-2">
                    {demoPatients.map((patient: any) => (
                      <button
                        key={patient.id}
                        onClick={() => loadDemoPatient(patient.id)}
                        disabled={state.loading}
                        className="w-full bg-gray-800/50 hover:bg-amber-800/30 rounded-lg p-3 text-left transition-colors border border-transparent hover:border-amber-500/30"
                      >
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="text-white font-medium">{patient.name}</span>
                              <p className="text-xs text-gray-400">
                                {patient.gender}, DOB: {patient.birthDate}
                              </p>
                              {patient.description && (
                                <p className="text-xs text-amber-400/80 mt-1">
                                  🏥 {patient.description}
                                </p>
                              )}
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-2">
                            <span className="text-xs bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded">
                              {patient.conditions} dx
                            </span>
                            <span className="text-xs bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded">
                              {patient.procedures} proc
                            </span>
                            <span className="text-xs bg-pink-500/20 text-pink-300 px-1.5 py-0.5 rounded">
                              {patient.medications} meds
                            </span>
                            <span className="text-xs bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded">
                              {patient.observations} obs
                            </span>
                            {patient.expected_atoms && (
                              <span className="text-xs bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded">
                                ~{patient.expected_atoms} atoms
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Step 2: Fetch Patient */}
            <div className={`bg-gray-800/50 border border-gray-700 rounded-2xl p-6 transition-opacity ${state.step >= 1 ? "" : "opacity-50"}`}>
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400">2</span>
                Fetch Patient Data
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Retrieve patient demographics from Epic&apos;s FHIR API.
              </p>
              <button
                onClick={fetchPatientData}
                disabled={!state.epicConnected || state.loading}
                className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 ${
                  !state.epicConnected
                    ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                    : state.patientData
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-cyan-500 hover:bg-cyan-600 text-white"
                }`}
              >
                {state.loading ? "Loading..." : state.patientData ? "✓ Patient Fetched" : "Fetch Patient →"}
              </button>
            </div>

            {/* Step 3: Generate Claim */}
            <div className={`bg-gray-800/50 border border-gray-700 rounded-2xl p-6 transition-opacity ${state.step >= 2 ? "" : "opacity-50"}`}>
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400">3</span>
                Generate Claim
                {selectedDemoPatient && (
                  <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded ml-2">Demo Mode</span>
                )}
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Convert FHIR data to EvidenceAtoms and generate a claim with full traceability.
              </p>
              <button
                onClick={selectedDemoPatient ? generateDemoClaim : generateClaim}
                disabled={!state.patientData || state.loading}
                className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 ${
                  !state.patientData
                    ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                    : state.claim
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-purple-500 hover:bg-purple-600 text-white"
                }`}
              >
                {state.loading ? "Generating..." : state.claim ? "✓ Claim Generated" : "Generate Claim →"}
              </button>
            </div>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            {/* Patient Card */}
            {state.patientData && (
              <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/30 border border-blue-500/30 rounded-2xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <span className="text-2xl">👤</span> Patient Data
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-400">Name</span>
                    <p className="text-white font-medium">{state.patientData.name}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400">ID</span>
                    <p className="text-white font-mono text-sm">{state.patientData.id.slice(0, 12)}...</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400">Date of Birth</span>
                    <p className="text-white">{state.patientData.birthDate || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-400">Gender</span>
                    <p className="text-white capitalize">{state.patientData.gender || "N/A"}</p>
                  </div>
                </div>
                {state.patientData.address && (
                  <div className="mt-4">
                    <span className="text-xs text-gray-400">Address</span>
                    <p className="text-white text-sm">{state.patientData.address}</p>
                  </div>
                )}
              </div>
            )}

            {/* Data Preview Panel */}
            {state.dataPreview && showDataPreview && (
              <div className="bg-gradient-to-br from-indigo-900/30 to-violet-900/30 border border-indigo-500/30 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <span className="text-2xl">📊</span> Available Clinical Data
                  </h3>
                  <button
                    onClick={() => setShowDataPreview(false)}
                    className="text-gray-400 hover:text-white text-sm"
                  >
                    ✕ Hide
                  </button>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: "Conditions", count: state.dataPreview.conditions, icon: "🩺", color: "blue" },
                    { label: "Procedures", count: state.dataPreview.procedures, icon: "💉", color: "purple" },
                    { label: "Medications", count: state.dataPreview.medications, icon: "💊", color: "pink" },
                    { label: "Observations", count: state.dataPreview.observations, icon: "📈", color: "cyan" },
                    { label: "Encounters", count: state.dataPreview.encounters, icon: "🏥", color: "emerald" },
                    { label: "Allergies", count: state.dataPreview.allergies, icon: "⚠️", color: "orange" },
                    { label: "Immunizations", count: state.dataPreview.immunizations, icon: "💪", color: "green" },
                    { label: "Diagnostics", count: state.dataPreview.diagnosticReports, icon: "🔬", color: "indigo" },
                    { label: "Coverage", count: state.dataPreview.coverages, icon: "🛡️", color: "amber" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className={`bg-gray-800/50 rounded-lg p-3 text-center ${
                        item.count > 0 ? "ring-1 ring-emerald-500/30" : ""
                      }`}
                    >
                      <span className="text-xl">{item.icon}</span>
                      <p className={`text-2xl font-bold ${item.count > 0 ? "text-emerald-400" : "text-gray-500"}`}>
                        {item.count}
                      </p>
                      <p className="text-xs text-gray-400">{item.label}</p>
                    </div>
                  ))}
                </div>
                {state.dataPreview.errors.length > 0 && (
                  <div className="mt-3 text-xs text-yellow-500">
                    ⚠️ Could not fetch: {state.dataPreview.errors.join(", ")}
                  </div>
                )}
                <p className="text-xs text-gray-500 mt-3 text-center">
                  {state.dataPreview.conditions + state.dataPreview.procedures + state.dataPreview.medications > 0
                    ? "✨ This patient has rich clinical data for claim generation!"
                    : "💡 Try a different test patient for more clinical data"}
                </p>
              </div>
            )}

            {/* Generated Claim */}
            {state.claim && (
              <div className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <span className="text-2xl">📋</span> Generated Claim
                  </h3>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      state.claim.can_submit
                        ? "bg-emerald-500/20 text-emerald-400"
                        : state.claim.status === "REVIEW_REQUIRED"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-red-500/20 text-red-400"
                    }`}
                  >
                    {state.claim.status}
                  </span>
                </div>

                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-gray-400">Claim ID</span>
                    <p className="text-white font-mono">{state.claim.claim_id}</p>
                  </div>

                  <div>
                    <span className="text-xs text-gray-400">Evidence Atoms Created</span>
                    <p className="text-white font-bold text-2xl">{state.evidenceAtoms?.length || state.claim.all_evidence_ids?.length || 0}</p>
                  </div>

                  {/* Evidence Verification Summary */}
                  {(() => {
                    const verifiedDx = state.claim.diagnoses?.filter(d => d.has_evidence ?? (d.evidence_ids?.length > 0)).length || 0;
                    const unverifiedDx = (state.claim.diagnoses?.length || 0) - verifiedDx;
                    const verifiedLines = state.claim.lines?.filter(l => l.has_evidence ?? (l.supporting_evidence?.length > 0)).length || 0;
                    const unverifiedLines = (state.claim.lines?.length || 0) - verifiedLines;
                    const totalItems = (state.claim.diagnoses?.length || 0) + (state.claim.lines?.length || 0);
                    const verifiedItems = verifiedDx + verifiedLines;
                    const verificationRate = totalItems > 0 ? Math.round((verifiedItems / totalItems) * 100) : 0;
                    
                    return (
                      <div className={`rounded-xl p-4 border ${verificationRate === 100 ? 'bg-emerald-900/20 border-emerald-500/30' : verificationRate >= 70 ? 'bg-yellow-900/20 border-yellow-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-sm font-medium text-gray-300 flex items-center gap-2">
                            {verificationRate === 100 ? '✅' : verificationRate >= 70 ? '⚠️' : '❌'} 
                            Evidence Verification Status
                          </span>
                          <span className={`text-2xl font-bold ${verificationRate === 100 ? 'text-emerald-400' : verificationRate >= 70 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {verificationRate}%
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-gray-800/50 rounded-lg p-3">
                            <span className="text-xs text-gray-400 block mb-1">Diagnoses</span>
                            <div className="flex items-center gap-2">
                              <span className="text-emerald-400 font-bold">{verifiedDx} ✓</span>
                              {unverifiedDx > 0 && (
                                <span className="text-red-400 font-bold">{unverifiedDx} ⚠️</span>
                              )}
                            </div>
                          </div>
                          <div className="bg-gray-800/50 rounded-lg p-3">
                            <span className="text-xs text-gray-400 block mb-1">Procedures</span>
                            <div className="flex items-center gap-2">
                              <span className="text-emerald-400 font-bold">{verifiedLines} ✓</span>
                              {unverifiedLines > 0 && (
                                <span className="text-red-400 font-bold">{unverifiedLines} ⚠️</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {(unverifiedDx > 0 || unverifiedLines > 0) && (
                          <div className="mt-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                            <p className="text-xs text-red-300">
                              <strong>⚠️ Action Required:</strong> {unverifiedDx + unverifiedLines} item(s) lack supporting evidence. 
                              Doctors should verify these claims before submission or add evidence citations.
                            </p>
                          </div>
                        )}
                        {verificationRate === 100 && (
                          <div className="mt-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3">
                            <p className="text-xs text-emerald-300">
                              <strong>✅ Fully Verified:</strong> All diagnoses and procedures are linked to supporting evidence atoms.
                              This claim is ready for physician review.
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })()}

                  {/* Patient Fields with Evidence */}
                  <div>
                    <span className="text-xs text-gray-400 mb-2 block">Patient Fields (with citations)</span>
                    <div className="space-y-2">
                      {Object.entries(state.claim.patient || {}).map(([key, field]) => (
                        <div key={key} className="bg-gray-800/50 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-gray-400 text-sm">{field.field_name}</span>
                            <span className="text-xs text-blue-400">
                              📎 {field.evidence_ids?.length || 0} citations
                            </span>
                          </div>
                          <p className="text-white">{field.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Total Charges */}
                  <div className="bg-gradient-to-r from-emerald-900/30 to-teal-900/30 rounded-lg p-4">
                    <span className="text-xs text-gray-400">Total Charges</span>
                    <p className="text-3xl font-bold text-emerald-400">${state.claim.total_charges?.toFixed(2) || '0.00'}</p>
                  </div>

                  {/* Claim Lines (CPT Codes) */}
                  {state.claim.lines?.length > 0 && (
                    <div>
                      <span className="text-xs text-gray-400 mb-2 block">Procedures & Services (CPT/HCPCS)</span>
                      <div className="space-y-2">
                        {state.claim.lines.map((line, idx) => {
                          const hasEvidence = line.has_evidence ?? (line.supporting_evidence?.length > 0);
                          const evidenceStatus = line.evidence_status || (hasEvidence ? "verified" : "unsupported");
                          const borderColor = evidenceStatus === "verified" ? "border-emerald-500" : evidenceStatus === "partial" ? "border-yellow-500" : "border-red-500";
                          const bgColor = evidenceStatus === "verified" ? "bg-emerald-500/5" : evidenceStatus === "partial" ? "bg-yellow-500/5" : "bg-red-500/5";
                          
                          return (
                            <div key={idx} className={`${bgColor} rounded-lg p-3 border-l-4 ${borderColor}`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className={`font-mono font-bold ${hasEvidence ? "text-purple-400" : "text-red-400"}`}>{line.code}</span>
                                  <span className="text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded">{line.code_type}</span>
                                  {/* Evidence Status Badge */}
                                  {hasEvidence ? (
                                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded flex items-center gap-1">
                                      <span>✓</span> Verified
                                    </span>
                                  ) : (
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded flex items-center gap-1 animate-pulse">
                                      <span>⚠️</span> No Evidence
                                    </span>
                                  )}
                                </div>
                                <span className="text-emerald-400 font-bold">${line.charge_amount?.toFixed(2)}</span>
                              </div>
                              <p className={`text-sm mt-1 ${hasEvidence ? "text-white" : "text-red-200"}`}>{line.description}</p>
                              <p className={`text-xs mt-1 italic ${hasEvidence ? "text-gray-400" : "text-red-300"}`}>{line.rationale}</p>
                              <div className="flex items-center justify-between mt-2 flex-wrap gap-2">
                                <div className="flex items-center gap-1 flex-wrap">
                                  {hasEvidence && line.supporting_evidence?.length > 0 && (
                                    <>
                                      <span className="text-xs text-emerald-400">📎 Evidence:</span>
                                      {line.supporting_evidence.slice(0, 2).map((evId, evIdx) => (
                                        <button
                                          key={evIdx}
                                          onClick={() => {
                                            const atom = state.evidenceAtoms.find(a => a.evidence_id === evId);
                                            if (atom) alert(`Evidence: ${atom.content_excerpt}`);
                                          }}
                                          className="text-xs bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded hover:bg-emerald-500/40 transition-colors font-mono"
                                          title="Click to view evidence"
                                        >
                                          {evId.substring(0, 12)}...
                                        </button>
                                      ))}
                                      {line.supporting_evidence.length > 2 && (
                                        <span className="text-xs text-emerald-400">+{line.supporting_evidence.length - 2} more</span>
                                      )}
                                    </>
                                  )}
                                  {!hasEvidence && (
                                    <span className="text-xs text-red-400 italic">⚠️ Needs evidence citation for billing verification</span>
                                  )}
                                </div>
                                <span className={`text-xs px-2 py-1 rounded ${line.confidence >= 0.9 ? 'bg-green-500/20 text-green-400' : line.confidence >= 0.7 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                                  {(line.confidence * 100).toFixed(0)}% confidence
                                </span>
                              </div>
                              {line.requires_review && (
                                <div className="mt-2 bg-yellow-500/10 text-yellow-400 text-xs px-2 py-1 rounded border border-yellow-500/30">
                                  ⚠️ This line requires manual review before submission
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Diagnoses */}
                  {state.claim.diagnoses?.length > 0 && (
                    <div>
                      <span className="text-xs text-gray-400 mb-2 block">Diagnoses (ICD-10)</span>
                      <div className="space-y-2">
                        {state.claim.diagnoses.map((dx, idx) => {
                          const hasEvidence = dx.has_evidence ?? (dx.evidence_ids?.length > 0);
                          const evidenceStatus = dx.evidence_status || (hasEvidence ? "verified" : "unsupported");
                          const borderColor = evidenceStatus === "verified" ? "border-emerald-500" : evidenceStatus === "partial" ? "border-yellow-500" : "border-red-500";
                          const bgColor = evidenceStatus === "verified" ? "bg-emerald-500/5" : evidenceStatus === "partial" ? "bg-yellow-500/5" : "bg-red-500/5";
                          
                          return (
                            <div key={idx} className={`${bgColor} rounded-lg p-3 border-l-4 ${borderColor}`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className={`font-mono font-bold ${hasEvidence ? "text-blue-400" : "text-red-400"}`}>{dx.code}</span>
                                  {/* Evidence Status Badge */}
                                  {hasEvidence ? (
                                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded flex items-center gap-1">
                                      <span>✓</span> Verified
                                    </span>
                                  ) : (
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded flex items-center gap-1 animate-pulse">
                                      <span>⚠️</span> No Evidence
                                    </span>
                                  )}
                                </div>
                                <span className={`text-xs px-2 py-1 rounded ${dx.confidence >= 0.9 ? 'bg-green-500/20 text-green-400' : dx.confidence >= 0.7 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                                  {(dx.confidence * 100).toFixed(0)}% confidence
                                </span>
                              </div>
                              <p className={`text-sm mt-1 ${hasEvidence ? "text-white" : "text-red-200"}`}>{dx.display}</p>
                              <div className="flex items-center gap-2 mt-2 flex-wrap">
                                {dx.is_primary && <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">Primary Dx</span>}
                                {hasEvidence && dx.evidence_ids?.length > 0 && (
                                  <div className="flex items-center gap-1">
                                    <span className="text-xs text-emerald-400">📎 Evidence:</span>
                                    {dx.evidence_ids.slice(0, 2).map((evId, evIdx) => (
                                      <button
                                        key={evIdx}
                                        onClick={() => {
                                          const atom = state.evidenceAtoms.find(a => a.evidence_id === evId);
                                          if (atom) alert(`Evidence: ${atom.content_excerpt}`);
                                        }}
                                        className="text-xs bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded hover:bg-emerald-500/40 transition-colors font-mono"
                                        title="Click to view evidence"
                                      >
                                        {evId.substring(0, 12)}...
                                      </button>
                                    ))}
                                    {dx.evidence_ids.length > 2 && (
                                      <span className="text-xs text-emerald-400">+{dx.evidence_ids.length - 2} more</span>
                                    )}
                                  </div>
                                )}
                                {!hasEvidence && (
                                  <span className="text-xs text-red-400 italic">⚠️ Needs evidence citation for verification</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Evidence Atoms Detail */}
                  {state.evidenceAtoms?.length > 0 && (
                    <div>
                      <span className="text-xs text-gray-400 mb-2 block">Evidence Atoms ({state.evidenceAtoms.length} extracted)</span>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {state.evidenceAtoms.map((atom, idx) => (
                          <div key={idx} className="bg-gray-800/50 rounded-lg p-3 border-l-4 border-emerald-500">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-emerald-400 font-mono text-xs">{atom.evidence_id}</span>
                              <span className="text-xs text-gray-500">{atom.source_system}</span>
                            </div>
                            <p className="text-white text-sm">{atom.content_excerpt}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">{atom.evidence_type}</span>
                              <span className="text-xs text-gray-500">{(atom.confidence * 100).toFixed(0)}% confidence</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Validation Messages */}
                  {state.claim.validation_errors?.length > 0 && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                      <span className="text-red-400 text-sm font-medium">Validation Errors</span>
                      <ul className="mt-2 space-y-1">
                        {state.claim.validation_errors.map((err, idx) => (
                          <li key={idx} className="text-red-300 text-sm">• {err}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {state.claim.validation_warnings?.length > 0 && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                      <span className="text-yellow-400 text-sm font-medium">Warnings</span>
                      <ul className="mt-2 space-y-1">
                        {state.claim.validation_warnings.map((warn, idx) => (
                          <li key={idx} className="text-yellow-300 text-sm">• {warn}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={generateNarrative}
                      disabled={state.loading}
                      className="flex-1 py-3 px-4 rounded-xl font-medium transition-all duration-200 bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      {state.loading ? "Generating..." : "📄 View Full Claim with Citations"}
                    </button>
                  </div>

                  <button
                    disabled={!state.claim.can_submit}
                    className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 ${
                      state.claim.can_submit
                        ? "bg-emerald-500 hover:bg-emerald-600 text-white"
                        : "bg-gray-700 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    {state.claim.can_submit ? "Submit Claim" : "Cannot Submit - Review Required"}
                  </button>
                </div>
              </div>
            )}

            {/* Empty State */}
            {!state.patientData && !state.claim && (
              <div className="bg-gray-800/30 border border-gray-700 border-dashed rounded-2xl p-12 text-center">
                <div className="text-4xl mb-4">🏥</div>
                <h3 className="text-lg font-medium text-gray-400">No Data Yet</h3>
                <p className="text-sm text-gray-500 mt-2">
                  Connect to Epic and fetch patient data to see results here.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Narrative Claim Modal */}
      {state.showNarrative && state.narrativeClaim && (
        <div className="fixed inset-0 bg-black/80 z-50 overflow-y-auto">
          <div className="min-h-screen py-8 px-4">
            <div className="max-w-6xl mx-auto">
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-t-2xl p-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">{state.narrativeClaim.title}</h2>
                  <p className="text-gray-300 text-sm mt-1">{state.narrativeClaim.summary}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>Generated: {new Date(state.narrativeClaim.generated_at).toLocaleString()}</span>
                    <span>Model: {state.narrativeClaim.llm_model}</span>
                    <span className={`px-2 py-0.5 rounded ${state.narrativeClaim.requires_review ? 'bg-yellow-500/20 text-yellow-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                      {state.narrativeClaim.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setState(prev => ({ ...prev, showNarrative: false }))}
                  className="bg-white/10 hover:bg-white/20 text-white p-2 rounded-lg transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Modal Content */}
              <div className="bg-gray-900 rounded-b-2xl grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                {/* Left: Narrative Sections */}
                <div className="lg:col-span-2 space-y-4">
                  <NarrativeSection
                    title="Patient Information"
                    content={state.narrativeClaim.patient_section.content}
                    atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                    evidenceIds={state.narrativeClaim.patient_section.evidence_ids}
                    icon="👤"
                    borderColor="border-blue-500"
                  />
                  <NarrativeSection
                    title="Diagnoses"
                    content={state.narrativeClaim.diagnoses_section.content}
                    atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                    evidenceIds={state.narrativeClaim.diagnoses_section.evidence_ids}
                    icon="🩺"
                    borderColor="border-cyan-500"
                  />
                  <NarrativeSection
                    title="Procedures & Services"
                    content={state.narrativeClaim.procedures_section.content}
                    atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                    evidenceIds={state.narrativeClaim.procedures_section.evidence_ids}
                    icon="💉"
                    borderColor="border-purple-500"
                  />
                  <NarrativeSection
                    title="Medical Necessity Justification"
                    content={state.narrativeClaim.medical_necessity_section.content}
                    atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                    evidenceIds={state.narrativeClaim.medical_necessity_section.evidence_ids}
                    icon="📋"
                    borderColor="border-amber-500"
                  />
                  <NarrativeSection
                    title="Billing Summary"
                    content={state.narrativeClaim.billing_summary_section.content}
                    atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                    evidenceIds={state.narrativeClaim.billing_summary_section.evidence_ids}
                    icon="💰"
                    borderColor="border-emerald-500"
                  />

                  {/* Total */}
                  <div className="bg-gradient-to-r from-emerald-900/50 to-teal-900/50 border border-emerald-500/30 rounded-xl p-6 text-center">
                    <span className="text-gray-400 text-sm">Total Charges</span>
                    <p className="text-4xl font-bold text-emerald-400 mt-1">
                      ${state.narrativeClaim.total_charges.toFixed(2)}
                    </p>
                  </div>

                  {/* Review Reasons */}
                  {state.narrativeClaim.review_reasons.length > 0 && (
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
                      <h4 className="text-yellow-400 font-medium mb-2">⚠️ Review Required</h4>
                      <ul className="space-y-1">
                        {state.narrativeClaim.review_reasons.map((reason, idx) => (
                          <li key={idx} className="text-yellow-300 text-sm">• {reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Right: Evidence Library */}
                <div className="lg:col-span-1">
                  <div className="sticky top-4">
                    <EvidenceLibrary
                      atoms={state.narrativeClaim.evidence_atoms as EvidenceAtomType[]}
                      highlightedIds={[
                        ...state.narrativeClaim.patient_section.evidence_ids,
                        ...state.narrativeClaim.diagnoses_section.evidence_ids,
                        ...state.narrativeClaim.procedures_section.evidence_ids,
                      ]}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}













