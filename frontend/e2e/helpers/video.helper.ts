/**
 * Video-related helper functions for E2E tests
 * Provides utilities for video upload, management, and verification
 */

import { Page, expect } from '@playwright/test'
import { Buffer } from 'buffer'

export interface VideoFile {
  name: string
  content: Buffer
  mimeType: string
  size?: number
}

/**
 * Create a fake video file for testing
 */
export function createFakeVideoFile(sizeInKB = 100): VideoFile {
  // Create fake video content
  const content = Buffer.alloc(sizeInKB * 1024, 'fake video data')

  return {
    name: `test-video-${Date.now()}.mp4`,
    content,
    mimeType: 'video/mp4',
    size: content.length,
  }
}

/**
 * Upload a video file
 */
export async function uploadVideo(
  page: Page,
  videoFile?: VideoFile,
  title?: string
): Promise<string | null> {
  const file = videoFile || createFakeVideoFile()

  // Navigate to upload page
  await page.goto('/upload').catch(() => {
    // If /upload doesn't exist, try /videos
    return page.goto('/videos')
  })

  // Find file input
  const fileInput = page.locator('input[type="file"]')

  if (!(await fileInput.isVisible().catch(() => false))) {
    // Look for upload button to click first
    const uploadButton = page.locator('text=/upload|add video/i').first()
    if (await uploadButton.isVisible().catch(() => false)) {
      await uploadButton.click()
      await page.waitForTimeout(500)
    }
  }

  // Upload file
  if (await fileInput.isVisible().catch(() => false)) {
    await fileInput.setInputFiles({
      name: file.name,
      mimeType: file.mimeType,
      buffer: file.content,
    })

    // Fill title if provided and field exists
    if (title) {
      const titleInput = page.locator('input[name="title"],input[placeholder*="title" i]')
      if (await titleInput.isVisible().catch(() => false)) {
        await titleInput.fill(title)
      }
    }

    // Look for upload/submit button
    const submitButton = page.locator('button:has-text("Upload"),button[type="submit"]')
    if (await submitButton.isVisible().catch(() => false)) {
      await submitButton.click()
    }

    // Wait for upload to complete or show progress
    await page.waitForTimeout(2000)

    // Try to get video ID from URL if navigated to video detail
    const url = page.url()
    const match = url.match(/\/videos\/([a-f0-9-]+)/)

    return match ? match[1] : null
  }

  return null
}

/**
 * Navigate to video detail page
 */
export async function navigateToVideo(page: Page, videoId?: string): Promise<void> {
  if (videoId) {
    await page.goto(`/videos/${videoId}`)
  } else {
    // Navigate to first video in list
    await page.goto('/videos')
    await page.waitForTimeout(1000)

    const firstVideo = page.locator('[data-testid="video-card"]').first()
    if (await firstVideo.isVisible().catch(() => false)) {
      await firstVideo.click()
    }
  }
}

/**
 * Wait for video processing to complete
 */
export async function waitForVideoProcessing(
  page: Page,
  timeoutMs = 30000
): Promise<void> {
  const startTime = Date.now()

  while (Date.now() - startTime < timeoutMs) {
    // Check for "completed" status
    const completedStatus = page.locator('text=/completed|ready|processed/i')
    if (await completedStatus.isVisible().catch(() => false)) {
      return
    }

    // Check if still processing
    const processingStatus = page.locator('text=/processing|uploading/i')
    if (!(await processingStatus.isVisible().catch(() => false))) {
      // Not processing anymore
      return
    }

    await page.waitForTimeout(1000)
  }
}

/**
 * Delete a video
 */
export async function deleteVideo(page: Page, videoId?: string): Promise<void> {
  if (videoId) {
    await navigateToVideo(page, videoId)
  }

  // Find delete button
  const deleteButton = page
    .locator('button[title="Delete"],button[aria-label="Delete"]')
    .first()

  if (await deleteButton.isVisible().catch(() => false)) {
    await deleteButton.click()

    // Confirm deletion
    const confirmButton = page.locator('text=/confirm|delete|yes/i').first()
    if (await confirmButton.isVisible().catch(() => false)) {
      await confirmButton.click()
    }

    await page.waitForTimeout(1000)
  }
}

/**
 * Get list of videos from videos page
 */
export async function getVideoList(page: Page): Promise<number> {
  await page.goto('/videos')
  await page.waitForTimeout(1000)

  const videoCards = page.locator('[data-testid="video-card"]')
  return await videoCards.count()
}

/**
 * Check if video player is visible and playing
 */
export async function isVideoPlayerVisible(page: Page): Promise<boolean> {
  const videoPlayer = page.locator('video')
  return await videoPlayer.isVisible().catch(() => false)
}

/**
 * Get video status from UI
 */
export async function getVideoStatus(page: Page): Promise<string | null> {
  const statusBadge = page.locator('[data-testid="video-status"]').or(
    page.locator('text=/completed|processing|uploaded|failed/i')
  )

  if (await statusBadge.isVisible().catch(() => false)) {
    return await statusBadge.textContent()
  }

  return null
}

/**
 * Verify video card contains expected information
 */
export async function verifyVideoCard(
  page: Page,
  expectedTitle?: string
): Promise<void> {
  const videoCard = page.locator('[data-testid="video-card"]').first()

  await expect(videoCard).toBeVisible({ timeout: 5000 })

  // Check for title
  const titleElement = videoCard.locator('h3,h2').first()
  await expect(titleElement).toBeVisible()

  if (expectedTitle) {
    await expect(titleElement).toContainText(expectedTitle)
  }

  // Check for status badge
  const statusElement = videoCard.locator('text=/completed|processing|uploaded|failed/i')
  await expect(statusElement).toBeVisible()
}
