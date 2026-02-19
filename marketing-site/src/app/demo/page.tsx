import CTASection from '@/components/CTASection'
import Link from 'next/link'

export const metadata = {
  title: 'Product Demo - Insurabridge',
  description: 'See Insurabridge in action - automated insurance claim generation from EHR data with evidence citations.',
}

export default function Demo() {
  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-gradient-to-b from-clinical-50 to-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">See Insurabridge in Action</h1>
            <p className="body-large">
              Watch how our platform generates audit-ready insurance claims from EHR data in minutes
            </p>
          </div>
        </div>
      </section>

      {/* Screenshots Placeholder */}
      <section className="section-padding bg-white">
        <div className="container-custom max-w-6xl">
          <div className="space-y-16">
            {/* Screenshot 1: Login */}
            <div>
              <h2 className="text-2xl font-bold text-clinical-900 mb-6">
                1. Connect to Your EHR
              </h2>
              <div className="card bg-clinical-50 aspect-video flex items-center justify-center border-2 border-dashed border-clinical-300">
                <div className="text-center">
                  <svg className="w-24 h-24 text-clinical-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="text-clinical-500">Screenshot: EHR Provider Login Screen</p>
                  <p className="text-sm text-clinical-400 mt-2">Epic, Cerner, and other major EHR systems</p>
                </div>
              </div>
              <p className="text-clinical-600 mt-4">
                Secure OAuth2 authentication with your EHR system. No credentials stored on our servers.
              </p>
            </div>

            {/* Screenshot 2: Dashboard */}
            <div>
              <h2 className="text-2xl font-bold text-clinical-900 mb-6">
                2. Select Patient Encounter
              </h2>
              <div className="card bg-clinical-50 aspect-video flex items-center justify-center border-2 border-dashed border-clinical-300">
                <div className="text-center">
                  <svg className="w-24 h-24 text-clinical-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p className="text-clinical-500">Screenshot: Patient Encounter Dashboard</p>
                  <p className="text-sm text-clinical-400 mt-2">View all encounters with quick filters</p>
                </div>
              </div>
              <p className="text-clinical-600 mt-4">
                Browse patient encounters pulled directly from your EHR via FHIR API. 
                Filter by date, status, or encounter type.
              </p>
            </div>

            {/* Screenshot 3: Claim Generation */}
            <div>
              <h2 className="text-2xl font-bold text-clinical-900 mb-6">
                3. Generate Claim with AI
              </h2>
              <div className="card bg-clinical-50 aspect-video flex items-center justify-center border-2 border-dashed border-clinical-300">
                <div className="text-center">
                  <svg className="w-24 h-24 text-clinical-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <p className="text-clinical-500">Screenshot: AI Processing Clinical Data</p>
                  <p className="text-sm text-clinical-400 mt-2">Local LLM extracts codes from documentation</p>
                </div>
              </div>
              <p className="text-clinical-600 mt-4">
                Our local AI engine analyzes clinical notes, diagnoses, and procedures to generate 
                appropriate ICD-10, CPT, and HCPCS codes with confidence scores.
              </p>
            </div>

            {/* Screenshot 4: Claim Output */}
            <div>
              <h2 className="text-2xl font-bold text-clinical-900 mb-6">
                4. Review Evidence-Backed Claim
              </h2>
              <div className="card bg-clinical-50 aspect-video flex items-center justify-center border-2 border-dashed border-clinical-300">
                <div className="text-center">
                  <svg className="w-24 h-24 text-clinical-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-clinical-500">Screenshot: Generated Claim with Evidence</p>
                  <p className="text-sm text-clinical-400 mt-2">Every code linked to supporting documentation</p>
                </div>
              </div>
              <p className="text-clinical-600 mt-4">
                Review the generated claim with inline evidence citations. Each code shows supporting 
                clinical notes, confidence scores, and audit trail. Export to CMS-1500 or X12 format.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Architecture Diagram */}
      <section className="section-padding bg-clinical-50">
        <div className="container-custom max-w-5xl">
          <h2 className="heading-2 text-center mb-12">System Architecture</h2>
          
          <div className="card">
            <div className="space-y-4 text-center">
              <div className="inline-block px-6 py-3 bg-clinical-100 rounded-lg border border-clinical-300">
                <div className="font-semibold text-clinical-900">Your EHR System</div>
                <div className="text-sm text-clinical-600">Epic / Cerner / Other</div>
              </div>

              <div className="flex justify-center">
                <svg className="w-6 h-12 text-clinical-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>

              <div className="inline-block px-6 py-3 bg-primary-100 rounded-lg border-2 border-primary-300">
                <div className="font-semibold text-primary-900">SMART on FHIR OAuth2</div>
                <div className="text-sm text-primary-700">Secure Authentication</div>
              </div>

              <div className="flex justify-center">
                <svg className="w-6 h-12 text-clinical-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>

              <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto">
                <div className="px-4 py-3 bg-clinical-100 rounded-lg border border-clinical-300">
                  <div className="text-sm font-medium text-clinical-900">FHIR API</div>
                  <div className="text-xs text-clinical-600">Data Extraction</div>
                </div>
                <div className="px-4 py-3 bg-clinical-100 rounded-lg border border-clinical-300">
                  <div className="text-sm font-medium text-clinical-900">Local LLM</div>
                  <div className="text-xs text-clinical-600">AI Processing</div>
                </div>
                <div className="px-4 py-3 bg-clinical-100 rounded-lg border border-clinical-300">
                  <div className="text-sm font-medium text-clinical-900">PostgreSQL</div>
                  <div className="text-xs text-clinical-600">Storage</div>
                </div>
              </div>

              <div className="flex justify-center">
                <svg className="w-6 h-12 text-clinical-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>

              <div className="inline-block px-6 py-3 bg-success-100 rounded-lg border-2 border-success-300">
                <div className="font-semibold text-success-900">Submission-Ready Claim</div>
                <div className="text-sm text-success-700">CMS-1500 • X12 837 • JSON</div>
              </div>

              <div className="mt-8 p-4 bg-primary-50 rounded-lg border border-primary-200">
                <div className="flex items-start justify-center">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <p className="text-sm text-clinical-700">
                    <strong>All PHI processing occurs within your hospital network.</strong> No data leaves your environment.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center mt-12">
            <Link href="/contact" className="btn-primary btn-large">
              Schedule a Live Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Evidence Citations Example */}
      <section className="section-padding bg-white">
        <div className="container-custom max-w-4xl">
          <h2 className="heading-2 text-center mb-12">Evidence-Based Coding</h2>
          
          <div className="card">
            <div className="space-y-6">
              <div className="flex items-start justify-between p-4 bg-clinical-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-lg font-semibold text-primary-600">99214</span>
                    <span className="badge">CPT</span>
                    <span className="text-sm text-clinical-600">Office visit, established patient</span>
                  </div>
                  <p className="text-sm text-clinical-600 mb-3">
                    Office or other outpatient visit for the evaluation and management of an established patient
                  </p>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <svg className="w-4 h-4 text-success-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm font-medium text-success-700">92% Confidence</span>
                    </div>
                  </div>
                </div>
                <div className="ml-6">
                  <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                    View Evidence →
                  </button>
                </div>
              </div>

              <div className="p-4 bg-primary-50 rounded-lg border-l-4 border-primary-600">
                <h4 className="text-sm font-semibold text-clinical-900 mb-3">Supporting Evidence:</h4>
                <div className="space-y-2 text-sm text-clinical-700">
                  <p>
                    <span className="font-medium">Clinical Note (Page 2):</span> "Patient presents for follow-up of 
                    hypertension and diabetes. Reviewed medication compliance. Discussed lifestyle modifications. 
                    Moderate complexity medical decision making."
                  </p>
                  <p className="mt-2">
                    <span className="font-medium">FHIR Reference:</span> Encounter/abc123 (2024-01-15, Duration: 25 minutes)
                  </p>
                  <p className="mt-2">
                    <span className="font-medium">Guideline Match:</span> CPT 99214 criteria met: established patient, 
                    30-39 minutes, moderate complexity MDM
                  </p>
                </div>
              </div>

              <div className="flex items-start p-4 bg-clinical-50 rounded-lg">
                <svg className="w-5 h-5 text-clinical-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-clinical-600">
                  Every code includes supporting quotes, FHIR references, and confidence ratings. 
                  Coders can review, edit, or override any AI suggestion.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="section-padding bg-clinical-50">
        <div className="container-custom">
          <h2 className="heading-2 text-center mb-12">Key Capabilities</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              { title: 'Multi-EHR Support', description: 'Works with Epic, Cerner, and other major vendors' },
              { title: 'Real-Time Processing', description: 'Generate claims in minutes, not hours' },
              { title: 'Confidence Scoring', description: 'AI rates certainty for each code (0-100%)' },
              { title: 'Evidence Citations', description: 'Direct quotes from clinical documentation' },
              { title: 'Compliance Checks', description: 'NCCI edits, bundling rules, modifier validation' },
              { title: 'Audit Trail', description: 'Complete reasoning chain for every decision' },
              { title: 'CMS-1500 Export', description: 'Export to standard claim formats' },
              { title: 'Human Review', description: 'Coder approval required before submission' },
              { title: 'Local Processing', description: 'All PHI stays within your network' },
            ].map((feature, index) => (
              <div key={index} className="card">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <h3 className="font-semibold text-clinical-900 mb-2">{feature.title}</h3>
                    <p className="text-sm text-clinical-600">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection />
    </>
  )
}
