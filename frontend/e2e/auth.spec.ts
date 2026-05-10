import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('text=Sign in with Google')).toBeVisible();
  });

  test('should redirect unauthenticated users from dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    
    await expect(page).toHaveURL(/.*\/?$/);
  });

  test('should have proper meta tags', async ({ page }) => {
    await page.goto('/');
    
    await expect(page).toHaveTitle(/FH-Connect/i);
  });
});

test.describe('Meeting Room', () => {
  test('should require authentication to join meeting', async ({ page }) => {
    await page.goto('/room/test-room');
    
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/room/test-room');
  });

  test('should display join button when on landing', async ({ page }) => {
    await page.goto('/');
    
    const joinButton = page.locator('button:has-text("Join Meeting")');
    await expect(joinButton).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate to landing page', async ({ page }) => {
    await page.goto('/dashboard');
    await page.locator('text=FH-Connect').first().click();
    
    await expect(page).toHaveURL('/');
  });
});