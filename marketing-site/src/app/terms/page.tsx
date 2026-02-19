export const metadata = {
  title: 'Terms of Service - Insurabridge',
  description: 'Terms of service for using the Insurabridge healthcare claims automation platform.',
}

export default function Terms() {
  return (
    <section className="section-padding bg-white">
      <div className="container-custom max-w-4xl">
        <h1 className="heading-1 mb-8">Terms of Service</h1>
        
        <div className="prose prose-lg max-w-none">
          <p className="text-clinical-600 mb-8">
            <strong>Last Updated:</strong> February 2024
          </p>

          <div className="space-y-8">
            <div>
              <h2 className="heading-3 mb-4">1. Acceptance of Terms</h2>
              <p className="text-clinical-600">
                By accessing or using Insurabridge ("the Service"), you agree to be bound by these Terms of Service 
                ("Terms"). If you do not agree to these Terms, do not use the Service.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">2. Description of Service</h2>
              <p className="text-clinical-600 mb-4">
                Insurabridge is a healthcare claims automation platform that:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Integrates with Electronic Health Record (EHR) systems via SMART on FHIR</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Extracts clinical data and documentation</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Generates structured insurance claim data using AI assistance</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Provides evidence citations and audit trails</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">3. On-Premise Deployment</h2>
              <p className="text-clinical-600">
                Insurabridge is designed for on-premise deployment within your organization's network. 
                You retain complete control and ownership of all data processed by the system. 
                We do not host, store, or have access to your PHI.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">4. User Responsibilities</h2>
              <p className="text-clinical-600 mb-4">You agree to:</p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Maintain the security of your account credentials</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Use the Service only for lawful purposes</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Review all AI-generated claims before submission to payers</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Comply with all applicable healthcare regulations</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Maintain appropriate physical and technical safeguards</span>
                </li>
              </ul>
            </div>

            <div className="card bg-yellow-50 border-2 border-yellow-300">
              <h2 className="heading-3 mb-4">5. AI-Assisted Coding Disclaimer</h2>
              <p className="text-clinical-700 font-medium mb-3">
                IMPORTANT: Human Review Required
              </p>
              <p className="text-clinical-600">
                Insurabridge provides AI-assisted suggestions for medical codes. All AI-generated codes and claims 
                MUST be reviewed and approved by qualified medical coding professionals before submission to payers. 
                The Service is a tool to assist, not replace, human medical coders. Your organization is responsible 
                for the accuracy and appropriateness of all submitted claims.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">6. HIPAA and Compliance</h2>
              <p className="text-clinical-600 mb-4">
                For on-premise deployments:
              </p>
              <ul className="space-y-2 text-clinical-600">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>You remain the Covered Entity or Business Associate</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>You are responsible for ensuring HIPAA compliance of your deployment</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>We provide HIPAA-conscious architecture and security features</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Business Associate Agreements available for hosted deployments</span>
                </li>
              </ul>
            </div>

            <div>
              <h2 className="heading-3 mb-4">7. Limitation of Liability</h2>
              <p className="text-clinical-600">
                To the maximum extent permitted by law, Insurabridge shall not be liable for any indirect, 
                incidental, special, consequential, or punitive damages resulting from use of the Service, 
                including but not limited to claim denials, payment delays, or coding errors. The Service is 
                provided "as is" without warranties of any kind.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">8. Intellectual Property</h2>
              <p className="text-clinical-600">
                The Service, including all software, algorithms, documentation, and branding, is owned by 
                Insurabridge and protected by copyright, trademark, and other intellectual property laws. 
                You receive a limited license to use the Service; you do not acquire ownership rights.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">9. Modifications to Service</h2>
              <p className="text-clinical-600">
                We reserve the right to modify, suspend, or discontinue any aspect of the Service at any time. 
                We will provide reasonable notice of significant changes that may impact your use.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">10. Termination</h2>
              <p className="text-clinical-600">
                Either party may terminate the service agreement with written notice. Upon termination, 
                you must cease use of the Service and may export or delete all data in your deployment.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">11. Governing Law</h2>
              <p className="text-clinical-600">
                These Terms shall be governed by and construed in accordance with the laws of the United States 
                and applicable state laws, without regard to conflict of law principles.
              </p>
            </div>

            <div>
              <h2 className="heading-3 mb-4">12. Contact Information</h2>
              <p className="text-clinical-600">
                For questions about these Terms, contact us at:{' '}
                <a href="mailto:legal@insura.bridge" className="text-primary-600 hover:underline">
                  legal@insura.bridge
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
