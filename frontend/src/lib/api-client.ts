/** Base API client with authentication and error handling. */

import { tokenStorage } from './token-storage'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }
}

export interface RequestOptions extends RequestInit {
  requireAuth?: boolean
  params?: Record<string, string | number | boolean | undefined>
}

/**
 * Make an authenticated API request.
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requireAuth = true, params, ...fetchOptions } = options

  // Build URL with query parameters
  let url = `${API_BASE_URL}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  // Setup headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  }

  // Add authentication token if required
  if (requireAuth) {
    const token = tokenStorage.getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  // Make request
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    })

    // Handle non-OK responses
    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json()
      } catch {
        errorData = { detail: response.statusText }
      }

      // Handle 401 Unauthorized - clear token and redirect
      if (response.status === 401) {
        tokenStorage.clearAll()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }

      throw new ApiError(response.status, response.statusText, errorData)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T
    }

    // Parse JSON response
    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    // Network or other errors
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`)
  }
}

/**
 * GET request helper.
 */
export async function apiGet<T = any>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'GET' })
}

/**
 * POST request helper.
 */
export async function apiPost<T = any>(
  endpoint: string,
  data?: any,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT request helper.
 */
export async function apiPut<T = any>(
  endpoint: string,
  data?: any,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PATCH request helper.
 */
export async function apiPatch<T = any>(
  endpoint: string,
  data?: any,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE request helper.
 */
export async function apiDelete<T = any>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'DELETE' })
}

/**
 * Upload file with progress tracking.
 */
export async function apiUploadFile(
  url: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    // Track upload progress
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100
          onProgress(progress)
        }
      })
    }

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve()
      } else {
        reject(new ApiError(xhr.status, xhr.statusText))
      }
    })

    xhr.addEventListener('error', () => {
      reject(new Error('Upload failed'))
    })

    xhr.open('PUT', url)
    xhr.setRequestHeader('Content-Type', file.type)
    xhr.send(file)
  })
}
