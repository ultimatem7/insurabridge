import Link from 'next/link'
import CTASection from '@/components/CTASection'

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-clinical-50 to-white">
        <div className="container-custom section-padding">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-primary-100 text-primary-700 text-sm font-medium mb-6">
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              HIPAA Compliant • On-Premise Deployment
            </div>
            
            <h1 className="heading-1 mb-6">
              Automated Insurance Claims from EHR Data
            </h1>
            
            <p className="body-large mb-8 max-w-3xl mx-auto">
              Generate audit-ready insurance claims automatically from your EHR. 
              PHI-safe architecture with evidence citations for every code. 
              Seamless SMART on FHIR integration with Epic, Cerner, and more.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/contact" className="btn-primary btn-large">
                Book a Demo
              </Link>
              <Link href="/demo" className="btn-secondary btn-large">
                View Demo
              </Link>
            </div>

            <p className="mt-6 text-sm text-clinical-500">
              Trusted by hospitals and surgical centers nationwide
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-16">
            <h2 className="heading-2 mb-4">How It Works</h2>
            <p className="body-large max-w-2xl mx-auto">
              Four simple steps from EHR data to submission-ready claims
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                step: '1',
                title: 'Connect to EHR',
                description: 'Secure OAuth integration with Epic, Cerner, and other major EHR systems via SMART on FHIR',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                ),
              },
              {
                step: '2',
                title: 'Extract Clinical Data',
                description: 'Fetch patient encounters, diagnoses, procedures, and clinical notes via FHIR R4 API',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                ),
              },
              {
                step: '3',
                title: 'Generate Claim',
                description: 'Local AI processes clinical data to generate ICD-10, CPT, and HCPCS codes with confidence scores',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                ),
              },
              {
                step: '4',
                title: 'Audit-Ready Evidence',
                description: 'Every code linked to supporting clinical documentation with confidence ratings for review',
                icon: (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                ),
              },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="card text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 text-primary-600 mb-6">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      {item.icon}
                    </svg>
                  </div>
                  <div className="absolute top-8 left-4 w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-semibold text-clinical-900 mb-3">
                    {item.title}
                  </h3>
                  <p className="text-clinical-600">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-12">
            <Link href="/how-it-works" className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center">
              Learn more about our process
              <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* Compliance & Security */}
      <section className="section-padding bg-clinical-50">
        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="badge mb-6">Security & Compliance</div>
              <h2 className="heading-2 mb-6">
                Built for Healthcare Security Standards
              </h2>
              <p className="body-large mb-8">
                PHI never leaves your environment. Full HIPAA compliance with on-premise deployment, 
                encrypted databases, and comprehensive audit logging.
              </p>
              
              <div className="space-y-4">
                {[
                  {
                    title: 'PHI-Safe Processing',
                    description: 'All patient data processed on-premise with zero external API calls',
                  },
                  {
                    title: 'On-Premise Deployment',
                    description: 'Deploy within your hospital network with Docker-based infrastructure',
                  },
                  {
                    title: 'Complete Audit Logging',
                    description: 'Track every PHI access with immutable audit trails for compliance',
                  },
                  {
                    title: 'SMART on FHIR Integration',
                    description: 'Standards-compliant OAuth2 authentication with major EHR vendors',
                  },
                ].map((item, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-success-500 flex items-center justify-center mr-4 mt-1">
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-semibold text-clinical-900 mb-1">{item.title}</h4>
                      <p className="text-clinical-600">{item.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8">
                <Link href="/security" className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center">
                  View security details
                  <svg className="w-5 h-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              {[
                { label: 'HIPAA Compliant', icon: '🔒' },
                { label: 'SOC 2 Ready', icon: '✓' },
                { label: 'AES-256 Encryption', icon: '🛡️' },
                { label: '15-Min Session Timeout', icon: '⏱️' },
              ].map((item, index) => (
                <div key={index} className="card text-center">
                  <div className="text-4xl mb-3">{item.icon}</div>
                  <div className="text-sm font-medium text-clinical-900">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Who It's For */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="text-center mb-16">
            <h2 className="heading-2 mb-4">Who It's For</h2>
            <p className="body-large max-w-2xl mx-auto">
              Designed for healthcare organizations that demand accuracy, compliance, and efficiency
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                title: 'Hospitals',
                description: 'Streamline claim generation across departments with enterprise-grade security',
                icon: '🏥',
              },
              {
                title: 'Surgical Centers',
                description: 'Accelerate post-procedure billing with automated code extraction',
                icon: '⚕️',
              },
              {
                title: 'Billing Teams',
                description: 'Reduce manual coding time by 80% with AI-assisted claim generation',
                icon: '📊',
              },
              {
                title: 'Compliance Officers',
                description: 'Ensure audit readiness with evidence-backed codes and full traceability',
                icon: '✓',
              },
            ].map((item, index) => (
              <div key={index} className="card text-center hover:border-primary-300">
                <div className="text-5xl mb-4">{item.icon}</div>
                <h3 className="text-xl font-semibold text-clinical-900 mb-3">
                  {item.title}
                </h3>
                <p className="text-clinical-600">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <CTASection />
    </>
  )
}
