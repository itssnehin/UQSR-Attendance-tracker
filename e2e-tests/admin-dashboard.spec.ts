import { test, expect } from '@playwright/test';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/admin');
  });

  test('should display calendar configuration interface', async ({ page }) => {
    // Check that calendar is visible
    await expect(page.locator('[data-testid="calendar-container"]')).toBeVisible();
    
    // Check that current month is displayed
    const currentMonth = new Date().toLocaleString('default', { month: 'long', year: 'numeric' });
    await expect(page.locator('[data-testid="calendar-header"]')).toContainText(currentMonth);
  });

  test('should allow marking days as run days', async ({ page }) => {
    // Find a date that's not already marked
    const dateCell = page.locator('[data-testid="calendar-day"]:not(.run-day)').first();
    await dateCell.click();
    
    // Verify the day is now marked as a run day
    await expect(dateCell).toHaveClass(/run-day/);
    
    // Save configuration
    await page.locator('[data-testid="save-calendar-btn"]').click();
    
    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should display real-time attendance counter', async ({ page }) => {
    // Check attendance counter is visible
    await expect(page.locator('[data-testid="attendance-counter"]')).toBeVisible();
    
    // Check initial count is displayed
    const counter = page.locator('[data-testid="current-attendance-count"]');
    await expect(counter).toBeVisible();
    
    // Verify counter shows a number
    const countText = await counter.textContent();
    expect(countText).toMatch(/^\d+$/);
  });

  test('should show QR code for current day if run is scheduled', async ({ page }) => {
    // First mark today as a run day
    const today = new Date();
    const todaySelector = `[data-date="${today.toISOString().split('T')[0]}"]`;
    
    await page.locator(todaySelector).click();
    await page.locator('[data-testid="save-calendar-btn"]').click();
    
    // Navigate to QR display
    await page.locator('[data-testid="qr-display-tab"]').click();
    
    // Verify QR code is displayed
    await expect(page.locator('[data-testid="qr-code-image"]')).toBeVisible();
    await expect(page.locator('[data-testid="session-info"]')).toBeVisible();
  });

  test('should export attendance data', async ({ page }) => {
    // Navigate to export section
    await page.locator('[data-testid="export-tab"]').click();
    
    // Set date range
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 7);
    const endDate = new Date();
    
    await page.locator('[data-testid="start-date-input"]').fill(startDate.toISOString().split('T')[0]);
    await page.locator('[data-testid="end-date-input"]').fill(endDate.toISOString().split('T')[0]);
    
    // Start download
    const downloadPromise = page.waitForDownload();
    await page.locator('[data-testid="export-btn"]').click();
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/attendance-export-.*\.csv/);
  });

  test('should handle mobile viewport correctly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that mobile navigation is visible
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
    
    // Check that calendar adapts to mobile
    await expect(page.locator('[data-testid="calendar-container"]')).toBeVisible();
    
    // Verify touch interactions work
    const dateCell = page.locator('[data-testid="calendar-day"]').first();
    await dateCell.tap();
  });
});