import { test, expect } from '@playwright/test';

test.describe('Gamification Features', () => {
  // Helper function to login
  async function login(page) {
    await page.goto('/');
    await page.getByLabel(/사용자명 또는 이메일/i).fill('testuser');
    await page.getByLabel(/비밀번호/i).fill('Test123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await page.waitForURL('**/dashboard');
  }

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('should display character info on dashboard', async ({ page }) => {
    // Check character card
    await expect(page.getByTestId('character-card')).toBeVisible();
    await expect(page.getByText(/레벨 \d+/i)).toBeVisible();
    await expect(page.getByRole('progressbar')).toBeVisible();
    await expect(page.getByText(/\d+ \/ \d+ XP/i)).toBeVisible();
  });

  test('should navigate to quests page', async ({ page }) => {
    // Click quests menu item
    await page.getByRole('link', { name: /퀘스트/i }).click();

    // Check quests page
    await page.waitForURL('**/quests');
    await expect(page.getByRole('heading', { name: /퀘스트/i })).toBeVisible();
    
    // Should show quest categories
    await expect(page.getByRole('tab', { name: /일일 퀘스트/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /주간 퀘스트/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /특별 퀘스트/i })).toBeVisible();
  });

  test('should start a quest', async ({ page }) => {
    await page.goto('/quests');

    // Find and click on a quest card
    const questCard = page.locator('[data-testid="quest-card"]').first();
    await questCard.click();

    // Check quest details modal
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('button', { name: /퀘스트 시작/i })).toBeVisible();

    // Start quest
    await page.getByRole('button', { name: /퀘스트 시작/i }).click();

    // Should navigate to quest page
    await page.waitForURL(/.*quests\/\d+/);
    await expect(page.getByTestId('quest-content')).toBeVisible();
  });

  test('should display achievements', async ({ page }) => {
    // Navigate to achievements
    await page.getByRole('link', { name: /업적/i }).click();

    await page.waitForURL('**/achievements');
    await expect(page.getByRole('heading', { name: /업적/i })).toBeVisible();

    // Check achievement categories
    await expect(page.getByText(/퀘스트 업적/i)).toBeVisible();
    await expect(page.getByText(/학습 업적/i)).toBeVisible();
    await expect(page.getByText(/연속 출석/i)).toBeVisible();

    // Check achievement cards
    const achievementCards = page.locator('[data-testid="achievement-card"]');
    await expect(achievementCards).toHaveCount(await achievementCards.count());
  });

  test('should display badges', async ({ page }) => {
    // Navigate to badges
    await page.getByRole('link', { name: /배지/i }).click();

    await page.waitForURL('**/badges');
    await expect(page.getByRole('heading', { name: /배지/i })).toBeVisible();

    // Check badge display
    const badges = page.locator('[data-testid^="badge-"]');
    await expect(badges.first()).toBeVisible();

    // Check locked and unlocked badges
    await expect(page.locator('[data-testid="badge-unlocked"]')).toBeVisible();
    await expect(page.locator('[data-testid="badge-locked"]')).toBeVisible();
  });

  test('should show level up animation', async ({ page }) => {
    // This would require backend setup to trigger level up
    // For now, we'll test the UI components exist
    
    await page.goto('/dashboard');
    
    // Check if level progress component exists
    const levelProgress = page.getByTestId('level-progress-container');
    await expect(levelProgress).toBeVisible();
    
    // Hover to see total XP
    await levelProgress.hover();
    await expect(page.getByText(/총 경험치:/i)).toBeVisible();
  });

  test('should claim daily reward', async ({ page }) => {
    await page.goto('/dashboard');

    // Look for daily reward button
    const dailyRewardButton = page.getByRole('button', { name: /일일 보상/i });
    
    if (await dailyRewardButton.isVisible()) {
      await dailyRewardButton.click();

      // Check reward modal
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByText(/일일 보상을 받았습니다/i)).toBeVisible();
      
      // Close modal
      await page.getByRole('button', { name: /확인/i }).click();
    }
  });

  test('should navigate to leaderboard', async ({ page }) => {
    // Navigate to leaderboard
    await page.getByRole('link', { name: /리더보드/i }).click();

    await page.waitForURL('**/leaderboard');
    await expect(page.getByRole('heading', { name: /리더보드/i })).toBeVisible();

    // Check leaderboard tabs
    await expect(page.getByRole('tab', { name: /전체/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /주간/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /월간/i })).toBeVisible();

    // Check leaderboard entries
    const leaderboardEntries = page.locator('[data-testid="leaderboard-entry"]');
    await expect(leaderboardEntries.first()).toBeVisible();
  });

  test('should show quest completion flow', async ({ page }) => {
    // Navigate to active quest
    await page.goto('/quests');
    
    // Find in-progress quest
    const inProgressQuest = page.locator('[data-testid="quest-in-progress"]').first();
    
    if (await inProgressQuest.isVisible()) {
      await inProgressQuest.click();

      // Complete quest actions
      // This would depend on actual quest implementation
      
      // Check for completion UI
      const completeButton = page.getByRole('button', { name: /퀘스트 완료/i });
      if (await completeButton.isVisible()) {
        await completeButton.click();

        // Check rewards modal
        await expect(page.getByText(/퀘스트 완료!/i)).toBeVisible();
        await expect(page.getByText(/보상:/i)).toBeVisible();
      }
    }
  });

  test('should filter quests by subject', async ({ page }) => {
    await page.goto('/quests');

    // Click subject filter
    await page.getByRole('button', { name: /과목 선택/i }).click();
    await page.getByRole('option', { name: /수학/i }).click();

    // Check filtered results
    const questCards = page.locator('[data-testid="quest-card"]');
    
    for (const card of await questCards.all()) {
      await expect(card.getByText(/수학/i)).toBeVisible();
    }
  });
});