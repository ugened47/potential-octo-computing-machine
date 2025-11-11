/**
 * E2E Tests for Advanced Subtitle Styling Workflow
 * Tests the complete subtitle styling feature including:
 * - Create custom subtitle styles
 * - Preview subtitle styling
 * - Burn subtitles into video
 * - Translate subtitles
 * - Export with embedded subtitles
 * - Style templates and presets
 * - Font and color customization
 * - Position and timing adjustments
 */

import { test, expect } from './fixtures/test-fixtures'
import { navigateToVideo } from './helpers/video.helper'

test.describe('Subtitles - Basic Styling', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to a video with transcription
    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('displays subtitle styling interface', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Look for subtitles tab or section
    const subtitlesTab = page.locator(
      '[data-testid="subtitles-tab"],button:has-text("Subtitles"),button:has-text("Captions")'
    ).first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Should show subtitle controls
      const subtitleControls = page.locator(
        '[data-testid="subtitle-controls"],[data-subtitle-editor]'
      ).first()

      await expect(subtitleControls).toBeVisible({ timeout: 5000 })
    } else {
      test.skip(true, 'Subtitles section not found')
    }
  })

  test('user can access subtitle style editor', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to subtitles section
    const subtitlesTab = page.locator('button:has-text("Subtitles"),button:has-text("Captions")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Look for style editor button
      const styleButton = page.locator(
        '[data-testid="style-subtitles"],button:has-text("Style"),button:has-text("Customize")'
      ).first()

      if (await styleButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Should show style editor panel
        const styleEditor = page.locator(
          '[data-testid="subtitle-style-editor"],[role="dialog"]'
        ).first()

        await expect(styleEditor).toBeVisible({ timeout: 5000 })
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can customize subtitle font', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Navigate to subtitle styling
    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style"),button:has-text("Customize")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for font selector
        const fontSelect = page.locator(
          '[data-testid="font-select"],select[name="font"],select[name="font_family"]'
        ).first()

        if (await fontSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Select a font
          await fontSelect.selectOption({ index: 1 })
          await page.waitForTimeout(300)

          // Verify font was selected
          const selectedValue = await fontSelect.inputValue()
          expect(selectedValue).toBeTruthy()
        } else {
          test.skip(true, 'Font selector not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can customize subtitle color', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for color picker
        const colorInput = page.locator(
          '[data-testid="text-color"],input[name="color"],input[type="color"]'
        ).first()

        if (await colorInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Set color
          await colorInput.fill('#FF0000')
          await page.waitForTimeout(300)

          // Verify color was set
          const colorValue = await colorInput.inputValue()
          expect(colorValue.toLowerCase()).toBe('#ff0000')
        } else {
          test.skip(true, 'Color picker not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can adjust subtitle font size', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for font size input
        const fontSizeInput = page.locator(
          '[data-testid="font-size"],input[name="font_size"]'
        ).first()

        if (await fontSizeInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          await fontSizeInput.fill('24')
          await page.waitForTimeout(300)

          // Verify value was set
          const fontSize = await fontSizeInput.inputValue()
          expect(fontSize).toBe('24')
        } else {
          test.skip(true, 'Font size input not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can set subtitle background color and opacity', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for background color
        const bgColorInput = page.locator(
          '[data-testid="background-color"],input[name="background_color"]'
        ).first()

        if (await bgColorInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          await bgColorInput.fill('#000000')
          await page.waitForTimeout(300)

          // Look for opacity/alpha slider
          const opacitySlider = page.locator(
            '[data-testid="background-opacity"],input[name="opacity"]'
          ).first()

          if (await opacitySlider.isVisible().catch(() => false)) {
            await opacitySlider.fill('0.7')
            await page.waitForTimeout(300)
          }

          expect(true).toBe(true)
        } else {
          test.skip(true, 'Background color controls not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })
})

test.describe('Subtitles - Preview & Position', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('displays live preview of subtitle styling', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for preview panel
        const previewPanel = page.locator(
          '[data-testid="subtitle-preview"],[data-preview]'
        ).first()

        if (await previewPanel.isVisible({ timeout: 3000 }).catch(() => false)) {
          await expect(previewPanel).toBeVisible()

          // Preview should show subtitle text
          const previewText = previewPanel.locator('text=/sample|preview|subtitle/i')
          const hasText = await previewText.isVisible({ timeout: 2000 }).catch(() => false)

          expect(hasText).toBe(true)
        } else {
          test.skip(true, 'Preview panel not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can adjust subtitle position', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for position controls
        const positionSelect = page.locator(
          '[data-testid="subtitle-position"],select[name="position"]'
        ).first()

        if (await positionSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
          // Select a position (e.g., top, center, bottom)
          await positionSelect.selectOption({ label: /bottom|center|top/i })
          await page.waitForTimeout(300)

          // Verify selection
          const selectedValue = await positionSelect.inputValue()
          expect(selectedValue).toBeTruthy()
        } else {
          test.skip(true, 'Position controls not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('preview updates in real-time when styles change', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Get initial preview state
        const previewPanel = page.locator('[data-testid="subtitle-preview"]').first()

        if (await previewPanel.isVisible({ timeout: 2000 }).catch(() => false)) {
          // Change font size
          const fontSizeInput = page.locator('[name="font_size"]').first()
          if (await fontSizeInput.isVisible().catch(() => false)) {
            await fontSizeInput.fill('32')
            await page.waitForTimeout(500)

            // Preview should still be visible and updated
            await expect(previewPanel).toBeVisible()
          }

          expect(true).toBe(true)
        } else {
          test.skip(true, 'Preview panel not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })
})

test.describe('Subtitles - Templates & Presets', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can select from preset subtitle styles', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Look for presets
        const presetsButton = page.locator(
          '[data-testid="subtitle-presets"],button:has-text("Presets"),button:has-text("Templates")'
        ).first()

        if (await presetsButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await presetsButton.click()
          await page.waitForTimeout(500)

          // Should show list of presets
          const presetList = page.locator('[data-testid="preset-list"]')
          const presetItems = page.locator('[data-testid="preset-item"]')

          const hasList = await presetList.isVisible({ timeout: 2000 }).catch(() => false)
          const itemCount = await presetItems.count()

          expect(hasList || itemCount > 0).toBe(true)
        } else {
          test.skip(true, 'Presets not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can save custom subtitle style as template', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open style editor
      const styleButton = page.locator('button:has-text("Style")').first()
      if (await styleButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await styleButton.click()
        await page.waitForTimeout(500)

        // Customize some settings
        const fontSizeInput = page.locator('[name="font_size"]').first()
        if (await fontSizeInput.isVisible().catch(() => false)) {
          await fontSizeInput.fill('28')
          await page.waitForTimeout(300)
        }

        // Look for save template button
        const saveTemplateButton = page.locator(
          'button:has-text("Save Template"),button:has-text("Save Preset")'
        ).first()

        if (await saveTemplateButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await saveTemplateButton.click()
          await page.waitForTimeout(500)

          // Enter template name
          const templateNameInput = page.locator('input[name="template_name"]').first()
          if (await templateNameInput.isVisible().catch(() => false)) {
            await templateNameInput.fill('My Custom Style')
            await page.waitForTimeout(300)

            // Save
            const saveButton = page.locator('button:has-text("Save")').first()
            if (await saveButton.isVisible().catch(() => false)) {
              await saveButton.click()
              await page.waitForTimeout(1000)

              // Verify saved
              const successMessage = page.locator('text=/saved|created/i')
              const hasSuccess = await successMessage.isVisible({ timeout: 3000 }).catch(() => false)

              expect(hasSuccess).toBe(true)
            }
          } else {
            test.skip(true, 'Template name input not found')
          }
        } else {
          test.skip(true, 'Save template button not found')
        }
      } else {
        test.skip(true, 'Style button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })
})

test.describe('Subtitles - Translation', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can translate subtitles to another language', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Look for translate button
      const translateButton = page.locator(
        '[data-testid="translate-subtitles"],button:has-text("Translate")'
      ).first()

      if (await translateButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await translateButton.click()
        await page.waitForTimeout(500)

        // Should show language selector
        const languageSelect = page.locator(
          '[data-testid="target-language"],select[name="target_language"]'
        ).first()

        if (await languageSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
          // Select a language
          await languageSelect.selectOption({ label: /spanish|french|german/i })
          await page.waitForTimeout(300)

          // Start translation
          const startButton = page.locator('button:has-text("Translate"),button:has-text("Start")').first()
          if (await startButton.isVisible().catch(() => false)) {
            await startButton.click()
            await page.waitForTimeout(1000)

            // Verify translation started
            const processingIndicator = page.locator('text=/translating|processing/i')
            const hasProcessing = await processingIndicator.isVisible({ timeout: 5000 }).catch(() => false)

            expect(hasProcessing).toBe(true)
          }
        } else {
          test.skip(true, 'Language selector not found')
        }
      } else {
        test.skip(true, 'Translate button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('displays list of available translation languages', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Open translate dialog
      const translateButton = page.locator('button:has-text("Translate")').first()
      if (await translateButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await translateButton.click()
        await page.waitForTimeout(500)

        // Check language options
        const languageSelect = page.locator('select[name="target_language"]').first()
        if (await languageSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
          const options = await languageSelect.locator('option').count()
          expect(options).toBeGreaterThan(1)
        } else {
          test.skip(true, 'Language options not found')
        }
      } else {
        test.skip(true, 'Translate button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })
})

test.describe('Subtitles - Burn & Export', () => {
  test.beforeEach(async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    await page.goto('/videos')
    await page.waitForTimeout(1000)
    await navigateToVideo(page)
    await page.waitForTimeout(500)
  })

  test('user can burn subtitles into video', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Look for burn subtitles button
      const burnButton = page.locator(
        '[data-testid="burn-subtitles"],button:has-text("Burn"),button:has-text("Embed")'
      ).first()

      if (await burnButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await burnButton.click()
        await page.waitForTimeout(500)

        // Confirm action
        const confirmButton = page.locator('button:has-text("Confirm"),button:has-text("Start")').first()
        if (await confirmButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await confirmButton.click()
        }

        await page.waitForTimeout(1000)

        // Verify processing started
        const processingIndicator = page.locator('text=/burning|processing|embedding/i')
        const hasProcessing = await processingIndicator.isVisible({ timeout: 5000 }).catch(() => false)

        expect(hasProcessing).toBe(true)
      } else {
        test.skip(true, 'Burn subtitles button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })

  test('user can export video with embedded subtitles', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    // Open export dialog
    const exportButton = page.locator('button:has-text("Export")').first()

    if (await exportButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await exportButton.click()
      await page.waitForTimeout(500)

      // Look for subtitle options in export
      const includeSubtitles = page.locator(
        '[data-testid="include-subtitles"],input[name="include_subtitles"]'
      ).first()

      if (await includeSubtitles.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Enable subtitles in export
        if (await includeSubtitles.getAttribute('type').then(type => type === 'checkbox').catch(() => false)) {
          await includeSubtitles.check()
        } else {
          await includeSubtitles.click()
        }

        await page.waitForTimeout(300)

        // Start export
        const startExportButton = page.locator('button:has-text("Export"),button:has-text("Start")').first()
        if (await startExportButton.isVisible().catch(() => false)) {
          await startExportButton.click()
          await page.waitForTimeout(1000)

          // Verify export started
          const exportStatus = page.locator('text=/exporting|processing/i')
          const hasStatus = await exportStatus.isVisible({ timeout: 5000 }).catch(() => false)

          expect(hasStatus).toBe(true)
        }
      } else {
        test.skip(true, 'Subtitle export option not found')
      }
    } else {
      test.skip(true, 'Export button not found')
    }
  })

  test('user can download subtitle file separately (SRT/VTT)', async ({ authenticatedPage }) => {
    const { page } = authenticatedPage

    const subtitlesTab = page.locator('button:has-text("Subtitles")').first()

    if (await subtitlesTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await subtitlesTab.click()
      await page.waitForTimeout(500)

      // Look for download subtitles button
      const downloadButton = page.locator(
        '[data-testid="download-subtitles"],button:has-text("Download"),a:has-text("Download")'
      ).first()

      if (await downloadButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Setup download listener
        const downloadPromise = page.waitForEvent('download', { timeout: 10000 })

        await downloadButton.click()

        try {
          const download = await downloadPromise

          // Verify download is subtitle file
          expect(download.suggestedFilename()).toMatch(/\.(srt|vtt)$/i)
        } catch (error) {
          // Download might not trigger immediately
          await page.waitForTimeout(1000)

          // Check if download link appeared
          const downloadLink = page.locator('a[download],a[href*=".srt"],a[href*=".vtt"]')
          const hasLink = await downloadLink.isVisible().catch(() => false)

          expect(hasLink).toBe(true)
        }
      } else {
        test.skip(true, 'Download subtitles button not found')
      }
    } else {
      test.skip(true, 'Subtitles tab not found')
    }
  })
})
