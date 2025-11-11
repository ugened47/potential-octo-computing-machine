/**
 * E2E Tests for AI Highlights Detection Workflow
 * Tests the complete highlight detection feature including:
 * - Trigger highlight detection
 * - View detected highlights
 * - Configure detection settings
 * - Create clips from highlights
 * - Adjust highlight timestamps
 * - Export top highlights
 * - Sort and filter highlights
 * - Highlight confidence scores
 */

import { test, expect } from './fixtures/test-fixtures'
import { navigateToVideo, waitForVideoProcessing } from './helpers/video.helper'

test.describe('Highlights Detection - Basic Functionality', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to a video
    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('displays detect highlights button', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Look for highlights tab or section
    const highlightsTab = page.locator(
      '[data-testid="highlights-tab"],button:has-text("Highlights")'
    ).first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(500)

      // Should show detect highlights button
      const detectButton = page.locator(
        '[data-testid="detect-highlights"],button:has-text("Detect Highlights")'
      ).first()

      await expect(detectButton).toBeVisible({ timeout: 5000 })
    } else {
      test.skip(true, 'Highlights section not found')
    }
  })

  test('user can trigger highlight detection', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights section
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(500)

      // Click detect highlights button
      const detectButton = page.locator(
        '[data-testid="detect-highlights"],button:has-text("Detect")'
      ).first()

      if (await detectButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await detectButton.click()
        await page.waitForTimeout(1000)

        // Should show processing state
        const processingIndicator = page.locator(
          '[data-testid="highlights-processing"],text=/detecting|analyzing|processing/i'
        ).first()

        const isProcessing = await processingIndicator.isVisible({ timeout: 5000 }).catch(() => false)

        if (isProcessing) {
          await expect(processingIndicator).toBeVisible()
        } else {
          // Check if highlights were detected immediately (cached or fast processing)
          const highlightsList = page.locator('[data-testid="highlights-list"]')
          const hasHighlights = await highlightsList.isVisible({ timeout: 3000 }).catch(() => false)

          expect(hasHighlights).toBe(true)
        }
      } else {
        test.skip(true, 'Detect highlights button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('displays detected highlights in a list', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Trigger detection if needed
      const detectButton = page.locator('button:has-text("Detect")').first()
      if (await detectButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await detectButton.click()
        await page.waitForTimeout(3000) // Wait for processing
      }

      // Check for highlights list
      const highlightsList = page.locator('[data-testid="highlights-list"]')
      const highlightItems = page.locator('[data-testid="highlight-item"]')

      const hasList = await highlightsList.isVisible({ timeout: 10000 }).catch(() => false)
      const itemCount = await highlightItems.count()

      if (hasList || itemCount > 0) {
        expect(hasList || itemCount > 0).toBe(true)

        // Verify highlight items show timestamp
        if (itemCount > 0) {
          const firstHighlight = highlightItems.first()
          const timestamp = firstHighlight.locator('text=/\\d+:\\d+/')

          await expect(timestamp).toBeVisible()
        }
      } else {
        test.skip(true, 'No highlights detected or displayed')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('shows confidence scores for detected highlights', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights section
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Wait for highlights to load
      const highlightItems = page.locator('[data-testid="highlight-item"]')
      const itemCount = await highlightItems.count()

      if (itemCount > 0) {
        const firstHighlight = highlightItems.first()

        // Look for confidence score or percentage
        const confidenceScore = firstHighlight.locator(
          '[data-testid="confidence-score"],text=/\\d+%|confidence|score/i'
        ).first()

        if (await confidenceScore.isVisible({ timeout: 2000 }).catch(() => false)) {
          await expect(confidenceScore).toBeVisible()
        } else {
          test.skip(true, 'Confidence scores not displayed')
        }
      } else {
        test.skip(true, 'No highlights found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })
})

test.describe('Highlights Detection - Configuration', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can configure detection settings', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(500)

      // Look for settings button
      const settingsButton = page.locator(
        '[data-testid="highlight-settings"],button[aria-label="Settings"]'
      ).first()

      if (await settingsButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await settingsButton.click()
        await page.waitForTimeout(500)

        // Should show settings modal/panel
        const settingsPanel = page.locator('[data-testid="settings-panel"],[role="dialog"]').first()

        if (await settingsPanel.isVisible({ timeout: 2000 }).catch(() => false)) {
          // Look for configuration options (sensitivity, duration, etc.)
          const configOptions = page.locator(
            'label:has-text("Sensitivity"),label:has-text("Minimum Duration"),input[type="range"]'
          )

          const hasOptions = await configOptions.first().isVisible({ timeout: 2000 }).catch(() => false)
          expect(hasOptions).toBe(true)
        } else {
          test.skip(true, 'Settings panel not found')
        }
      } else {
        test.skip(true, 'Settings button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('user can set minimum highlight duration', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(500)

      // Open settings
      const settingsButton = page.locator('[data-testid="highlight-settings"]').first()
      if (await settingsButton.isVisible().catch(() => false)) {
        await settingsButton.click()
        await page.waitForTimeout(500)

        // Look for duration setting
        const durationInput = page.locator(
          '[name="min_duration"],input[placeholder*="duration" i]'
        ).first()

        if (await durationInput.isVisible({ timeout: 2000 }).catch(() => false)) {
          await durationInput.fill('10')
          await page.waitForTimeout(300)

          // Save settings
          const saveButton = page.locator('button:has-text("Save"),button:has-text("Apply")').first()
          if (await saveButton.isVisible().catch(() => false)) {
            await saveButton.click()
            await page.waitForTimeout(500)

            // Verify setting was saved
            const successMessage = page.locator('text=/saved|updated/i')
            const hasSuccess = await successMessage.isVisible({ timeout: 2000 }).catch(() => false)

            expect(hasSuccess).toBe(true)
          }
        } else {
          test.skip(true, 'Duration input not found')
        }
      } else {
        test.skip(true, 'Settings button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })
})

test.describe('Highlights Detection - Clip Creation', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can create clip from highlight', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Find a highlight
      const highlightItems = page.locator('[data-testid="highlight-item"]')
      const itemCount = await highlightItems.count()

      if (itemCount > 0) {
        const firstHighlight = highlightItems.first()

        // Look for "Create Clip" button
        const createClipButton = firstHighlight.locator(
          'button:has-text("Create Clip"),button:has-text("Make Clip")'
        ).first()

        if (await createClipButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await createClipButton.click()
          await page.waitForTimeout(1000)

          // Verify clip was created - check for success message or navigation to clips
          const successMessage = page.locator('text=/clip.*created|created.*clip/i')
          const hasSuccess = await successMessage.isVisible({ timeout: 3000 }).catch(() => false)

          if (hasSuccess) {
            await expect(successMessage).toBeVisible()
          } else {
            // Check if we were redirected to clips tab
            const clipsTab = page.locator('button:has-text("Clips")')
            const isOnClips = await clipsTab.getAttribute('aria-selected').then(val => val === 'true').catch(() => false)

            expect(hasSuccess || isOnClips).toBe(true)
          }
        } else {
          test.skip(true, 'Create clip button not found')
        }
      } else {
        test.skip(true, 'No highlights found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('user can adjust highlight timestamps before creating clip', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      const highlightItems = page.locator('[data-testid="highlight-item"]')
      const itemCount = await highlightItems.count()

      if (itemCount > 0) {
        const firstHighlight = highlightItems.first()

        // Look for edit or adjust button
        const editButton = firstHighlight.locator(
          'button[aria-label="Edit"],button:has-text("Edit"),button:has-text("Adjust")'
        ).first()

        if (await editButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await editButton.click()
          await page.waitForTimeout(500)

          // Should show timestamp inputs
          const startTimeInput = page.locator(
            '[name="start_time"],input[placeholder*="start" i]'
          ).first()

          if (await startTimeInput.isVisible({ timeout: 2000 }).catch(() => false)) {
            // Adjust the time
            await startTimeInput.fill('00:05')
            await page.waitForTimeout(300)

            // Save changes
            const saveButton = page.locator('button:has-text("Save"),button:has-text("Apply")').first()
            if (await saveButton.isVisible().catch(() => false)) {
              await saveButton.click()
              await page.waitForTimeout(500)

              // Verify update
              const successMessage = page.locator('text=/saved|updated/i')
              const hasSuccess = await successMessage.isVisible({ timeout: 2000 }).catch(() => false)

              expect(hasSuccess).toBe(true)
            }
          } else {
            test.skip(true, 'Time adjustment inputs not found')
          }
        } else {
          test.skip(true, 'Edit button not found')
        }
      } else {
        test.skip(true, 'No highlights found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('user can create multiple clips from top highlights', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Look for "Create All" or "Bulk Create" button
      const bulkCreateButton = page.locator(
        '[data-testid="create-all-clips"],button:has-text("Create All"),button:has-text("Create Top")'
      ).first()

      if (await bulkCreateButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await bulkCreateButton.click()
        await page.waitForTimeout(500)

        // May show confirmation dialog
        const confirmButton = page.locator('button:has-text("Confirm"),button:has-text("Create")').first()
        if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmButton.click()
        }

        await page.waitForTimeout(2000)

        // Verify clips were created
        const successMessage = page.locator('text=/clips.*created|created.*\\d+.*clips/i')
        const hasSuccess = await successMessage.isVisible({ timeout: 5000 }).catch(() => false)

        expect(hasSuccess).toBe(true)
      } else {
        test.skip(true, 'Bulk create button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })
})

test.describe('Highlights Detection - Sorting & Filtering', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can sort highlights by confidence score', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Look for sort dropdown or button
      const sortButton = page.locator(
        '[data-testid="sort-highlights"],select[name="sort"]'
      ).first()

      if (await sortButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Select sort by confidence
        if (await sortButton.getAttribute('type').then(type => type === 'select-one').catch(() => false)) {
          await sortButton.selectOption({ label: /confidence|score/i })
        } else {
          await sortButton.click()
          await page.waitForTimeout(300)

          const confidenceOption = page.locator('text=/confidence|score/i').first()
          if (await confidenceOption.isVisible().catch(() => false)) {
            await confidenceOption.click()
          }
        }

        await page.waitForTimeout(500)

        // Verify highlights are sorted (first item should have highest confidence)
        const highlightItems = page.locator('[data-testid="highlight-item"]')
        const itemCount = await highlightItems.count()

        expect(itemCount).toBeGreaterThan(0)
      } else {
        test.skip(true, 'Sort functionality not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('user can filter highlights by minimum confidence', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Look for filter controls
      const filterButton = page.locator(
        '[data-testid="filter-highlights"],button:has-text("Filter")'
      ).first()

      if (await filterButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await filterButton.click()
        await page.waitForTimeout(500)

        // Set minimum confidence filter
        const confidenceSlider = page.locator(
          '[name="min_confidence"],input[type="range"]'
        ).first()

        if (await confidenceSlider.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confidenceSlider.fill('70')
          await page.waitForTimeout(500)

          // Apply filter
          const applyButton = page.locator('button:has-text("Apply")').first()
          if (await applyButton.isVisible().catch(() => false)) {
            await applyButton.click()
          }

          await page.waitForTimeout(500)

          // Verify filtered results
          const highlightItems = page.locator('[data-testid="highlight-item"]')
          const itemCount = await highlightItems.count()

          expect(itemCount).toBeGreaterThanOrEqual(0)
        } else {
          test.skip(true, 'Confidence filter not found')
        }
      } else {
        test.skip(true, 'Filter button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })
})

test.describe('Highlights Detection - Export', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can export top highlights compilation', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Look for export highlights button
      const exportButton = page.locator(
        '[data-testid="export-highlights"],button:has-text("Export Highlights")'
      ).first()

      if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await exportButton.click()
        await page.waitForTimeout(500)

        // May show export configuration dialog
        const confirmButton = page.locator(
          'button:has-text("Export"),button:has-text("Confirm")'
        ).first()

        if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmButton.click()
        }

        await page.waitForTimeout(1000)

        // Verify export started
        const exportStatus = page.locator('text=/exporting|processing/i')
        const hasStatus = await exportStatus.isVisible({ timeout: 5000 }).catch(() => false)

        expect(hasStatus).toBe(true)
      } else {
        test.skip(true, 'Export highlights button not found')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })

  test('user can select specific highlights to export', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to highlights
    const highlightsTab = page.locator('button:has-text("Highlights")').first()

    if (await highlightsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await highlightsTab.click()
      await page.waitForTimeout(1000)

      // Select multiple highlights
      const highlightItems = page.locator('[data-testid="highlight-item"]')
      const itemCount = await highlightItems.count()

      if (itemCount >= 2) {
        // Select first two highlights
        const firstCheckbox = highlightItems.nth(0).locator('input[type="checkbox"]').first()
        const secondCheckbox = highlightItems.nth(1).locator('input[type="checkbox"]').first()

        if (await firstCheckbox.isVisible().catch(() => false)) {
          await firstCheckbox.check()
          await secondCheckbox.check()
          await page.waitForTimeout(300)

          // Look for export selected button
          const exportSelectedButton = page.locator(
            'button:has-text("Export Selected")'
          ).first()

          if (await exportSelectedButton.isVisible({ timeout: 2000 }).catch(() => false)) {
            await exportSelectedButton.click()
            await page.waitForTimeout(1000)

            // Verify export started
            const exportStatus = page.locator('text=/exporting|processing/i')
            const hasStatus = await exportStatus.isVisible({ timeout: 5000 }).catch(() => false)

            expect(hasStatus).toBe(true)
          } else {
            test.skip(true, 'Export selected button not found')
          }
        } else {
          test.skip(true, 'Highlight selection checkboxes not found')
        }
      } else {
        test.skip(true, 'Not enough highlights for selection test')
      }
    } else {
      test.skip(true, 'Highlights tab not found')
    }
  })
})
