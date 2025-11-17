import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  Sim,
  SimCreate,
  UsageRecord,
  Quota,
  LoginRequest,
  AuthResponse,
  User,
  HealthCheck
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, clear it
          this.clearToken()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )

    // Load token from localStorage on client side
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  getToken(): string | null {
    return this.token
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await this.client.post<AuthResponse>(
      '/api/v1/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    )

    if (response.data.access_token) {
      this.setToken(response.data.access_token)
    }

    return response.data
  }

  async logout(): Promise<void> {
    this.clearToken()
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/v1/auth/me')
    return response.data
  }

  // Health check
  async healthCheck(): Promise<HealthCheck> {
    const response = await this.client.get<HealthCheck>('/health')
    return response.data
  }

  // SIM endpoints
  async getSims(skip = 0, limit = 100): Promise<Sim[]> {
    const response = await this.client.get<Sim[]>('/api/v1/sims', {
      params: { skip, limit },
    })
    return response.data
  }

  async getSim(iccid: string): Promise<Sim> {
    const response = await this.client.get<Sim>(`/api/v1/sims/${iccid}`)
    return response.data
  }

  async createSim(data: SimCreate): Promise<Sim> {
    const response = await this.client.post<Sim>('/api/v1/sims', data)
    return response.data
  }

  async deleteSim(iccid: string): Promise<void> {
    await this.client.delete(`/api/v1/sims/${iccid}`)
  }

  async syncSims(): Promise<{ synced: number; message: string }> {
    const response = await this.client.post<{ synced: number; message: string }>(
      '/api/v1/sims/sync'
    )
    return response.data
  }

  // Usage endpoints
  async getUsage(
    iccid: string,
    startDate?: string,
    endDate?: string
  ): Promise<UsageRecord[]> {
    const response = await this.client.get<UsageRecord[]>(
      `/api/v1/usage/${iccid}`,
      {
        params: { start_date: startDate, end_date: endDate },
      }
    )
    return response.data
  }

  async syncUsage(iccid: string): Promise<{ synced: number; message: string }> {
    const response = await this.client.post<{ synced: number; message: string }>(
      `/api/v1/usage/${iccid}/sync`
    )
    return response.data
  }

  // Quota endpoints
  async getQuotas(iccid: string): Promise<Quota[]> {
    const response = await this.client.get<Quota[]>(`/api/v1/quotas/${iccid}`)
    return response.data
  }

  async getQuota(iccid: string, quotaType: 'data' | 'sms'): Promise<Quota> {
    const response = await this.client.get<Quota>(
      `/api/v1/quotas/${iccid}/${quotaType}`
    )
    return response.data
  }

  async syncQuota(
    iccid: string,
    quotaType: 'data' | 'sms'
  ): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      `/api/v1/quotas/${iccid}/${quotaType}/sync`
    )
    return response.data
  }
}

// Export singleton instance
export const apiClient = new ApiClient()
export default apiClient
