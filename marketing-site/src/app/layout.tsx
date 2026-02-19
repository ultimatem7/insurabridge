import type { Metadata } from 'next'
import './globals.css'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export const metadata: Metadata = {
  title: 'Insurabridge - AI-Powered Healthcare Claims Automation',
  description: 'Automated insurance claim generation from EHR data with audit-ready evidence. HIPAA-compliant, on-premise deployment with SMART on FHIR integration.',
  keywords: 'healthcare claims, EHR integration, medical billing, insurance claims automation, HIPAA compliant, FHIR, Epic, Cerner',
  authors: [{ name: 'Insurabridge' }],
  openGraph: {
    title: 'Insurabridge - AI-Powered Healthcare Claims Automation',
    description: 'Automated insurance claim generation from EHR data with audit-ready evidence.',
    type: 'website',
    locale: 'en_US',
    siteName: 'Insurabridge',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Insurabridge - AI-Powered Healthcare Claims Automation',
    description: 'Automated insurance claim generation from EHR data with audit-ready evidence.',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body>
        <Header />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
