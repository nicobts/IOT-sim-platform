// API Response Types
export interface ApiResponse<T> {
  data: T
  message?: string
  status: string
}

// SIM Types
export interface Sim {
  id: number
  iccid: string
  imsi?: string
  msisdn?: string
  status: string
  operator?: string
  country?: string
  ip_address?: string
  imei?: string
  created_at: string
  updated_at: string
  last_status_update?: string
}

export interface SimCreate {
  iccid: string
  imsi?: string
  msisdn?: string
}

// Usage Types
export interface UsageRecord {
  id: number
  sim_id: number
  iccid: string
  timestamp: string
  volume_rx_bytes: number
  volume_tx_bytes: number
  total_bytes: number
  total_mb: number
}

// Quota Types
export interface Quota {
  id: number
  sim_id: number
  iccid: string
  quota_type: 'data' | 'sms'
  volume_total: number
  volume_used: number
  volume_remaining: number
  threshold_percentage?: number
  threshold_volume?: number
  auto_topup: boolean
  status: string
  last_updated: string
  expires_at?: string
}

// Auth Types
export interface LoginRequest {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
}

// Health Check
export interface HealthCheck {
  status: string
  timestamp: string
  version?: string
  database?: string
  redis?: string
  once_api?: string
}
