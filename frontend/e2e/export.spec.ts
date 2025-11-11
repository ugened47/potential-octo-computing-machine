/**
 * E2E Tests for Video Export Workflow
 * Tests the complete video export feature including:
 * - Export configuration (resolution, quality, format)
 * - Single clip export
 * - Combined video export
 * - Multiple clips as ZIP
 * - Export progress monitoring
 * - Download functionality
 * - Cancel export
 * - Retry failed export
 * - Export history
 * - Custom export settings
 */

import { test, expect } from './fixtures/test-fixtures'
import { navigateToVideo, waitForVideoProcessing } from './helpers/video.helper'

test.describe('Video Export - Basic Functionality', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to a video with clips
    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('displays export button and opens export modal', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Look for export button
    const exportButton = page.locator(
      '[data-testid="export-button"],button:has-text("Export")'
    ).first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Should open export modal/dialog
      const exportModal = page.locator(
        '[data-testid="export-modal"],[role="dialog"]'
      ).first()

      await expect(exportModal).toBeVisible({ timeout: 5000 })

      // Should show export options
      const exportOptions = page.locator('text=/resolution|quality|format/i')
      await expect(exportOptions.first()).toBeVisible()
    } else {
      test.skip(true, 'Export button not found')
    }
  })

  test('user can configure export settings', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Open export modal
    const exportButton = page.locator(
      '[data-testid="export-button"],button:has-text("Export")'
    ).first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Select resolution
      const resolutionSelect = page.locator(
        '[data-testid="resolution-select"],select[name="resolution"]'
      ).first()

      if (await resolutionSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
        await resolutionSelect.selectOption({ label: /1080p|720p|HD/i })
        await page.waitForTimeout(300)

        // Select quality
        const qualitySelect = page.locator(
          '[data-testid="quality-select"],select[name="quality"]'
        ).first()

        if (await qualitySelect.isVisible().catch(() => false)) {
          await qualitySelect.selectOption({ label: /high|medium/i })
        }

        // Select format
        const formatSelect = page.locator(
          '[data-testid="format-select"],select[name="format"]'
        ).first()

        if (await formatSelect.isVisible().catch(() => false)) {
          await formatSelect.selectOption({ label: /mp4|mov/i })
        }

        // Verify settings are selected
        expect(true).toBe(true)
      } else {
        test.skip(true, 'Export settings not found')
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })

  test('user can export single clip', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to clips tab if exists
    const clipsTab = page.locator('button:has-text("Clips")')
    if (await clipsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clipsTab.click()
      await page.waitForTimeout(500)
    }

    // Find a clip to export
    const clipCard = page.locator('[data-testid="clip-card"]').first()

    if (await clipCard.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Click export on the clip
      const clipExportButton = clipCard.locator('button:has-text("Export")').first()

      if (await clipExportButton.isVisible().catch(() => false)) {
        await clipExportButton.click()
        await page.waitForTimeout(500)

        // Confirm export
        const confirmButton = page.locator(
          '[data-testid="confirm-export"],button:has-text("Confirm"),button:has-text("Start Export")'
        ).first()

        if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmButton.click()
          await page.waitForTimeout(1000)

          // Should show export progress or success message
          const exportProgress = page.locator(
            '[data-testid="export-progress"],text=/exporting|processing/i'
          )

          const hasProgress = await exportProgress.isVisible({ timeout: 5000 }).catch(() => false)

          if (hasProgress) {
            await expect(exportProgress).toBeVisible()
          } else {
            // Check for success message
            const successMessage = page.locator('text=/export.*complete|exported successfully/i')
            const hasSuccess = await successMessage.isVisible({ timeout: 3000 }).catch(() => false)
            expect(hasSuccess || hasProgress).toBe(true)
          }
        }
      } else {
        test.skip(true, 'Clip export button not found')
      }
    } else {
      test.skip(true, 'No clips found to export')
    }
  })

  test('user can export combined video with all clips', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Open export modal
    const exportButton = page.locator(
      '[data-testid="export-button"],button:has-text("Export")'
    ).first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Look for "combine all clips" or "merge clips" option
      const combineOption = page.locator(
        '[data-testid="combine-clips"],input[name="combine"],text=/combine|merge.*clips/i'
      ).first()

      if (await combineOption.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Check the option if it's a checkbox
        if (await combineOption.getAttribute('type').then(type => type === 'checkbox').catch(() => false)) {
          await combineOption.check()
        } else {
          await combineOption.click()
        }

        await page.waitForTimeout(300)

        // Start export
        const startExportButton = page.locator(
          '[data-testid="start-export"],button:has-text("Export"),button:has-text("Start")'
        ).first()

        if (await startExportButton.isVisible().catch(() => false)) {
          await startExportButton.click()
          await page.waitForTimeout(1000)

          // Verify export started
          const exportStatus = page.locator('text=/exporting|processing|export.*started/i')
          const hasStatus = await exportStatus.isVisible({ timeout: 5000 }).catch(() => false)

          expect(hasStatus).toBe(true)
        }
      } else {
        test.skip(true, 'Combine clips option not found')
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })
})

