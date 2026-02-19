import CTASection from '@/components/CTASection'

export const metadata = {
  title: 'Security & Compliance - Insurabridge',
  description: 'HIPAA-compliant healthcare claims automation with enterprise-grade security and on-premise deployment.',
}

export default function Security() {
  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-gradient-to-b from-clinical-50 to-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-success-100 text-success-700 text-sm font-medium mb-6">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              HIPAA Compliant • SOC 2 Ready
            </div>
            <h1 className="heading-1 mb-6">Enterprise-Grade Security</h1>
            <p className="body-large">
              Built from the ground up with healthcare security standards and PHI protection as the foundation
            </p>
          </div>
        </div>
      </section>

      {/* Security Features */}
      <section className="section-padding bg-white">
        <div className="container-custom max-w-5xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                title: 'On-Premise Deployment',
                description: 'Deploy entirely within your hospital network. Zero external dependencies for PHI processing.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
                ),
              },
              {
                title: 'End-to-End Encryption',
                description: 'AES-256-GCM encryption at rest. TLS 1.3 for data in transit. Encrypted database connections.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                ),
              },
              {
                title: 'Audit Logging',
                description: 'Immutable audit trails for every PHI access. Cryptographic chain prevents tampering.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                ),
              },
              {
                title: 'Role-Based Access',
                description: 'Granular permissions system. Admin, billing manager, coder, auditor, and viewer roles.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                ),
              },
              {
                title: 'Session Management',
                description: '15-minute automatic timeout. JWT tokens with refresh rotation. Secure session storage.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                ),
              },
              {
                title: 'OAuth2 Security',
                description: 'SMART on FHIR with PKCE. State validation. No credential storage. Read-only FHIR access.',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                ),
              },
            ].map((feature, index) => (
              <div key={index} className="card">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-primary-100 text-primary-600 mb-4">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {feature.icon}
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-clinical-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-clinical-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Standards */}
      <section className="section-padding bg-clinical-50">
        <div className="container-custom">
          <div className="max-w-4xl mx-auto">
            <h2 className="heading-2 text-center mb-12">Compliance Standards</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <div className="card text-center">
                <div className="text-4xl mb-4">🔒</div>
                <h3 className="text-xl font-semibold text-clinical-900 mb-2">HIPAA</h3>
                <p className="text-clinical-600">Full compliance with HIPAA Privacy and Security Rules</p>
              </div>
              <div className="card text-center">
                <div className="text-4xl mb-4">✓</div>
                <h3 className="text-xl font-semibold text-clinical-900 mb-2">SOC 2</h3>
                <p className="text-clinical-600">Type II certification in progress for hosted deployments</p>
              </div>
              <div className="card text-center">
                <div className="text-4xl mb-4">🛡️</div>
                <h3 className="text-xl font-semibold text-clinical-900 mb-2">FHIR R4</h3>
                <p className="text-clinical-600">Compliant with HL7 FHIR Release 4 standards</p>
              </div>
            </div>

            <div className="card">
              <h3 className="text-xl font-semibold text-clinical-900 mb-6">HIPAA Safeguards Implemented</h3>
              
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold text-clinical-900 mb-3">Administrative Safeguards</h4>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Security management process with risk analysis</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Workforce security and authorization procedures</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Information access management controls</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-clinical-900 mb-3">Physical Safeguards</h4>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">On-premise deployment within secured facilities</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Workstation security and device controls</span>
                    </li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-clinical-900 mb-3">Technical Safeguards</h4>
                  <ul className="space-y-2">
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Access controls with unique user identification</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Complete audit controls with tamper-proof logs</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Integrity controls ensuring data is not altered</span>
                    </li>
                    <li className="flex items-start">
                      <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-clinical-600">Transmission security with encryption</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Data Handling */}
      <section className="section-padding bg-white">
        <div className="container-custom max-w-4xl">
          <h2 className="heading-2 text-center mb-12">Data Handling Policy</h2>
          
          <div className="space-y-8">
            <div className="card border-l-4 border-primary-600">
              <h3 className="text-xl font-semibold text-clinical-900 mb-4">What We Do</h3>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-clinical-600">Process all PHI locally within your network</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-clinical-600">Encrypt all data at rest and in transit</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-clinical-600">Log every PHI access with full audit trail</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-success-500 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-clinical-600">Enforce automatic session timeouts</span>
                </li>
              </ul>
            </div>

            <div className="card border-l-4 border-clinical-400">
              <h3 className="text-xl font-semibold text-clinical-900 mb-4">What We Don't Do</h3>
              <ul className="space-y-3">
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-clinical-400 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-clinical-600">Never send PHI to external servers or cloud services</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-clinical-400 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-clinical-600">Never cache PHI in plain text</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-clinical-400 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-clinical-600">Never log sensitive patient information</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-clinical-400 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-clinical-600">Never share data with third parties</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection />
    </>
  )
}
