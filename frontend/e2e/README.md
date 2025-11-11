# E2E Test Suite Documentation

## Overview

This directory contains comprehensive End-to-End (E2E) tests for the AI Video Clipper application. The tests are built using **Playwright** and follow best practices for test organization, maintainability, and reliability.

## Test Coverage

### Frontend E2E Tests

1. **Authentication** (`auth.spec.ts`)
   - User registration and login
   - Password validation
   - Session management
   - Protected routes
   - Password reset
   - User profile management

2. **Video Workflow** (`video-workflow.spec.ts`)
   - Video upload and listing
   - Video detail pages
   - Video processing status
   - Video deletion
   - Responsive design

3. **Transcription** (`transcription.spec.ts`)
   - Starting transcription
   - Viewing transcripts
   - Searching within transcripts
   - Clickable transcript segments
   - Transcript export
   - Progress tracking

4. **Timeline Editor** (`timeline-editor.spec.ts`)
   - Waveform display
   - Playback controls
   - Timeline seeking
   - Segment operations (create, select, delete, resize, move)
   - Zoom and navigation
   - Undo/redo operations

5. **Silence Removal** (`silence-removal.spec.ts`)
   - Silence detection
   - Threshold adjustment
   - Preview and validation
   - Processing with progress tracking
   - Statistics display

6. **Keyword Search & Clipping** (`keyword-search-clipping.spec.ts`)
   - Keyword search in transcripts
   - Search results with timestamps
   - Clip creation from search results
   - Clip duration and buffer settings
   - Clip management (view, delete, export)

7. **Dashboard** (`dashboard.spec.ts`)
   - Dashboard statistics
   - Video list/grid display
   - Search and filtering
   - Sorting and pagination
   - Empty states
   - Quick actions

8. **Error Handling** (`error-handling.spec.ts`)
   - Network errors and retries
   - Invalid inputs and validation
   - Authorization errors
   - Missing resources (404)
   - Concurrent operations
   - Edge cases and data boundaries

### Backend E2E Tests

Located in `backend/tests/e2e/`:

1. **Full Workflow** (`test_full_workflow.py`)
   - Complete user journey
   - Workflow integration
   - Error handling

2. **Comprehensive Workflows** (`test_comprehensive_workflows.py`)
   - Video lifecycle
   - Transcription workflow
   - Clip creation workflow
   - Silence removal workflow
   - Timeline editing workflow
   - Dashboard stats
   - Concurrent operations
   - User data isolation
   - Pagination, filtering, and sorting

## Test Structure

### Directory Layout

```
frontend/e2e/
├── README.md                           # This file
├── auth.spec.ts                        # Authentication tests
├── video-workflow.spec.ts              # Video management tests
├── transcription.spec.ts               # Transcription feature tests
├── timeline-editor.spec.ts             # Timeline editing tests
├── silence-removal.spec.ts             # Silence removal tests
├── keyword-search-clipping.spec.ts     # Keyword search & clipping tests
├── dashboard.spec.ts                   # Dashboard tests
├── error-handling.spec.ts              # Error handling tests
├── fixtures/
│   └── test-fixtures.ts                # Playwright fixtures
└── helpers/
    ├── auth.helper.ts                  # Authentication utilities
    ├── video.helper.ts                 # Video utilities
    └── api.helper.ts                   # API utilities
```

## Running Tests

### Prerequisites

```bash
cd frontend
npm install
```

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Specific Test File

```bash
npx playwright test auth.spec.ts
```

### Run in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### Run in Debug Mode

```bash
npx playwright test --debug
```

### Run on Specific Browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Run Only Failed Tests

```bash
npx playwright test --last-failed
```

## Test Best Practices

### 1. Test Independence

- Each test should be independent and not rely on other tests
- Use fixtures to set up test data
- Clean up after tests when necessary

```typescript
test('example test', async ({ authenticatedPage }) => {
  const { page } = authenticatedPage
  // Test automatically has authenticated user
})
```

### 2. Use Helper Functions

- Reuse common actions through helper functions
- Keep tests readable and maintainable

```typescript
import { login, logout } from './helpers/auth.helper'
import { uploadVideo } from './helpers/video.helper'
```

### 3. Flexible Assertions

- Tests are designed to work with evolving UI
- Use flexible selectors that work across implementations
- Gracefully handle optional features

```typescript
// Multiple selector strategies
const button = page.locator(
  'button:has-text("Upload"),
   a[href="/upload"],
   [data-testid="upload-button"]'
).first()

// Check if feature exists before testing
if (await button.isVisible({ timeout: 3000 }).catch(() => false)) {
  await button.click()
} else {
  test.skip(true, 'Feature not implemented')
}
```

### 4. Avoid Hard Timeouts

- Use dynamic waits instead of fixed timeouts when possible
- Use `.waitForTimeout()` sparingly

