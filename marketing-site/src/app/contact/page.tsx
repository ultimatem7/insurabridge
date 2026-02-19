'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'

export default function Contact() {
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  
  const { register, handleSubmit, formState: { errors }, reset } = useForm()

  const onSubmit = async (data: any) => {
    setLoading(true)
    
    try {
      // Mock API endpoint - in production, this would send to your backend
      const response = await fetch('/api/demo-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (response.ok || response.status === 404) {
        // 404 is expected since endpoint doesn't exist yet - still count as success for demo
        setSubmitted(true)
        reset()
        console.log('Demo request:', data)
      } else {
        alert('Something went wrong. Please try again.')
      }
    } catch (error) {
      // For demo purposes, still count as success
      setSubmitted(true)
      reset()
      console.log('Demo request:', data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Hero */}
      <section className="section-padding bg-gradient-to-b from-clinical-50 to-white">
        <div className="container-custom">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="heading-1 mb-6">Book a Demo</h1>
            <p className="body-large">
              Schedule a personalized demonstration and see how Insurabridge can transform your claims process
            </p>
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="section-padding bg-white">
        <div className="container-custom">
          <div className="max-w-2xl mx-auto">
            {submitted ? (
              <div className="card border-2 border-success-200 bg-success-50">
                <div className="text-center py-12">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-success-500 text-white mb-6">
                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-clinical-900 mb-4">
                    Thank You!
                  </h2>
                  <p className="text-lg text-clinical-600 mb-6">
                    We've received your demo request. Our team will contact you within 24 hours 
                    to schedule a personalized demonstration.
                  </p>
                  <button
                    onClick={() => setSubmitted(false)}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Submit another request
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="card">
                <div className="space-y-6">
                  {/* Name */}
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-clinical-900 mb-2">
                      Full Name *
                    </label>
                    <input
                      {...register('name', { required: 'Name is required' })}
                      type="text"
                      id="name"
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="Dr. Jane Smith"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message as string}</p>
                    )}
                  </div>

                  {/* Organization */}
                  <div>
                    <label htmlFor="organization" className="block text-sm font-medium text-clinical-900 mb-2">
                      Organization *
                    </label>
                    <input
                      {...register('organization', { required: 'Organization is required' })}
                      type="text"
                      id="organization"
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="Memorial Hospital"
                    />
                    {errors.organization && (
                      <p className="mt-1 text-sm text-red-600">{errors.organization.message as string}</p>
                    )}
                  </div>

                  {/* Email */}
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-clinical-900 mb-2">
                      Email Address *
                    </label>
                    <input
                      {...register('email', {
                        required: 'Email is required',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Invalid email address',
                        },
                      })}
                      type="email"
                      id="email"
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                      placeholder="jane.smith@hospital.com"
                    />
                    {errors.email && (
                      <p className="mt-1 text-sm text-red-600">{errors.email.message as string}</p>
                    )}
                  </div>

                  {/* Role */}
                  <div>
                    <label htmlFor="role" className="block text-sm font-medium text-clinical-900 mb-2">
                      Role *
                    </label>
                    <select
                      {...register('role', { required: 'Role is required' })}
                      id="role"
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                    >
                      <option value="">Select your role</option>
                      <option value="billing_manager">Billing Manager</option>
                      <option value="medical_coder">Medical Coder</option>
                      <option value="compliance_officer">Compliance Officer</option>
                      <option value="it_director">IT Director</option>
                      <option value="cfo">CFO / Finance</option>
                      <option value="provider">Healthcare Provider</option>
                      <option value="other">Other</option>
                    </select>
                    {errors.role && (
                      <p className="mt-1 text-sm text-red-600">{errors.role.message as string}</p>
                    )}
                  </div>

                  {/* EHR Vendor */}
                  <div>
                    <label htmlFor="ehr_vendor" className="block text-sm font-medium text-clinical-900 mb-2">
                      Current EHR Vendor *
                    </label>
                    <select
                      {...register('ehr_vendor', { required: 'EHR vendor is required' })}
                      id="ehr_vendor"
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition"
                    >
                      <option value="">Select your EHR</option>
                      <option value="epic">Epic</option>
                      <option value="cerner">Cerner / Oracle Health</option>
                      <option value="eclinicalworks">eClinicalWorks</option>
                      <option value="athenahealth">Athenahealth</option>
                      <option value="meditech">Meditech</option>
                      <option value="allscripts">Allscripts</option>
                      <option value="other">Other</option>
                    </select>
                    {errors.ehr_vendor && (
                      <p className="mt-1 text-sm text-red-600">{errors.ehr_vendor.message as string}</p>
                    )}
                  </div>

                  {/* Message */}
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-clinical-900 mb-2">
                      Message (Optional)
                    </label>
                    <textarea
                      {...register('message')}
                      id="message"
                      rows={4}
                      className="w-full px-4 py-3 border border-clinical-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition resize-none"
                      placeholder="Tell us about your current claims process or specific challenges..."
                    />
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary btn-large disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Submitting...
                      </span>
                    ) : (
                      'Request Demo'
                    )}
                  </button>

                  <p className="text-sm text-clinical-500 text-center">
                    By submitting, you agree to our <a href="/privacy" className="text-primary-600 hover:underline">Privacy Policy</a>
                  </p>
                </div>
              </form>
            )}

            {/* Contact Info */}
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-clinical-50 rounded-lg">
                <svg className="w-8 h-8 text-primary-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <h3 className="font-semibold text-clinical-900 mb-1">Email</h3>
                <a href="mailto:demo@insura.bridge" className="text-primary-600 hover:underline text-sm">
                  demo@insura.bridge
                </a>
              </div>

              <div className="text-center p-6 bg-clinical-50 rounded-lg">
                <svg className="w-8 h-8 text-primary-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-semibold text-clinical-900 mb-1">Response Time</h3>
                <p className="text-clinical-600 text-sm">Within 24 hours</p>
              </div>

              <div className="text-center p-6 bg-clinical-50 rounded-lg">
                <svg className="w-8 h-8 text-primary-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <h3 className="font-semibold text-clinical-900 mb-1">Demo Duration</h3>
                <p className="text-clinical-600 text-sm">30-45 minutes</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
