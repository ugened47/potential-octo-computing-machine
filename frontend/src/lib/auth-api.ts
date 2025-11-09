/** API client for authentication operations. */

import { apiRequest } from "./api-client";
import { setToken, removeToken } from "./token-storage";
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
} from "@/types/auth";

/**
 * Login user.
 */
export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });

  // Store token
  setToken(response.access_token);

  return response;
}

/**
 * Register new user.
 */
export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });

  // Store token
  setToken(response.access_token);

  return response;
}

/**
 * Logout user.
 */
export async function logout(): Promise<void> {
  removeToken();
}

/**
 * Get current user.
 */
export async function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/api/v1/auth/me", {
    method: "GET",
  });
}

/**
 * Request password reset.
 */
export async function requestPasswordReset(email: string): Promise<void> {
  return apiRequest<void>("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

/**
 * Reset password.
 */
export async function resetPassword(
  token: string,
  newPassword: string,
): Promise<void> {
  return apiRequest<void>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}
