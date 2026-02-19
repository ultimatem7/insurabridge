import CTASection from '@/components/CTASection'

export const metadata = {
  title: 'How It Works - Insurabridge',
  description: 'Learn how Insurabridge automates insurance claim generation from EHR data with audit-ready evidence.',
}

export default function HowItWorks() {
  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-gradient-to-b from-clinical-50 to-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">How Insurabridge Works</h1>
            <p className="body-large">
              From EHR connection to submission-ready claims in minutes, with complete audit trails
            </p>
          </div>
        </div>
      </section>

      {/* Detailed Process */}
      <section className="section-padding bg-white">
        <div className="container-custom max-w-4xl">
          <div className="space-y-16">
            {[
              {
                step: '01',
                title: 'Secure EHR Connection',
                description: 'Connect to your EHR system using industry-standard SMART on FHIR OAuth2 authentication. We support Epic, Cerner, eClinicalWorks, Athenahealth, and Meditech.',
                details: [
                  'OAuth2 with PKCE for enhanced security',
                  'Read-only access to patient data',
                  'Session management with automatic timeout',
                  'No credentials stored on our servers',
                ],
              },
              {
                step: '02',
                title: 'FHIR Data Extraction',
                description: 'Pull relevant clinical data using FHIR R4 API standards. All data is normalized to handle variations across different EHR vendors.',
                details: [
                  'Patient demographics and insurance info',
                  'Encounter details and visit information',
                  'Diagnoses (Condition resources)',
                  'Procedures and interventions',
                  'Clinical notes and documentation',
                  'Lab results and observations',
                ],
              },
              {
                step: '03',
                title: 'AI-Powered Analysis',
                description: 'Our local AI engine processes clinical documentation to extract billable services and generate appropriate medical codes.',
                details: [
                  'ICD-10-CM diagnosis code mapping',
                  'CPT and HCPCS procedure codes',
                  'Modifier recommendations',
                  'Medical necessity validation',
                  'NCCI bundling checks',
                  'Confidence scoring for each code',
                ],
              },
              {
                step: '04',
                title: 'Evidence Generation',
                description: 'Every code is linked to supporting clinical documentation with specific citations and confidence ratings.',
                details: [
                  'Direct quotes from clinical notes',
                  'FHIR resource references',
                  'Confidence scores (0-100%)',
                  'Supporting lab values',
                  'Policy references where applicable',
                  'Audit trail with timestamps',
                ],
              },
              {
                step: '05',
                title: 'Human Review & Submission',
                description: 'Claims are presented for coder review before submission. All AI suggestions are clearly marked and require human approval.',
                details: [
                  'Side-by-side clinical evidence view',
                  'Editable claim fields',
                  'Compliance checks and warnings',
                  'Export to CMS-1500 or X12 837',
                  'Integration with clearinghouses',
                  'Submission tracking',
                ],
              },
            ].map((item) => (
              <div key={item.step} className="flex gap-8">
                <div className="flex-shrink-0">
                  <div className="w-20 h-20 rounded-2xl bg-primary-100 text-primary-600 flex items-center justify-center text-2xl font-bold">
                    {item.step}
                  </div>
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-clinical-900 mb-4">
                    {item.title}
                  </h2>
                  <p className="text-lg text-clinical-600 mb-6">
                    {item.description}
                  </p>
                  <ul className="space-y-3">
                    {item.details.map((detail, index) => (
                      <li key={index} className="flex items-start">
                        <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-clinical-600">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integration Architecture */}
      <section className="section-padding bg-clinical-50">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 text-center mb-12">Integration Architecture</h2>
            
            <div className="card bg-white p-8">
              <div className="space-y-6">
                <div className="text-center p-6 bg-clinical-50 rounded-lg">
                  <div className="text-sm font-medium text-clinical-600 mb-2">Your EHR System</div>
                  <div className="font-semibold text-clinical-900">Epic / Cerner / Other</div>
                </div>

                <div className="flex justify-center">
                  <svg className="w-6 h-12 text-clinical-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>

                <div className="text-center p-6 bg-primary-50 rounded-lg border-2 border-primary-200">
                  <div className="text-sm font-medium text-primary-700 mb-2">SMART on FHIR OAuth2</div>
                  <div className="font-semibold text-primary-900">Secure Authentication</div>
                </div>

                <div className="flex justify-center">
                  <svg className="w-6 h-12 text-clinical-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>

                <div className="text-center p-6 bg-clinical-50 rounded-lg">
                  <div className="text-sm font-medium text-clinical-600 mb-2">Insurabridge (On-Premise)</div>
                  <div className="font-semibold text-clinical-900">Local Processing</div>
                </div>

                <div className="flex justify-center">
                  <svg className="w-6 h-12 text-clinical-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>

                <div className="text-center p-6 bg-success-50 rounded-lg border-2 border-success-200">
                  <div className="text-sm font-medium text-success-700 mb-2">Output</div>
                  <div className="font-semibold text-success-900">Submission-Ready Claims</div>
                </div>
              </div>

              <div className="mt-8 p-4 bg-clinical-50 rounded-lg">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-clinical-600">
                    <strong className="text-clinical-900">Important:</strong> All PHI processing occurs within your hospital's network. 
                    No patient data is sent to external servers or cloud services.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection />
    </>
  )
}