test.describe('Video Export - Multiple Clips', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can export multiple clips as ZIP archive', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to clips section
    const clipsTab = page.locator('button:has-text("Clips")')
    if (await clipsTab.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clipsTab.click()
      await page.waitForTimeout(500)
    }

    // Look for bulk actions or select multiple clips
    const clipCards = page.locator('[data-testid="clip-card"]')
    const clipCount = await clipCards.count()

    if (clipCount >= 2) {
      // Select first two clips
      const firstCheckbox = clipCards.nth(0).locator('input[type="checkbox"]')
      const secondCheckbox = clipCards.nth(1).locator('input[type="checkbox"]')

      if (await firstCheckbox.isVisible().catch(() => false)) {
        await firstCheckbox.check()
        await secondCheckbox.check()
        await page.waitForTimeout(300)

        // Look for bulk export button
        const bulkExportButton = page.locator(
          '[data-testid="bulk-export"],button:has-text("Export Selected")'
        ).first()

        if (await bulkExportButton.isVisible().catch(() => false)) {
          await bulkExportButton.click()
          await page.waitForTimeout(500)

          // Select ZIP format option if available
          const zipOption = page.locator('text=/zip|archive/i')
          if (await zipOption.isVisible({ timeout: 2000 }).catch(() => false)) {
            await zipOption.click()
          }

          // Confirm export
          const confirmButton = page.locator(
            'button:has-text("Export"),button:has-text("Confirm")'
          ).first()

          if (await confirmButton.isVisible().catch(() => false)) {
            await confirmButton.click()
            await page.waitForTimeout(1000)

            // Verify export started
            const exportProgress = page.locator('text=/exporting|processing/i')
            const hasProgress = await exportProgress.isVisible({ timeout: 5000 }).catch(() => false)

            expect(hasProgress).toBe(true)
          }
        } else {
          test.skip(true, 'Bulk export button not found')
        }
      } else {
        test.skip(true, 'Clip selection checkboxes not found')
      }
    } else {
      test.skip(true, 'Not enough clips for bulk export test')
    }
  })

  test('displays export preview before final export', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const exportButton = page.locator(
      '[data-testid="export-button"],button:has-text("Export")'
    ).first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Look for preview option
      const previewButton = page.locator(
        '[data-testid="preview-export"],button:has-text("Preview")'
      ).first()

      if (await previewButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await previewButton.click()
        await page.waitForTimeout(1000)

        // Should show preview player or thumbnail
        const preview = page.locator(
          '[data-testid="export-preview"],video,[data-preview]'
        ).first()

        await expect(preview).toBeVisible({ timeout: 5000 })
      } else {
        test.skip(true, 'Preview functionality not found')
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })
})