```typescript
// Good: Wait for specific condition
await page.waitForURL(/\/dashboard/)

// Acceptable: Small wait for UI updates
await page.waitForTimeout(500)

// Avoid: Long fixed waits
// await page.waitForTimeout(5000)
```

### 5. Error Handling

- Wrap potentially failing operations in try-catch or .catch()
- Provide meaningful error messages

```typescript
const hasFeature = await element.isVisible().catch(() => false)

if (!hasFeature) {
  test.skip(true, 'Feature not available')
}
```

### 6. Data Generation

- Use unique test data to avoid collisions
- Generate timestamps or UUIDs for uniqueness

```typescript
const user = generateTestUser() // Creates unique user with timestamp
```

## Test Fixtures

### authenticatedPage

Automatically creates and logs in a test user:

```typescript
test('example', async ({ authenticatedPage }) => {
  const { page, user } = authenticatedPage
  // page is authenticated
  // user contains credentials
})
```

### apiClient

Provides authenticated API client for direct API calls:

```typescript
test('example', async ({ apiClient }) => {
  // Make API calls directly
})
```

## Helper Functions

### Authentication Helpers

```typescript
// Generate unique test user
const user = generateTestUser()

// Register new user
await registerUser(page, user)

// Login
await login(page, user)

// Logout
await logout(page)

// Check if logged in
const isLoggedIn = await isLoggedIn(page)
```

### Video Helpers

```typescript
// Create fake video file
const file = createFakeVideoFile(100) // 100KB

// Upload video
const videoId = await uploadVideo(page, file, 'My Video')

// Navigate to video
await navigateToVideo(page, videoId)

// Delete video
await deleteVideo(page, videoId)

// Wait for processing
await waitForVideoProcessing(page)
```

### API Helpers

```typescript
// Create API client
const client = await createAPIClient(page, token)

// Register user via API
const { token, userId } = await registerUserAPI(request, email, password)

// Create video via API
const videoId = await createVideoAPI(request, client, title)
```

## Debugging Tests

### View Test Report

```bash
npx playwright show-report
```

### Take Screenshots on Failure

Screenshots are automatically taken on failure and saved to `test-results/`.

### Use Playwright Inspector

```bash
npx playwright test --debug
```

### Enable Trace Viewer

Traces are automatically captured on first retry. View with:

```bash
npx playwright show-trace trace.zip
```

## CI/CD Integration

Tests are configured to run in CI with:
- 2 retries on failure
- GitHub Actions reporter
- Sequential execution (not parallel)
- Screenshots and videos on failure

See `playwright.config.ts` for configuration.

## Test Maintenance

### Adding New Tests

1. Create new test file or add to existing file
2. Use appropriate fixtures and helpers
3. Follow existing naming conventions
4. Add documentation for complex scenarios

### Updating Tests

1. Keep tests synchronized with feature changes
2. Update selectors if UI changes
3. Add new scenarios as features evolve
4. Remove obsolete tests

### Common Issues

#### Test Timeouts

- Increase timeout for slow operations
- Check if application is actually slow
- Use more specific waits instead of fixed timeouts

#### Flaky Tests

- Ensure proper waits for async operations
- Check for race conditions
- Use Playwright's auto-waiting features
- Avoid hard-coded timeouts

#### Selector Issues

- Use multiple selector strategies
- Prefer data-testid attributes
- Use text content as fallback
- Make selectors flexible

## Code Quality

### Test Organization

- Group related tests in `describe` blocks
- Use descriptive test names
- Keep tests focused and concise
- One assertion concept per test

### Code Style

- Use TypeScript for type safety
- Follow ESLint rules
- Use async/await consistently
- Comment complex logic

### Documentation

- Add JSDoc comments for helpers
- Document complex test scenarios
- Keep README up to date
- Add examples for common patterns

## Performance

### Test Execution Speed

- Run tests in parallel when possible
- Use API calls for setup when appropriate
- Avoid unnecessary navigation
- Reuse browser contexts when safe

### Resource Usage

- Clean up test data when needed
- Close browser contexts properly
- Manage file uploads efficiently
- Monitor test execution time

## Security

### Test Data

- Never commit real credentials
- Use environment variables for secrets
- Generate unique test data
- Clean up sensitive data after tests

### API Access

- Use test-specific API endpoints when available
- Limit test user permissions
- Validate authorization in tests
- Test security scenarios explicitly

## Future Improvements

- [ ] Add visual regression testing
- [ ] Add performance testing
- [ ] Add accessibility testing
- [ ] Expand mobile testing
- [ ] Add load testing scenarios
- [ ] Integrate with monitoring tools

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Best Practices Guide](https://playwright.dev/docs/best-practices)
- [Test Fixtures](https://playwright.dev/docs/test-fixtures)
- [Selectors Guide](https://playwright.dev/docs/selectors)

## Support

For questions or issues:
1. Check existing test examples
2. Review Playwright documentation
3. Check test helper functions
4. Ask team members
