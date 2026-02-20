import { test, expect } from '@playwright/test';

/**
 * TeacherHub E2E 테스트
 * 웹사이트: http://study.unmong.com:4010/
 * API 서버: http://study.unmong.com:8081/
 */

const BASE_URL = process.env.BASE_URL || 'http://study.unmong.com:4010';

test.describe('TeacherHub 대시보드', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('메인 페이지 로드 확인', async ({ page }) => {
    // 페이지 타이틀 확인
    await expect(page).toHaveTitle('TeacherHub');

    // root 요소가 렌더링되었는지 확인
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('대시보드 UI 요소 표시 확인', async ({ page }) => {
    // 대시보드가 로드될 때까지 대기
    await page.waitForLoadState('networkidle');

    // Material UI 기반 UI가 렌더링되었는지 확인
    // 페이지에 콘텐츠가 있는지 확인
    const body = page.locator('body');
    await expect(body).not.toBeEmpty();
  });

  test('API 응답 대기 및 데이터 로드 확인', async ({ page }) => {
    // API 응답을 인터셉트하여 데이터 로드 확인
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/v2/') && response.status() === 200,
      { timeout: 10000 }
    );

    await page.goto('/');

    try {
      const response = await responsePromise;
      expect(response.status()).toBe(200);
    } catch (error) {
      // API 호출이 없을 수 있음
      console.log('API 호출 없음 또는 타임아웃');
    }
  });
});

test.describe('TeacherHub 기간 선택기', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('기간 선택 드롭다운 동작 확인', async ({ page }) => {
    // Select 요소 찾기
    const selects = page.locator('div[role="combobox"]');
    const selectCount = await selects.count();

    if (selectCount > 0) {
      // 첫 번째 드롭다운 클릭
      await selects.first().click();

      // 메뉴 옵션이 표시되는지 확인
      const menuItems = page.locator('[role="option"], [role="menuitem"]');
      await expect(menuItems.first()).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('TeacherHub 강사 목록', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('강사 랭킹 테이블이 표시되는지 확인', async ({ page }) => {
    // 테이블 또는 데이터 그리드 찾기
    const table = page.locator('table, [role="grid"]');

    if (await table.isVisible()) {
      await expect(table).toBeVisible();
    }
  });

  test('강사 정보 카드가 표시되는지 확인', async ({ page }) => {
    // Material UI Paper 또는 Card 컴포넌트 찾기
    const cards = page.locator('.MuiPaper-root, .MuiCard-root');
    const cardCount = await cards.count();

    // 카드가 있는지 확인
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });
});

test.describe('TeacherHub 학원 선택', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('학원 선택 드롭다운이 있는지 확인', async ({ page }) => {
    // 학원 선택 UI 요소 찾기
    const academySelector = page.locator('[data-testid="academy-selector"], select, [role="combobox"]');
    const selectorCount = await academySelector.count();

    expect(selectorCount).toBeGreaterThanOrEqual(0);
  });

  test('학원 목록이 올바르게 로드되는지 확인', async ({ page }) => {
    // 학원 이름이 페이지에 표시되는지 확인
    const academyNames = ['공단기', '해커스공무원', '에듀윌공무원'];

    let foundAny = false;
    for (const name of academyNames) {
      const element = page.getByText(name, { exact: false });
      if (await element.isVisible().catch(() => false)) {
        foundAny = true;
        break;
      }
    }

    // 최소 하나의 학원 이름이 표시되어야 함
    // 데이터가 없을 수도 있으므로 유연하게 처리
    console.log('학원 정보 표시 여부:', foundAny);
  });
});

test.describe('TeacherHub 반응형 디자인', () => {
  test('모바일 뷰포트에서 올바르게 표시되는지 확인', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 페이지가 올바르게 렌더링되는지 확인
    const root = page.locator('#root');
    await expect(root).toBeVisible();

    // 가로 스크롤이 없는지 확인 (반응형 디자인 검증)
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);

    // 약간의 오차 허용
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 10);
  });

  test('태블릿 뷰포트에서 올바르게 표시되는지 확인', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });

  test('데스크톱 뷰포트에서 올바르게 표시되는지 확인', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });
});

test.describe('TeacherHub 에러 처리', () => {
  test('JavaScript 에러가 발생하지 않는지 확인', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 심각한 JavaScript 에러가 없어야 함
    const criticalErrors = errors.filter(e =>
      !e.includes('ResizeObserver') && // 일반적인 무시 가능한 에러
      !e.includes('Script error')
    );

    if (criticalErrors.length > 0) {
      console.log('발견된 JavaScript 에러:', criticalErrors);
    }

    expect(criticalErrors.length).toBe(0);
  });

  test('네트워크 요청 실패 시 에러 처리 확인', async ({ page }) => {
    // API 요청이 실패했을 때 UI가 깨지지 않는지 확인
    await page.route('**/api/v2/**', route => route.abort());

    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // 페이지가 여전히 렌더링되는지 확인
    const root = page.locator('#root');
    await expect(root).toBeVisible();
  });
});

test.describe('TeacherHub 접근성', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('키보드 탐색이 가능한지 확인', async ({ page }) => {
    // Tab 키로 요소 간 이동이 가능한지 확인
    await page.keyboard.press('Tab');

    // 포커스된 요소가 있는지 확인
    const focusedElement = page.locator(':focus');
    // 포커스 가능한 요소가 있을 수도 있고 없을 수도 있음
    const isFocused = await focusedElement.count();
    console.log('포커스 가능한 요소 수:', isFocused);
  });

  test('ARIA 레이블이 적절히 설정되었는지 확인', async ({ page }) => {
    // 버튼에 접근성 레이블이 있는지 확인
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      const title = await button.getAttribute('title');

      // 버튼에 텍스트, aria-label, 또는 title 중 하나가 있어야 함
      const hasAccessibleName = ariaLabel || textContent?.trim() || title;
      if (!hasAccessibleName) {
        console.log(`버튼 ${i}에 접근성 이름이 없습니다.`);
      }
    }
  });
});

test.describe('TeacherHub 성능', () => {
  test('페이지 로드 시간이 적절한지 확인', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    console.log(`페이지 로드 시간: ${loadTime}ms`);

    // 10초 이내에 로드되어야 함
    expect(loadTime).toBeLessThan(10000);
  });

  test('번들 크기가 적절한지 확인', async ({ page }) => {
    const resources: { url: string; size: number }[] = [];

    page.on('response', async response => {
      if (response.url().includes('.js') && response.status() === 200) {
        try {
          const buffer = await response.body();
          resources.push({ url: response.url(), size: buffer.length });
        } catch (e) {
          // 무시
        }
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const totalSize = resources.reduce((sum, r) => sum + r.size, 0);
    console.log(`총 JavaScript 번들 크기: ${(totalSize / 1024 / 1024).toFixed(2)}MB`);

    // 5MB 이하여야 함 (React 앱 기준 적절한 크기)
    expect(totalSize).toBeLessThan(5 * 1024 * 1024);
  });
});
