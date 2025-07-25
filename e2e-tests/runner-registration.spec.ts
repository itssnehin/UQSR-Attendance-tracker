import { test, expect } from '@playwright/test';

test.describe('Runner Registration', () => {
  let sessionId: string;

  test.beforeAll(async ({ request }) => {
    // Set up a run for today to get a valid session ID
    const today = new Date().toISOString().split('T')[0];
    
    // Configure today as a run day
    await request.post('http://localhost:8000/api/calendar/configure', {
      data: {
        date: today,
        has_run: true
      }
    });
    
    // Get the session ID for today
    const response = await request.get('http://localhost:8000/api/calendar/today');
    const data = await response.json();
    sessionId = data.session_id;
  });

  test('should display registration form when accessing valid QR code', async ({ page }) => {
    await page.goto(`/register/${sessionId}`);
    
    // Check registration form is visible
    await expect(page.locator('[data-testid="registration-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="runner-name-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="register-btn"]')).toBeVisible();
  });

  test('should successfully register a runner', async ({ page }) => {
    await page.goto(`/register/${sessionId}`);
    
    // Fill in runner name
    const runnerName = `Test Runner ${Date.now()}`;
    await page.locator('[data-testid="runner-name-input"]').fill(runnerName);
    
    // Submit registration
    await page.locator('[data-testid="register-btn"]').click();
    
    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toContainText('successfully registered');
  });

  test('should prevent duplicate registration', async ({ page }) => {
    const runnerName = `Duplicate Runner ${Date.now()}`;
    
    // First registration
    await page.goto(`/register/${sessionId}`);
    await page.locator('[data-testid="runner-name-input"]').fill(runnerName);
    await page.locator('[data-testid="register-btn"]').click();
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Attempt duplicate registration
    await page.goto(`/register/${sessionId}`);
    await page.locator('[data-testid="runner-name-input"]').fill(runnerName);
    await page.locator('[data-testid="register-btn"]').click();
    
    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('already registered');
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto(`/register/${sessionId}`);
    
    // Try to submit without name
    await page.locator('[data-testid="register-btn"]').click();
    
    // Verify validation error
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('Name is required');
  });

  test('should handle invalid session ID', async ({ page }) => {
    await page.goto('/register/invalid-session-id');
    
    // Verify error message for invalid session
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid or expired');
  });

  test('should work correctly on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto(`/register/${sessionId}`);
    
    // Check mobile-optimized layout
    await expect(page.locator('[data-testid="registration-form"]')).toBeVisible();
    
    // Verify form elements are properly sized for mobile
    const nameInput = page.locator('[data-testid="runner-name-input"]');
    await expect(nameInput).toBeVisible();
    
    // Test touch interaction
    await nameInput.tap();
    await nameInput.fill('Mobile Test Runner');
    
    await page.locator('[data-testid="register-btn"]').tap();
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    await page.goto(`/register/${sessionId}`);
    
    // Simulate network failure
    await page.route('**/api/register', route => route.abort());
    
    await page.locator('[data-testid="runner-name-input"]').fill('Network Test Runner');
    await page.locator('[data-testid="register-btn"]').click();
    
    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('network error');
  });
});