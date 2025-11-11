/**
 * API helper functions for E2E tests
 * Provides utilities for direct API calls to set up test data
 */

import { Page, APIRequestContext } from '@playwright/test'

export interface APIClient {
  token: string | null
  baseURL: string
}

/**
 * Create an authenticated API client
 */
export async function createAPIClient(
  page: Page,
  token?: string
): Promise<APIClient> {
  const authToken = token || (await getTokenFromPage(page))

  return {
    token: authToken,
    baseURL: process.env.API_BASE_URL || 'http://localhost:8000',
  }
}

/**
 * Get auth token from page
 */
async function getTokenFromPage(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return (
      localStorage.getItem('access_token') ||
      localStorage.getItem('token') ||
      sessionStorage.getItem('access_token') ||
      sessionStorage.getItem('token')
    )
  })
}

/**
 * Make authenticated API request
 */
export async function apiRequest(
  request: APIRequestContext,
  client: APIClient,
  method: string,
  endpoint: string,
  data?: any
): Promise<any> {
  const url = `${client.baseURL}${endpoint}`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (client.token) {
    headers['Authorization'] = `Bearer ${client.token}`
  }

  const response = await request.fetch(url, {
    method,
    headers,
    data: data ? JSON.stringify(data) : undefined,
  })

  if (response.ok()) {
    return await response.json().catch(() => null)
  }

  throw new Error(`API request failed: ${response.status()} ${response.statusText()}`)
}

/**
 * Register user via API
 */
export async function registerUserAPI(
  request: APIRequestContext,
  email: string,
  password: string,
  fullName?: string
): Promise<{ token: string; userId: string }> {
  const baseURL = process.env.API_BASE_URL || 'http://localhost:8000'

  const response = await request.post(`${baseURL}/api/v1/auth/register`, {
    data: {
      email,
      password,
      full_name: fullName || 'Test User',
    },
  })

  if (!response.ok()) {
    throw new Error(`Registration failed: ${response.status()}`)
  }

  const data = await response.json()

  return {
    token: data.access_token,
    userId: data.user?.id || data.id,
  }
}

/**
 * Login via API
 */
export async function loginAPI(
  request: APIRequestContext,
  email: string,
  password: string
): Promise<string> {
  const baseURL = process.env.API_BASE_URL || 'http://localhost:8000'

  const response = await request.post(`${baseURL}/api/v1/auth/login`, {
    data: {
      email,
      password,
    },
  })

  if (!response.ok()) {
    throw new Error(`Login failed: ${response.status()}`)
  }

  const data = await response.json()

  return data.access_token
}

/**
 * Create video via API
 */
export async function createVideoAPI(
  request: APIRequestContext,
  client: APIClient,
  title: string,
  s3Key?: string
): Promise<string> {
  const response = await request.post(`${client.baseURL}/api/v1/videos`, {
    headers: {
      Authorization: `Bearer ${client.token}`,
    },
    data: {
      title,
      s3_key: s3Key || `videos/test-${Date.now()}.mp4`,
      duration: 120,
      file_size: 1024 * 1024,
    },
  })

  if (!response.ok()) {
    throw new Error(`Create video failed: ${response.status()}`)
  }

  const data = await response.json()

  return data.id
}

/**
 * Get video details via API
 */
export async function getVideoAPI(
  request: APIRequestContext,
  client: APIClient,
  videoId: string
): Promise<any> {
  const response = await request.get(`${client.baseURL}/api/v1/videos/${videoId}`, {
    headers: {
      Authorization: `Bearer ${client.token}`,
    },
  })

  if (!response.ok()) {
    throw new Error(`Get video failed: ${response.status()}`)
  }

  return await response.json()
}

/**
 * Delete video via API
 */
export async function deleteVideoAPI(
  request: APIRequestContext,
  client: APIClient,
  videoId: string
): Promise<void> {
  const response = await request.delete(`${client.baseURL}/api/v1/videos/${videoId}`, {
    headers: {
      Authorization: `Bearer ${client.token}`,
    },
  })

  if (!response.ok() && response.status() !== 404) {
    throw new Error(`Delete video failed: ${response.status()}`)
  }
}

/**
 * Wait for API endpoint to be ready
 */
export async function waitForAPIReady(
  request: APIRequestContext,
  baseURL: string,
  timeoutMs = 30000
): Promise<boolean> {
  const startTime = Date.now()

  while (Date.now() - startTime < timeoutMs) {
    try {
      const response = await request.get(`${baseURL}/api/health`)
      if (response.ok()) {
        return true
      }
    } catch (error) {
      // API not ready yet
    }

    await new Promise((resolve) => setTimeout(resolve, 1000))
  }

  return false
}
