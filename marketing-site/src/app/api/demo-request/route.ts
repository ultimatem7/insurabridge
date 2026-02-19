import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validate required fields
    const requiredFields = ['name', 'organization', 'email', 'role', 'ehr_vendor']
    for (const field of requiredFields) {
      if (!body[field]) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        )
      }
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(body.email)) {
      return NextResponse.json(
        { error: 'Invalid email address' },
        { status: 400 }
      )
    }
    
    // Log demo request (in production, save to database or send to CRM)
    console.log('Demo Request Received:', {
      name: body.name,
      organization: body.organization,
      email: body.email,
      role: body.role,
      ehr_vendor: body.ehr_vendor,
      message: body.message,
      timestamp: new Date().toISOString(),
    })
    
    // In production, you would:
    // 1. Save to database
    // 2. Send email notification to sales team
    // 3. Add to CRM (Salesforce, HubSpot, etc.)
    // 4. Send confirmation email to requester
    
    // For now, just return success
    return NextResponse.json(
      {
        success: true,
        message: 'Demo request received. We will contact you within 24 hours.',
        request_id: `DEMO-${Date.now()}`,
      },
      { status: 200 }
    )
    
  } catch (error) {
    console.error('Error processing demo request:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Handle other HTTP methods
export async function GET() {
  return NextResponse.json(
    { error: 'Method not allowed. Use POST to submit demo requests.' },
    { status: 405 }
  )
}
