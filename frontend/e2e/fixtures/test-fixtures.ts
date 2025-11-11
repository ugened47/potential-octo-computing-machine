/**
 * Playwright test fixtures for E2E tests
 * Provides reusable setup and teardown logic
 */

import { test as base, expect } from '@playwright/test'
import {
  setupAuthenticatedSession,
  TestUser,
  clearAuthState,
} from '../helpers/auth.helper'
import { createAPIClient, APIClient } from '../helpers/api.helper'

// Extend base test with custom fixtures
export const test = base.extend<{
  authenticatedPage: { page: any; user: TestUser }
  apiClient: APIClient
}>({
  // Fixture: Authenticated user session
  authenticatedPage: async ({ page }, use) => {
    // Setup: Create and login user
    const user = await setupAuthenticatedSession(page)

    // Provide authenticated page to test
    await use({ page, user })

    // Teardown: Clear auth state
    await clearAuthState(page)
  },

  // Fixture: API client
  apiClient: async ({ page }, use) => {
    const client = await createAPIClient(page)

    await use(client)
  },
})

export { expect }
