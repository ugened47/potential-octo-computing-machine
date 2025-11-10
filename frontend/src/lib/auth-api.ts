// Authentication API client
import { tokenStorage } from "./token-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface PasswordResetRequestData {
  email: string;
}

export interface PasswordResetData {
  token: string;
  new_password: string;
}

class AuthAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = tokenStorage.getAccessToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    if (
      token &&
      !endpoint.includes("/login") &&
      !endpoint.includes("/register")
    ) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshed = await this.refreshToken();
      if (refreshed) {
        // Retry original request
        headers["Authorization"] = `Bearer ${tokenStorage.getAccessToken()}`;
        const retryResponse = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        });
        if (!retryResponse.ok) {
          const error = await retryResponse
            .json()
            .catch(() => ({ message: retryResponse.statusText }));
          throw new Error(error.message || "API request failed");
        }
        return retryResponse.json();
      } else {
        tokenStorage.clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        throw new Error("Session expired");
      }
    }

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ message: response.statusText }));
      throw new Error(error.message || error.detail || "API request failed");
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  /**
   * Register a new user account
   * @param data - Registration data (email, password, optional full_name)
   * @returns Authentication response with tokens and user data
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    return this.request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * Login with email and password
   * @param data - Login credentials (email, password)
   * @returns Authentication response with tokens and user data
   */
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    tokenStorage.setTokens(response.access_token, response.refresh_token);
    return response;
  }

  /**
   * Logout the current user
   * Clears local tokens and calls backend logout endpoint
   */
  async logout(): Promise<void> {
    try {
      await this.request("/api/auth/logout", { method: "POST" });
    } finally {
      tokenStorage.clear();
    }
  }

  /**
   * Refresh the access token using the refresh token
   * @returns True if refresh successful, false otherwise
   */
  async refreshToken(): Promise<boolean> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await this.request<AuthResponse>("/api/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      tokenStorage.setTokens(response.access_token, response.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get the current authenticated user's profile
   * @returns User profile data
   */
  async getCurrentUser(): Promise<User> {
    return this.request<User>("/api/auth/me");
  }

  /**
   * Update the current user's profile
   * @param data - Partial user data to update
   * @returns Updated user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    return this.request<User>("/api/auth/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * Request a password reset email
   * @param email - Email address to send reset link to
   */
  async requestPasswordReset(email: string): Promise<void> {
    await this.request("/api/auth/password-reset-request", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  /**
   * Reset password using a reset token
   * @param token - Password reset token from email
   * @param newPassword - New password to set
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.request("/api/auth/password-reset", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  }

  /**
   * Change password for authenticated user
   * @param currentPassword - Current password
   * @param newPassword - New password to set
   */
  async changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<void> {
    await this.request("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
  }

  /**
   * Check if user is authenticated
   * @returns True if user has a valid token
   */
  isAuthenticated(): boolean {
    return tokenStorage.hasValidToken();
  }

  /**
   * Verify email address with token
   * @param token - Email verification token
   */
  async verifyEmail(token: string): Promise<void> {
    await this.request("/api/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  }

  /**
   * Resend email verification link
   */
  async resendVerificationEmail(): Promise<void> {
    await this.request("/api/auth/resend-verification", {
      method: "POST",
    });
  }
}

export const authAPI = new AuthAPI();
