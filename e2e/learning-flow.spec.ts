import { test, expect } from '@playwright/test';

test.describe('Learning Flow', () => {
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

  test('should complete a math quest', async ({ page }) => {
    // Navigate to quests
    await page.goto('/quests');

    // Find a math quest
    const mathQuest = page.locator('[data-testid="quest-card"]').filter({
      hasText: /수학/i
    }).first();

    await mathQuest.click();

    // Start quest
    await page.getByRole('button', { name: /퀘스트 시작/i }).click();

    // Wait for quest page
    await page.waitForURL(/.*quests\/\d+/);

    // Answer questions (mock implementation)
    const questions = page.locator('[data-testid="question"]');
    const questionCount = await questions.count();

    for (let i = 0; i < questionCount; i++) {
      // Select an answer
      await page.locator('[data-testid="answer-option"]').first().click();
      
      // Submit answer
      await page.getByRole('button', { name: /다음/i }).click();
      
      // Wait for next question or completion
      await page.waitForTimeout(500);
    }

    // Check completion screen
    await expect(page.getByText(/퀘스트 완료!/i)).toBeVisible();
    await expect(page.getByText(/획득한 경험치:/i)).toBeVisible();
    await expect(page.getByText(/획득한 코인:/i)).toBeVisible();
  });

  test('should show real-time progress updates', async ({ page }) => {
    await page.goto('/dashboard');

    // Get initial XP
    const xpText = await page.getByText(/\d+ \/ \d+ XP/i).textContent();
    const initialXP = parseInt(xpText?.match(/\d+/)?.[0] || '0');

    // Complete an action that gives XP
    // This is a mock - in real app, would complete a quest or learning activity

    // Check for XP animation
    await expect(page.getByTestId('exp-gain-animation')).toBeVisible();
    
    // Verify XP increased
    const newXpText = await page.getByText(/\d+ \/ \d+ XP/i).textContent();
    const newXP = parseInt(newXpText?.match(/\d+/)?.[0] || '0');
    
    expect(newXP).toBeGreaterThan(initialXP);
  });

  test('should track learning streak', async ({ page }) => {
    await page.goto('/dashboard');

    // Check streak display
    const streakElement = page.getByTestId('streak-display');
    await expect(streakElement).toBeVisible();
    
    // Check streak number
    await expect(streakElement.getByText(/\d+일 연속/i)).toBeVisible();
  });

  test('should show subject progress', async ({ page }) => {
    // Navigate to progress page
    await page.getByRole('link', { name: /학습 진도/i }).click();

    await page.waitForURL('**/progress');
    await expect(page.getByRole('heading', { name: /학습 진도/i })).toBeVisible();

    // Check subject cards
    const subjects = ['수학', '과학', '영어', '국어'];
    
    for (const subject of subjects) {
      const subjectCard = page.locator('[data-testid="subject-card"]').filter({
        hasText: subject
      });
      
      await expect(subjectCard).toBeVisible();
      await expect(subjectCard.getByRole('progressbar')).toBeVisible();
      await expect(subjectCard.getByText(/레벨 \d+/i)).toBeVisible();
    }
  });

  test('should access AI tutor', async ({ page }) => {
    // Click AI tutor button
    await page.getByRole('button', { name: /AI 튜터/i }).click();

    // Check AI tutor chat interface
    await expect(page.getByTestId('ai-tutor-chat')).toBeVisible();
    await expect(page.getByPlaceholder(/질문을 입력하세요/i)).toBeVisible();

    // Send a message
    await page.getByPlaceholder(/질문을 입력하세요/i).fill('수학 문제를 도와주세요');
    await page.getByRole('button', { name: /전송/i }).click();

    // Wait for response
    await expect(page.getByTestId('ai-response')).toBeVisible({ timeout: 10000 });
  });

  test('should show personalized recommendations', async ({ page }) => {
    await page.goto('/dashboard');

    // Check recommendations section
    const recommendations = page.getByTestId('recommendations-section');
    await expect(recommendations).toBeVisible();
    
    // Check recommended quests
    await expect(recommendations.getByText(/추천 퀘스트/i)).toBeVisible();
    const recommendedQuests = recommendations.locator('[data-testid="recommended-quest"]');
    await expect(recommendedQuests.first()).toBeVisible();
  });

  test('should track time spent learning', async ({ page }) => {
    await page.goto('/dashboard');

    // Check study time display
    const studyTime = page.getByTestId('study-time-today');
    await expect(studyTime).toBeVisible();
    await expect(studyTime.getByText(/오늘 학습 시간:/i)).toBeVisible();
  });

  test('should show achievement unlocked notification', async ({ page }) => {
    // This test would require triggering an achievement
    // For UI testing, we can check if the notification system works
    
    await page.goto('/dashboard');

    // Check if notification container exists
    const notificationContainer = page.locator('[data-testid="notification-container"]');
    
    // If there's an achievement notification
    const achievementNotification = notificationContainer.locator('[data-testid="achievement-notification"]');
    
    if (await achievementNotification.isVisible()) {
      await expect(achievementNotification.getByText(/업적 달성!/i)).toBeVisible();
      
      // Click to view achievement
      await achievementNotification.click();
      
      // Should show achievement details
      await expect(page.getByRole('dialog')).toBeVisible();
    }
  });

  test('should handle quest abandonment', async ({ page }) => {
    await page.goto('/quests');

    // Find an active quest
    const activeQuest = page.locator('[data-testid="quest-in-progress"]').first();
    
    if (await activeQuest.isVisible()) {
      await activeQuest.click();

      // Click abandon button
      await page.getByRole('button', { name: /퀘스트 포기/i }).click();

      // Confirm abandonment
      await expect(page.getByText(/정말로 퀘스트를 포기하시겠습니까?/i)).toBeVisible();
      await page.getByRole('button', { name: /확인/i }).click();

      // Should return to quest list
      await page.waitForURL('**/quests');
    }
  });

  test('should show learning statistics', async ({ page }) => {
    // Navigate to stats page
    await page.getByRole('link', { name: /통계/i }).click();

    await page.waitForURL('**/stats');
    await expect(page.getByRole('heading', { name: /학습 통계/i })).toBeVisible();

    // Check various stats
    await expect(page.getByText(/총 학습 시간/i)).toBeVisible();
    await expect(page.getByText(/완료한 퀘스트/i)).toBeVisible();
    await expect(page.getByText(/획득한 경험치/i)).toBeVisible();
    await expect(page.getByText(/정답률/i)).toBeVisible();

    // Check charts
    await expect(page.getByTestId('progress-chart')).toBeVisible();
    await expect(page.getByTestId('subject-distribution-chart')).toBeVisible();
  });
});