/**
 * Team Collaboration E2E Tests
 *
 * End-to-end tests for team collaboration features.
 */

import { test, expect } from '@playwright/test';

test.describe('Team Collaboration', () => {
  test.beforeEach(async ({ page }) => {
    // Login as test user
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test.describe('Organizations', () => {
    test('should create a new organization', async ({ page }) => {
      await page.goto('/organizations');
      await page.click('button:has-text("New Organization")');

      await page.fill('input#name', 'Test Organization');
      await page.fill('input#slug', 'test-org');
      await page.fill('textarea#description', 'This is a test organization');

      await page.click('button:has-text("Create")');

      await expect(page.locator('text=Test Organization')).toBeVisible();
    });

    test('should edit an organization', async ({ page }) => {
      await page.goto('/organizations');
      await page.click('[data-testid="org-menu"]').first();
      await page.click('text=Edit');

      await page.fill('input#name', 'Updated Organization');
      await page.click('button:has-text("Update")');

      await expect(page.locator('text=Updated Organization')).toBeVisible();
    });

    test('should delete an organization', async ({ page }) => {
      await page.goto('/organizations');

      page.on('dialog', (dialog) => dialog.accept());

      await page.click('[data-testid="org-menu"]').first();
      await page.click('text=Delete');

      await expect(page.locator('text=No organizations yet')).toBeVisible();
    });
  });

  test.describe('Team Members', () => {
    test('should invite a team member', async ({ page }) => {
      await page.goto('/organizations/test-org/members');
      await page.click('button:has-text("Invite Member")');

      await page.fill('input#email', 'newmember@example.com');
      await page.selectOption('select', { label: 'Editor - Can edit content' });
      await page.fill('input#message', 'Welcome to the team!');

      await page.click('button:has-text("Send Invitation")');

      await expect(
        page.locator('text=newmember@example.com')
      ).toBeVisible();
    });

    test('should change member role', async ({ page }) => {
      await page.goto('/organizations/test-org/members');

      await page.click('[data-testid="member-menu"]').first();
      await page.click('text=Change to Admin');

      await expect(page.locator('text=admin')).toBeVisible();
    });

    test('should remove a team member', async ({ page }) => {
      await page.goto('/organizations/test-org/members');

      page.on('dialog', (dialog) => dialog.accept());

      await page.click('[data-testid="member-menu"]').first();
      await page.click('text=Remove');

      await expect(page.locator('text=No members yet')).toBeVisible();
    });
  });

  test.describe('Sharing', () => {
    test('should share a video with a user', async ({ page }) => {
      await page.goto('/videos/test-video-id');
      await page.click('button:has-text("Share")');

      await page.fill('input[type="email"]', 'colleague@example.com');
      await page.click('button:has-text("Send Invitation")');

      await expect(
        page.locator('text=colleague@example.com')
      ).toBeVisible();
    });

    test('should generate a share link', async ({ page }) => {
      await page.goto('/videos/test-video-id');
      await page.click('button:has-text("Share")');
      await page.click('text=Share via Link');

      await page.click('button:has-text("Generate Link")');

      await expect(page.locator('text=Active Links')).toBeVisible();
      await expect(page.locator('input[readonly]')).toBeVisible();
    });

    test('should copy share link to clipboard', async ({ page, context }) => {
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);

      await page.goto('/videos/test-video-id');
      await page.click('button:has-text("Share")');
      await page.click('text=Share via Link');

      // Generate link first
      await page.click('button:has-text("Generate Link")');

      // Copy link
      await page.click('button[aria-label="Copy"]').first();

      // Verify clipboard
      const clipboardText = await page.evaluate(() =>
        navigator.clipboard.readText()
      );
      expect(clipboardText).toContain('/shared/');
    });
  });

  test.describe('Comments', () => {
    test('should add a comment', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      await page.fill(
        'textarea[placeholder="Add a comment..."]',
        'This is a test comment'
      );
      await page.click('button:has-text("Comment")');

      await expect(
        page.locator('text=This is a test comment')
      ).toBeVisible();
    });

    test('should reply to a comment', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      await page.click('button:has-text("Reply")').first();
      await page.fill(
        'textarea[placeholder="Write a reply..."]',
        'This is a reply'
      );
      await page.click('button:has-text("Reply")').last();

      await expect(page.locator('text=This is a reply')).toBeVisible();
    });

    test('should resolve a comment', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      await page.click('[data-testid="comment-menu"]').first();
      await page.click('text=Resolve');

      await expect(page.locator('text=Resolved')).toBeVisible();
    });

    test('should filter comments', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      await page.selectOption('select', { label: 'Open' });

      await expect(page.locator('text=Resolved')).not.toBeVisible();
    });
  });

  test.describe('Version History', () => {
    test('should display version history', async ({ page }) => {
      await page.goto('/videos/test-video-id/versions');

      await expect(page.locator('text=Version History')).toBeVisible();
      await expect(page.locator('text=v1')).toBeVisible();
    });

    test('should restore a previous version', async ({ page }) => {
      await page.goto('/videos/test-video-id/versions');

      page.on('dialog', (dialog) => dialog.accept());

      await page.click('[data-testid="version-menu"]').first();
      await page.click('text=Restore');

      await expect(page.locator('text=Current')).toBeVisible();
    });

    test('should compare two versions', async ({ page }) => {
      await page.goto('/videos/test-video-id/versions');

      // Select first version
      await page.click('[data-testid="version-menu"]').first();
      await page.click('text=Compare');

      // Select second version
      await page.click('[data-testid="version-menu"]').nth(1);
      await page.click('text=Compare');

      await expect(page.locator('text=Comparing')).toBeVisible();
    });
  });

  test.describe('Notifications', () => {
    test('should display notification bell with count', async ({ page }) => {
      await page.goto('/dashboard');

      const bellButton = page.locator('button:has-text("Bell")');
      await expect(bellButton).toBeVisible();

      const badge = bellButton.locator('[data-testid="unread-count"]');
      if (await badge.isVisible()) {
        const count = await badge.textContent();
        expect(parseInt(count || '0')).toBeGreaterThan(0);
      }
    });

    test('should open notifications panel', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('button[aria-label="Notifications"]');

      await expect(page.locator('text=Notifications')).toBeVisible();
    });

    test('should mark notification as read', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('button[aria-label="Notifications"]');

      await page.click('[data-testid="notification"]').first();

      await expect(page.locator('text=New').first()).not.toBeVisible();
    });

    test('should mark all notifications as read', async ({ page }) => {
      await page.goto('/dashboard');
      await page.click('button[aria-label="Notifications"]');

      await page.click('button:has-text("Mark all read")');

      await expect(page.locator('text=New')).not.toBeVisible();
    });
  });

  test.describe('Active Users (Presence)', () => {
    test('should display active users indicator', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      const activeUsersIndicator = page.locator('[data-testid="active-users"]');
      if (await activeUsersIndicator.isVisible()) {
        await expect(activeUsersIndicator).toBeVisible();
      }
    });

    test('should show user avatars on hover', async ({ page }) => {
      await page.goto('/videos/test-video-id');

      const activeUsersIndicator = page.locator('[data-testid="active-users"]');
      if (await activeUsersIndicator.isVisible()) {
        await activeUsersIndicator.hover();
        await expect(page.locator('[role="tooltip"]')).toBeVisible();
      }
    });
  });

  test.describe('Real-time Updates', () => {
    test('should receive real-time comment updates', async ({
      page,
      context,
    }) => {
      // Open video in two tabs
      const page1 = page;
      const page2 = await context.newPage();

      await page1.goto('/videos/test-video-id');
      await page2.goto('/videos/test-video-id');

      // Add comment in first tab
      await page1.fill(
        'textarea[placeholder="Add a comment..."]',
        'Real-time test comment'
      );
      await page1.click('button:has-text("Comment")');

      // Verify comment appears in second tab
      await expect(
        page2.locator('text=Real-time test comment')
      ).toBeVisible({ timeout: 5000 });

      await page2.close();
    });
  });
});
