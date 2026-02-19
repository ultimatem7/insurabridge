export const metadata = {
  title: 'Privacy Policy - Insurabridge',
  description: 'Insurabridge privacy policy and data handling practices.',
}

export default function Privacy() {
  return (
    <section className="section-padding bg-white">
      <div className="container-custom max-w-4xl">
        <h1 className="heading-1 mb-8">Privacy Policy</h1>
        
        <div className="prose prose-lg max-w-none">
          <p className="text-clinical-600 mb-8">
            <strong>Last Updated:</strong> February 2024
          </p>

          <div className="space-y-8">
            <div>
              <h2 className="heading-3 mb-4">Our Commitment to Privacy</h2>
              <p className="text-clinical-600">
                Insurabridge is committed to protecting the privacy and security of protected health information (PHI) 
                in accordance with HIPAA regulations. This Privacy Policy explains how we collect, use, and protect 
                information when you use our healthcare claims automation platform.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">Information We Collect</h2>
              <h3 className="text-xl font-semibold text-clinical-900 mb-3">Protected Health Information (PHI)</h3>
              <p className="text-clinical-600 mb-4">
                When you use Insurabridge to generate insurance claims, the system processes:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Patient demographics (name, date of birth, address)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Clinical encounter data (visit dates, provider information)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Diagnosis codes and medical conditions</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Procedure codes and treatment information</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Clinical notes and documentation</span>
                </li>
              </ul>

              <h3 className="text-xl font-semibold text-clinical-900 mb-3 mt-6">Non-PHI Information</h3>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>User account information (email, name, organization)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>System usage logs (feature usage, error reports)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Performance metrics (anonymized, aggregated)</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">How We Use Information</h2>
              <ul className="space-y-3 text-clinical-600">
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Claim Generation:</strong> PHI is processed locally to extract diagnosis and procedure codes</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>Evidence Linking:</strong> Supporting documentation is referenced for audit trails</span>
                </li>
                <li className="flex items-start">
                  <svg className="w-5 h-5 text-primary-600 mr-3 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span><strong>System Improvement:</strong> Non-PHI usage data helps improve platform features</span>
                </li>
              </ul>
            </div>

            <div className="card bg-primary-50 border-2 border-primary-200">
              <h2 className="heading-3 mb-4">PHI Protection Policy</h2>
              <p className="text-clinical-700 mb-4">
                <strong>All PHI processing occurs on-premise within your hospital network.</strong>
              </p>
              <ul className="space-y-2 text-clinical-700">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>PHI is never transmitted to external servers</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Local AI models process clinical data within your environment</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>No cloud storage or external API calls with PHI</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Data remains under your organization's control at all times</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">Data Retention</h2>
              <p className="text-clinical-600 mb-4">
                Data retention periods are configurable based on your organization's policies:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span><strong>Generated Claims:</strong> Retained per your internal policy (default: 7 years)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span><strong>Audit Logs:</strong> Retained for 7 years (HIPAA requirement)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span><strong>Session Data:</strong> Automatically purged after 15 minutes of inactivity</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">Your Rights</h2>
              <p className="text-clinical-600 mb-4">
                As a healthcare organization using Insurabridge, you have:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Complete control over PHI within your deployment</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Access to all audit logs and system activity</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Ability to configure data retention policies</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Right to export or delete all stored data</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">Security Measures</h2>
              <p className="text-clinical-600 mb-4">
                We implement industry-standard security controls:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>AES-256 encryption for data at rest</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>TLS 1.3 for data in transit</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Bcrypt password hashing with salt</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>JWT token-based authentication with refresh rotation</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Role-based access controls</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Comprehensive audit logging</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">Contact Us</h2>
              <p className="text-clinical-600">
                For questions about this Privacy Policy or our data practices, contact us at:{' '}
                <a href="mailto:privacy@insura.bridge" className="text-primary-600 hover:underline">
                  privacy@insura.bridge
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