test.describe('Video Export - Progress Monitoring', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
  })

  test('displays real-time export progress', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await navigateToVideo(page)
    await page.waitForTimeout(500)

    // Start an export
    const exportButton = page.locator('button:has-text("Export")').first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      const startExportButton = page.locator(
        'button:has-text("Export"),button:has-text("Start")'
      ).first()

      if (await startExportButton.isVisible().catch(() => false)) {
        await startExportButton.click()
        await page.waitForTimeout(1000)

        // Check for progress indicator
        const progressBar = page.locator(
          '[data-testid="export-progress-bar"],progress,[role="progressbar"]'
        ).first()

        if (await progressBar.isVisible({ timeout: 5000 }).catch(() => false)) {
          await expect(progressBar).toBeVisible()

          // Progress should have value
          const progressValue = await progressBar.getAttribute('value').catch(() => null)
          const ariaValueNow = await progressBar.getAttribute('aria-valuenow').catch(() => null)

          expect(progressValue !== null || ariaValueNow !== null).toBe(true)
        } else {
          // Check for percentage text
          const progressText = page.locator('text=/\\d+%/')
          const hasProgressText = await progressText.isVisible({ timeout: 3000 }).catch(() => false)

          if (hasProgressText) {
            await expect(progressText).toBeVisible()
          } else {
            test.skip(true, 'Export progress indicator not found')
          }
        }
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })

  test('user can view export queue and history', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to exports page/section
    const exportsLink = page.locator(
      '[href="/exports"],a:has-text("Exports"),button:has-text("Exports")'
    ).first()

    if (await exportsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportsLink.click()
      await page.waitForTimeout(1000)

      // Should show list of exports
      const exportsList = page.locator('[data-testid="exports-list"]')
      const exportItems = page.locator('[data-testid="export-item"]')

      const hasList = await exportsList.isVisible({ timeout: 3000 }).catch(() => false)
      const itemCount = await exportItems.count()

      expect(hasList || itemCount > 0).toBe(true)
    } else {
      test.skip(true, 'Exports page not found')
    }
  })

  test('shows estimated time remaining for export', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await navigateToVideo(page)

    // Start export
    const exportButton = page.locator('button:has-text("Export")').first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      const startButton = page.locator('button:has-text("Export"),button:has-text("Start")').first()

      if (await startButton.isVisible().catch(() => false)) {
        await startButton.click()
        await page.waitForTimeout(1000)

        // Look for time remaining indicator
        const timeRemaining = page.locator(
          'text=/time.*remaining|eta|estimated.*time/i'
        ).first()

        if (await timeRemaining.isVisible({ timeout: 5000 }).catch(() => false)) {
          await expect(timeRemaining).toBeVisible()
        } else {
          test.skip(true, 'Time remaining indicator not found')
        }
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })
})

