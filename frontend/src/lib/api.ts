/**
 * API Client for Insurabridge Backend
 * 
 * Handles authentication, request signing, and error handling.
 * All requests go to local backend - no external calls.
 */

const API_BASE = '/api/v1'

interface ApiError {
  message: string
  status: number
  detail?: string
}

class ApiClient {
  private accessToken: string | null = null
  private refreshToken: string | null = null

  setTokens(access: string, refresh: string) {
    this.accessToken = access
    this.refreshToken = refresh
    // In production, store in secure httpOnly cookie
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('access_token', access)
      sessionStorage.setItem('refresh_token', refresh)
    }
  }

  loadTokens() {
    if (typeof window !== 'undefined') {
      this.accessToken = sessionStorage.getItem('access_token')
      this.refreshToken = sessionStorage.getItem('refresh_token')
    }
  }

  clearTokens() {
    this.accessToken = null
    this.refreshToken = null
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
    }
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: { skipAuth?: boolean }
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (!options?.skipAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`
    }

    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
      // Try to refresh token on 401
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken()
        if (refreshed) {
          // Retry original request
          headers['Authorization'] = `Bearer ${this.accessToken}`
          const retryResponse = await fetch(`${API_BASE}${path}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined,
          })
          
          if (retryResponse.ok) {
            return retryResponse.json()
          }
        }
      }

      const error: ApiError = {
        message: 'Request failed',
        status: response.status,
      }

      try {
        const data = await response.json()
        error.detail = data.detail || data.message
      } catch {
        error.detail = response.statusText
      }

      throw error
    }

    return response.json()
  }

  private async refreshAccessToken(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      })

      if (response.ok) {
        const data = await response.json()
        this.setTokens(data.access_token, data.refresh_token)
        return true
      }
    } catch {
      // Refresh failed
    }

    this.clearTokens()
    return false
  }

  // Auth endpoints
  async login(email: string, password: string) {
    const data = await this.request<{
      access_token: string
      refresh_token: string
      expires_in: number
    }>('POST', '/auth/login', { email, password }, { skipAuth: true })
    
    this.setTokens(data.access_token, data.refresh_token)
    return data
  }

  async logout() {
    await this.request('POST', '/auth/logout')
    this.clearTokens()
  }

  async getCurrentUser() {
    return this.request<{
      id: string
      email: string
      full_name: string
      role: string
    }>('GET', '/auth/me')
  }

  // Claims endpoints
  async generateClaim(data: {
    clinical_text?: string
    encounter_id?: string
    payer_id?: string
    claim_type?: string
  }) {
    return this.request('POST', '/claims/generate', data)
  }

  async uploadAndGenerateClaim(file: File, payerId?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (payerId) formData.append('payer_id', payerId)

    const response = await fetch(`${API_BASE}/claims/generate/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Upload failed')
    }

    return response.json()
  }

  async getClaim(id: string) {
    return this.request('GET', `/claims/${id}`)
  }

  async listClaims(params?: { page?: number; status?: string }) {
    const query = new URLSearchParams()
    if (params?.page) query.set('page', String(params.page))
    if (params?.status) query.set('status', params.status)
    
    return this.request('GET', `/claims?${query}`)
  }

  async validateClaim(claimId: string) {
    return this.request('POST', '/claims/validate', { claim_id: claimId })
  }

  // Denials endpoints
  async recordDenial(data: {
    claim_id: string
    denial_date: string
    denial_reason: string
    denied_amount: number
    denial_code?: string
  }) {
    return this.request('POST', '/denials', data)
  }

  async getDenial(id: string) {
    return this.request('GET', `/denials/${id}`)
  }

  async generateAppeal(denialId: string, additionalContext?: string) {
    return this.request('POST', '/denials/appeals/generate', {
      denial_id: denialId,
      additional_context: additionalContext,
    })
  }

  // Code lookup endpoints
  async searchICD10(query: string, limit = 10) {
    return this.request('GET', `/codes/icd10?q=${encodeURIComponent(query)}&limit=${limit}`)
  }

  async searchCPT(query: string, limit = 10) {
    return this.request('GET', `/codes/cpt?q=${encodeURIComponent(query)}&limit=${limit}`)
  }

  async checkNCCI(codes: string[]) {
    return this.request('POST', '/codes/ncci-check', { codes })
  }

  // Audit endpoints
  async getAuditLogs(params?: {
    event_types?: string[]
    user_id?: string
    start_time?: string
    end_time?: string
    limit?: number
  }) {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.user_id) query.set('user_id', params.user_id)
    
    return this.request('GET', `/audit/logs?${query}`)
  }

  async generateRiskReport(startDate?: string, endDate?: string) {
    const query = new URLSearchParams()
    if (startDate) query.set('start_date', startDate)
    if (endDate) query.set('end_date', endDate)
    
    return this.request('GET', `/audit/risk-report?${query}`)
  }
}

export const api = new ApiClient()

// Initialize tokens on load
if (typeof window !== 'undefined') {
  api.loadTokens()
}

