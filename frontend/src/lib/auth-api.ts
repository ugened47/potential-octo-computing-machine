/** Authentication API client. */

import { apiPost, apiGet, apiPatch } from './api-client'
import { tokenStorage } from './token-storage'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  email: string
  password: string
  full_name?: string
}

export interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserUpdate {
  email?: string
  full_name?: string
  password?: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  password: string
}

/**
 * Login with email and password.
 * @param email - User email
 * @param password - User password
 * @returns Login response with access token and user data
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  // FastAPI OAuth2 expects form data for login
  const formData = new URLSearchParams()
  formData.append('username', email) // OAuth2 uses 'username' field
  formData.append('password', password)

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/auth/login`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    }
  )

  if (!response.ok) {
    throw new Error('Login failed')
  }

  const data = await response.json()

  // Store tokens
  tokenStorage.setToken(data.access_token)
  if (data.refresh_token) {
    tokenStorage.setRefreshToken(data.refresh_token)
  }

  return data
}

/**
 * Register a new user.
 * @param data - Registration data
 * @returns Created user
 */
export async function register(data: RegisterRequest): Promise<User> {
  return apiPost<User>('/auth/register', data, { requireAuth: false })
}

/**
 * Get current authenticated user.
 * @returns Current user data
 */
export async function getCurrentUser(): Promise<User> {
  return apiGet<User>('/auth/me')
}

/**
 * Update current user profile.
 * @param data - Fields to update
 * @returns Updated user
 */
export async function updateUser(data: UserUpdate): Promise<User> {
  return apiPatch<User>('/auth/me', data)
}

/**
 * Request password reset.
 * @param email - User email
 */
export async function forgotPassword(email: string): Promise<void> {
  return apiPost('/auth/forgot-password', { email }, { requireAuth: false })
}

/**
 * Reset password with token.
 * @param token - Reset token from email
 * @param password - New password
 */
export async function resetPassword(token: string, password: string): Promise<void> {
  return apiPost('/auth/reset-password', { token, password }, { requireAuth: false })
}

/**
 * Logout the current user.
 */
export function logout(): void {
  tokenStorage.clearAll()
  if (typeof window !== 'undefined') {
    window.location.href = '/login'
  }
}