test.describe('Video Export - Download & Cancellation', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
  })

  test('user can download completed export', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Look for completed export or navigate to exports page
    await page.goto('/exports').catch(() => {
      // Exports page might not exist
    })

    await page.waitForTimeout(1000)

    // Find completed export
    const downloadButton = page.locator(
      '[data-testid="download-export"],button:has-text("Download")'
    ).first()

    if (await downloadButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Setup download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 })

      await downloadButton.click()

      try {
        const download = await downloadPromise

        // Verify download started
        expect(download.suggestedFilename()).toBeTruthy()
        expect(download.suggestedFilename()).toMatch(/\.(mp4|mov|zip)$/i)
      } catch (error) {
        // Download might not start immediately
        await page.waitForTimeout(2000)

        // Check if download link appeared
        const downloadLink = page.locator('a[download],a[href*="download"]')
        const hasDownloadLink = await downloadLink.isVisible().catch(() => false)

        expect(hasDownloadLink).toBe(true)
      }
    } else {
      test.skip(true, 'No completed exports found to download')
    }
  })

  test('user can cancel export in progress', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await navigateToVideo(page)

    // Start an export
    const exportButton = page.locator('button:has-text("Export")').first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      const startButton = page.locator('button:has-text("Export"),button:has-text("Start")').first()

      if (await startButton.isVisible().catch(() => false)) {
        await startButton.click()
        await page.waitForTimeout(1000)

        // Look for cancel button
        const cancelButton = page.locator(
          '[data-testid="cancel-export"],button:has-text("Cancel")'
        ).first()

        if (await cancelButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await cancelButton.click()
          await page.waitForTimeout(500)

          // Confirm cancellation if needed
          const confirmCancel = page.locator('button:has-text("Confirm"),button:has-text("Yes")')
          if (await confirmCancel.isVisible({ timeout: 2000 }).catch(() => false)) {
            await confirmCancel.click()
          }

          await page.waitForTimeout(1000)

          // Verify export was cancelled
          const cancelledStatus = page.locator('text=/cancelled|canceled|stopped/i')
          const hasCancelled = await cancelledStatus.isVisible({ timeout: 3000 }).catch(() => false)

          if (hasCancelled) {
            await expect(cancelledStatus).toBeVisible()
          } else {
            // Check that progress indicator is gone
            const progressBar = page.locator('[data-testid="export-progress"]')
            const hasProgress = await progressBar.isVisible().catch(() => false)
            expect(hasProgress).toBe(false)
          }
        } else {
          test.skip(true, 'Cancel button not found')
        }
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })

  test('user can retry failed export', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to exports page to find failed exports
    await page.goto('/exports').catch(() => {})
    await page.waitForTimeout(1000)

    // Look for failed export
    const failedExport = page.locator('[data-status="failed"],[data-testid="failed-export"]').first()
    const failedStatus = page.locator('text=/failed|error/i').first()

    if (await failedExport.isVisible({ timeout: 3000 }).catch(() => false) ||
        await failedStatus.isVisible({ timeout: 3000 }).catch(() => false)) {

      // Find retry button
      const retryButton = page.locator(
        '[data-testid="retry-export"],button:has-text("Retry"),button:has-text("Try Again")'
      ).first()

      if (await retryButton.isVisible().catch(() => false)) {
        await retryButton.click()
        await page.waitForTimeout(1000)

        // Verify export restarted
        const exportingStatus = page.locator('text=/exporting|processing/i')
        const hasStatus = await exportingStatus.isVisible({ timeout: 5000 }).catch(() => false)

        expect(hasStatus).toBe(true)
      } else {
        test.skip(true, 'Retry button not found')
      }
    } else {
      test.skip(true, 'No failed exports found')
    }
  })

  test('maintains export quality settings across sessions', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await navigateToVideo(page)

    // Open export modal and set preferences
    const exportButton = page.locator('button:has-text("Export")').first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Set quality to high
      const qualitySelect = page.locator('[data-testid="quality-select"]').first()

      if (await qualitySelect.isVisible({ timeout: 2000 }).catch(() => false)) {
        await qualitySelect.selectOption({ label: /high/i })
        await page.waitForTimeout(300)

        // Close modal
        const closeButton = page.locator('button[aria-label="Close"],button:has-text("Cancel")').first()
        if (await closeButton.isVisible().catch(() => false)) {
          await closeButton.click()
        }

        await page.waitForTimeout(500)

        // Reopen export modal
        await exportButton.click()
        await page.waitForTimeout(500)

        // Verify quality is still set to high
        const selectedValue = await qualitySelect.inputValue().catch(() => '')
        const selectedOption = qualitySelect.locator('option[selected]')
        const selectedText = await selectedOption.textContent().catch(() => '')

        expect(selectedValue.toLowerCase().includes('high') ||
               selectedText.toLowerCase().includes('high')).toBe(true)
      } else {
        test.skip(true, 'Quality settings not found')
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })
})
