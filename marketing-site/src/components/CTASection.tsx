import Link from 'next/link'

export default function CTASection() {
  return (
    <section className="section-padding bg-primary-600">
      <div className="container-custom">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Claims Process?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Schedule a personalized demo and see how Insurabridge can reduce claim processing time 
            while improving accuracy and compliance.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              href="/contact"
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-medium rounded-lg text-primary-600 bg-white hover:bg-primary-50 transition-colors duration-200"
            >
              Book a Demo
            </Link>
            <Link 
              href="/demo"
              className="inline-flex items-center justify-center px-8 py-4 text-lg font-medium rounded-lg text-white border-2 border-white hover:bg-primary-700 transition-colors duration-200"
            >
              View Demo
            </Link>
          </div>
          <p className="mt-6 text-sm text-primary-200">
            No credit card required • 30-minute live demo • Custom deployment options
          </p>
        </div>
      </div>
    </section>
  )
}
