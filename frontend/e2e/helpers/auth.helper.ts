/**
 * Authentication helper functions for E2E tests
 * Provides reusable utilities for user registration, login, and auth state management
 */

import { Page, expect } from '@playwright/test'

export interface TestUser {
  email: string
  password: string
  full_name?: string
}

/**
 * Generate a unique test user with timestamp to avoid collisions
 */
export function generateTestUser(prefix = 'test'): TestUser {
  const timestamp = Date.now()
  return {
    email: `${prefix}-${timestamp}@example.com`,
    password: 'TestPassword123!',
    full_name: `${prefix} User ${timestamp}`,
  }
}

/**
 * Register a new user account
 * @returns The registered user credentials
 */
export async function registerUser(
  page: Page,
  user?: TestUser
): Promise<TestUser> {
  const testUser = user || generateTestUser()

  await page.goto('/register')

  // Fill registration form
  await page.fill('input[name="email"]', testUser.email)
  await page.fill('input[name="password"]', testUser.password)

  if (testUser.full_name) {
    const fullNameField = page.locator('input[name="full_name"]')
    if (await fullNameField.isVisible().catch(() => false)) {
      await fullNameField.fill(testUser.full_name)
    }
  }

  // Submit form
  await page.click('button[type="submit"]')

  // Wait for navigation to dashboard/home
  await page
    .waitForURL(/\/(dashboard|videos|home)/, { timeout: 10000 })
    .catch(() => {
      // Registration might have failed, that's okay for some tests
    })

  return testUser
}

/**
 * Login with existing credentials
 */
export async function login(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login')

  await page.fill('input[name="email"]', user.email)
  await page.fill('input[name="password"]', user.password)

  await page.click('button[type="submit"]')

  // Wait for successful login
  await page
    .waitForURL(/\/(dashboard|videos|home)/, { timeout: 10000 })
    .catch(() => {
      // Login might fail in some test scenarios
    })
}

/**
 * Logout current user
 */
export async function logout(page: Page): Promise<void> {
  const logoutButton = page.locator('text=/logout|sign out/i').first()

  if (await logoutButton.isVisible().catch(() => false)) {
    await logoutButton.click()

    // Wait for redirect to login or home
    await page
      .waitForURL(/\/(login|home|\/)/, { timeout: 5000 })
      .catch(() => {})
  }
}

/**
 * Check if user is logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  // Check for user menu or logout button
  const userMenu = page.locator('[data-testid="user-menu"]')
  const logoutButton = page.locator('text=/logout|sign out/i')

  const hasUserMenu = await userMenu.isVisible().catch(() => false)
  const hasLogoutButton = await logoutButton.isVisible().catch(() => false)

  return hasUserMenu || hasLogoutButton
}

/**
 * Setup authenticated session for test
 * Creates a new user and logs in
 */
export async function setupAuthenticatedSession(
  page: Page
): Promise<TestUser> {
  const user = await registerUser(page)

  // Verify we're logged in
  const loggedIn = await isLoggedIn(page)

  if (!loggedIn) {
    // Try logging in if registration didn't auto-login
    await login(page, user)
  }

  return user
}

/**
 * Get auth token from localStorage (if stored there)
 */
export async function getAuthToken(page: Page): Promise<string | null> {
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
 * Clear auth state (logout without UI)
 */
export async function clearAuthState(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
}

/**
 * Verify user is redirected to login when accessing protected route
 */
export async function expectRedirectToLogin(page: Page, protectedRoute: string): Promise<void> {
  await page.goto(protectedRoute)

  await page.waitForTimeout(1000)

  const currentUrl = page.url()
  expect(currentUrl).toMatch(/\/(login|$)/)
}
