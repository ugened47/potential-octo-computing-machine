/** Token storage utilities for JWT authentication. */

const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const tokenStorage = {
  /**
   * Get the stored authentication token.
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  },

  /**
   * Store the authentication token.
   */
  setToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEY, token)
  },

  /**
   * Remove the authentication token.
   */
  removeToken(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEY)
  },

  /**
   * Get the stored refresh token.
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },

  /**
   * Store the refresh token.
   */
  setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },

  /**
   * Remove the refresh token.
   */
  removeRefreshToken(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },

  /**
   * Check if a valid token exists.
   */
  hasValidToken(): boolean {
    const token = this.getToken()
    if (!token) return false

    // Check if token is expired (basic JWT parsing)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() < exp
    } catch {
      return false
    }
  },

  /**
   * Clear all auth data.
   */
  clearAll(): void {
    this.removeToken()
    this.removeRefreshToken()
  },
}
