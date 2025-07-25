import { test, expect } from '@playwright/test';

test.describe('Real-time Updates', () => {
  let sessionId: string;

  test.beforeAll(async ({ request }) => {
    // Set up a run for today
    const today = new Date().toISOString().split('T')[0];
    
    await request.post('http://localhost:8000/api/calendar/configure', {
      data: {
        date: today,
        has_run: true
      }
    });
    
    const response = await request.get('http://localhost:8000/api/calendar/today');
    const data = await response.json();
    sessionId = data.session_id;
  });

  test('should update attendance counter in real-time', async ({ browser }) => {
    // Create two browser contexts - one for admin, one for runner
    const adminContext = await browser.newContext();
    const runnerContext = await browser.newContext();
    
    const adminPage = await adminContext.newPage();
    const runnerPage = await runnerContext.newPage();
    
    // Open admin dashboard
    await adminPage.goto('/admin');
    
    // Get initial attendance count
    const initialCountText = await adminPage.locator('[data-testid="current-attendance-count"]').textContent();
    const initialCount = parseInt(initialCountText || '0');
    
    // Register a runner in the other context
    await runnerPage.goto(`/register/${sessionId}`);
    await runnerPage.locator('[data-testid="runner-name-input"]').fill(`Real-time Test ${Date.now()}`);
    await runnerPage.locator('[data-testid="register-btn"]').click();
    
    // Wait for success message on runner page
    await expect(runnerPage.locator('[data-testid="success-message"]')).toBeVisible();
    
    // Verify attendance counter updated on admin page
    await expect(adminPage.locator('[data-testid="current-attendance-count"]')).toContainText((initialCount + 1).toString());
    
    await adminContext.close();
    await runnerContext.close();
  });

  test('should handle WebSocket connection failures gracefully', async ({ page }) => {
    await page.goto('/admin');
    
    // Block WebSocket connections
    await page.route('**/socket.io/**', route => route.abort());
    
    // Verify that the page still functions without real-time updates
    await expect(page.locator('[data-testid="attendance-counter"]')).toBeVisible();
    
    // Check for connection status indicator
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('disconnected');
  });

  test('should reconnect WebSocket after network interruption', async ({ page }) => {
    await page.goto('/admin');
    
    // Wait for initial connection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('connected');
    
    // Simulate network interruption
    await page.route('**/socket.io/**', route => route.abort());
    
    // Wait for disconnection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('disconnected');
    
    // Restore network
    await page.unroute('**/socket.io/**');
    
    // Wait for reconnection
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('connected');
  });

  test('should broadcast updates to multiple admin sessions', async ({ browser }) => {
    // Create three browser contexts
    const admin1Context = await browser.newContext();
    const admin2Context = await browser.newContext();
    const runnerContext = await browser.newContext();
    
    const admin1Page = await admin1Context.newPage();
    const admin2Page = await admin2Context.newPage();
    const runnerPage = await runnerContext.newPage();
    
    // Open admin dashboards
    await admin1Page.goto('/admin');
    await admin2Page.goto('/admin');
    
    // Get initial counts from both admin pages
    const initialCount1Text = await admin1Page.locator('[data-testid="current-attendance-count"]').textContent();
    const initialCount2Text = await admin2Page.locator('[data-testid="current-attendance-count"]').textContent();
    const initialCount = parseInt(initialCount1Text || '0');
    
    // Verify both admin pages show the same count
    expect(initialCount1Text).toBe(initialCount2Text);
    
    // Register a runner
    await runnerPage.goto(`/register/${sessionId}`);
    await runnerPage.locator('[data-testid="runner-name-input"]').fill(`Broadcast Test ${Date.now()}`);
    await runnerPage.locator('[data-testid="register-btn"]').click();
    
    // Verify both admin pages update
    const expectedCount = (initialCount + 1).toString();
    await expect(admin1Page.locator('[data-testid="current-attendance-count"]')).toContainText(expectedCount);
    await expect(admin2Page.locator('[data-testid="current-attendance-count"]')).toContainText(expectedCount);
    
    await admin1Context.close();
    await admin2Context.close();
    await runnerContext.close();
  });
});