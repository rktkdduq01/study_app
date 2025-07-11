import { test, expect } from '@playwright/test';

test.describe('Parent Dashboard', () => {
  // Helper function to login as parent
  async function loginAsParent(page) {
    await page.goto('/');
    await page.getByLabel(/사용자명 또는 이메일/i).fill('parentuser');
    await page.getByLabel(/비밀번호/i).fill('Parent123!');
    await page.getByRole('button', { name: /로그인/i }).click();
    await page.waitForURL('**/parent-dashboard');
  }

  test.beforeEach(async ({ page }) => {
    await loginAsParent(page);
  });

  test('should display parent dashboard', async ({ page }) => {
    // Check parent dashboard elements
    await expect(page.getByRole('heading', { name: /부모님 대시보드/i })).toBeVisible();
    await expect(page.getByText(/자녀 학습 현황/i)).toBeVisible();
    
    // Check child list
    const childCards = page.locator('[data-testid="child-card"]');
    await expect(childCards.first()).toBeVisible();
  });

  test('should view child progress details', async ({ page }) => {
    // Click on a child card
    const childCard = page.locator('[data-testid="child-card"]').first();
    await childCard.click();

    // Check child detail page
    await page.waitForURL(/.*children\/\d+/);
    await expect(page.getByRole('heading', { name: /학습 상세 정보/i })).toBeVisible();

    // Check progress sections
    await expect(page.getByText(/전체 레벨:/i)).toBeVisible();
    await expect(page.getByText(/총 학습 시간:/i)).toBeVisible();
    await expect(page.getByText(/완료한 퀘스트:/i)).toBeVisible();
  });

  test('should view child learning statistics', async ({ page }) => {
    // Navigate to child stats
    const childCard = page.locator('[data-testid="child-card"]').first();
    await childCard.getByRole('button', { name: /통계 보기/i }).click();

    // Check statistics modal
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/학습 통계/i)).toBeVisible();

    // Check stat elements
    await expect(page.getByText(/일일 평균 학습 시간/i)).toBeVisible();
    await expect(page.getByText(/주간 학습 목표 달성률/i)).toBeVisible();
    await expect(page.getByText(/강점 과목/i)).toBeVisible();
    await expect(page.getByText(/개선 필요 과목/i)).toBeVisible();
  });

  test('should set learning goals for child', async ({ page }) => {
    // Click on goals button
    await page.getByRole('button', { name: /학습 목표 설정/i }).click();

    // Fill goal form
    await page.getByLabel(/일일 학습 시간/i).fill('60');
    await page.getByLabel(/주간 퀘스트 목표/i).fill('20');
    
    // Select focus subjects
    await page.getByRole('checkbox', { name: /수학/i }).check();
    await page.getByRole('checkbox', { name: /영어/i }).check();

    // Save goals
    await page.getByRole('button', { name: /저장/i }).click();

    // Check success message
    await expect(page.getByText(/학습 목표가 설정되었습니다/i)).toBeVisible();
  });

  test('should view real-time notifications', async ({ page }) => {
    // Check notifications section
    const notificationsSection = page.getByTestId('notifications-section');
    await expect(notificationsSection).toBeVisible();

    // Check for recent notifications
    const notifications = notificationsSection.locator('[data-testid="notification-item"]');
    
    if (await notifications.count() > 0) {
      // Check notification content
      await expect(notifications.first()).toContainText(/완료|시작|달성/);
    }
  });

  test('should view weekly report', async ({ page }) => {
    // Click weekly report button
    await page.getByRole('button', { name: /주간 리포트/i }).click();

    // Check report modal
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/주간 학습 리포트/i)).toBeVisible();

    // Check report sections
    await expect(page.getByText(/학습 시간 추이/i)).toBeVisible();
    await expect(page.getByText(/과목별 진도/i)).toBeVisible();
    await expect(page.getByText(/획득한 업적/i)).toBeVisible();
    await expect(page.getByText(/완료한 퀘스트/i)).toBeVisible();
  });

  test('should manage child account settings', async ({ page }) => {
    // Navigate to child settings
    await page.getByRole('button', { name: /자녀 계정 관리/i }).click();

    // Check settings page
    await expect(page.getByRole('heading', { name: /자녀 계정 설정/i })).toBeVisible();

    // Check available settings
    await expect(page.getByText(/학습 시간 제한/i)).toBeVisible();
    await expect(page.getByText(/콘텐츠 필터링/i)).toBeVisible();
    await expect(page.getByText(/보상 설정/i)).toBeVisible();
  });

  test('should set screen time limits', async ({ page }) => {
    await page.getByRole('button', { name: /자녀 계정 관리/i }).click();

    // Set daily limit
    await page.getByLabel(/일일 제한 시간/i).fill('120');
    
    // Set blocked hours
    await page.getByLabel(/학습 금지 시간 시작/i).fill('22:00');
    await page.getByLabel(/학습 금지 시간 종료/i).fill('07:00');

    // Save settings
    await page.getByRole('button', { name: /설정 저장/i }).click();

    // Check success message
    await expect(page.getByText(/설정이 저장되었습니다/i)).toBeVisible();
  });

  test('should view achievement history', async ({ page }) => {
    // Navigate to achievements tab
    await page.getByRole('tab', { name: /업적 기록/i }).click();

    // Check achievement list
    const achievementList = page.locator('[data-testid="achievement-history"]');
    await expect(achievementList).toBeVisible();

    // Check achievement items
    const achievements = achievementList.locator('[data-testid="achievement-item"]');
    
    if (await achievements.count() > 0) {
      const firstAchievement = achievements.first();
      await expect(firstAchievement).toContainText(/달성/);
      await expect(firstAchievement).toContainText(/\d{4}-\d{2}-\d{2}/); // Date format
    }
  });

  test('should compare children progress', async ({ page }) => {
    // Only if multiple children exist
    const childCards = page.locator('[data-testid="child-card"]');
    
    if (await childCards.count() > 1) {
      // Click compare button
      await page.getByRole('button', { name: /비교하기/i }).click();

      // Check comparison view
      await expect(page.getByText(/자녀 학습 비교/i)).toBeVisible();
      
      // Check comparison charts
      await expect(page.getByTestId('comparison-chart')).toBeVisible();
      await expect(page.getByText(/레벨 비교/i)).toBeVisible();
      await expect(page.getByText(/학습 시간 비교/i)).toBeVisible();
    }
  });

  test('should export learning report', async ({ page }) => {
    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /리포트 다운로드/i }).click();

    // Select report options
    await page.getByRole('checkbox', { name: /학습 통계/i }).check();
    await page.getByRole('checkbox', { name: /업적 기록/i }).check();
    await page.getByRole('checkbox', { name: /퀘스트 기록/i }).check();

    // Download report
    await page.getByRole('button', { name: /PDF 다운로드/i }).click();
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/learning-report.*\.pdf/);
  });

  test('should receive real-time progress updates', async ({ page }) => {
    // This test simulates real-time updates via WebSocket
    
    // Check for live indicator
    await expect(page.getByTestId('live-indicator')).toBeVisible();
    await expect(page.getByText(/실시간 업데이트 중/i)).toBeVisible();

    // Wait for any real-time update
    // In real app, this would be triggered by child's activity
    const progressUpdate = page.locator('[data-testid="real-time-update"]');
    
    // If update appears, check its content
    if (await progressUpdate.isVisible({ timeout: 5000 })) {
      await expect(progressUpdate).toContainText(/진행 중|완료/);
    }
  });
});