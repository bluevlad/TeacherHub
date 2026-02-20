import { defineConfig, devices } from '@playwright/test';

/**
 * TeacherHub E2E 테스트 설정
 *
 * 실행 방법:
 *   npm run test:e2e           # 전체 테스트 실행
 *   npm run test:e2e:ui        # UI 모드로 실행
 *   npm run test:e2e:headed    # 브라우저 표시하며 실행
 */

export default defineConfig({
  // 테스트 디렉토리
  testDir: './tests',

  // 테스트 파일 패턴
  testMatch: '**/*.spec.ts',

  // 병렬 실행
  fullyParallel: true,

  // CI 환경 설정
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // 타임아웃 설정
  timeout: 30000,
  expect: {
    timeout: 5000,
  },

  // 리포터 설정
  reporter: [
    ['list'],
    ['html', { outputFolder: './playwright-report', open: 'never' }],
    ['json', { outputFile: './test-results.json' }],
  ],

  // 공통 설정
  use: {
    // 기본 URL
    baseURL: process.env.BASE_URL || 'http://study.unmong.com:4010',

    // 추적 및 스크린샷
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // 브라우저 설정
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,

    // 로케일 설정
    locale: 'ko-KR',
    timezoneId: 'Asia/Seoul',
  },

  // 브라우저 프로젝트
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // 모바일 테스트
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  // 출력 디렉토리
  outputDir: './test-results',
});
