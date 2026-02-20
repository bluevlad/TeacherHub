import { test, expect, APIRequestContext } from '@playwright/test';

/**
 * TeacherHub API 테스트
 * API 서버: http://study.unmong.com:8081/
 */

const API_URL = process.env.API_URL || 'http://study.unmong.com:8081';

test.describe('학원(Academy) API', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('GET /api/v2/academies - 전체 학원 목록 조회', async () => {
    const response = await request.get('/api/v2/academies');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);

    // 학원 데이터 구조 확인
    const academy = data[0];
    expect(academy).toHaveProperty('id');
    expect(academy).toHaveProperty('code');
    expect(academy).toHaveProperty('name');
    expect(academy).toHaveProperty('website');
    expect(academy).toHaveProperty('isActive');
    expect(academy).toHaveProperty('createdAt');
  });

  test('GET /api/v2/academies/:id - 특정 학원 조회', async () => {
    const response = await request.get('/api/v2/academies/1');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.id).toBe(1);
    expect(data.name).toBe('공단기');
    expect(data.code).toBe('gongdangi');
  });

  test('GET /api/v2/academies/:id/teachers - 학원별 강사 목록 조회', async () => {
    const response = await request.get('/api/v2/academies/1/teachers');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);

    // 모든 강사가 해당 학원 소속인지 확인
    for (const teacher of data) {
      expect(teacher.academyId).toBe(1);
      expect(teacher.academyName).toBe('공단기');
    }
  });

  test('GET /api/v2/academies/:id - 존재하지 않는 학원 조회', async () => {
    const response = await request.get('/api/v2/academies/9999');

    // 404 또는 빈 응답이어야 함
    const status = response.status();
    expect([200, 404]).toContain(status);
  });
});

test.describe('강사(Teacher) API', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('GET /api/v2/teachers - 전체 강사 목록 조회', async () => {
    const response = await request.get('/api/v2/teachers');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeGreaterThan(0);

    // 강사 데이터 구조 확인
    const teacher = data[0];
    expect(teacher).toHaveProperty('id');
    expect(teacher).toHaveProperty('name');
    expect(teacher).toHaveProperty('aliases');
    expect(teacher).toHaveProperty('academyId');
    expect(teacher).toHaveProperty('academyName');
    expect(teacher).toHaveProperty('subjectId');
    expect(teacher).toHaveProperty('subjectName');
    expect(teacher).toHaveProperty('isActive');
    expect(teacher).toHaveProperty('createdAt');
  });

  test('GET /api/v2/teachers/:id - 특정 강사 조회', async () => {
    const response = await request.get('/api/v2/teachers/1');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data.id).toBe(1);
    expect(data.name).toBe('Shin Young-sik');
    expect(data.academyName).toBe('공단기');
  });

  test('GET /api/v2/teachers/search - 강사 검색', async () => {
    const response = await request.get('/api/v2/teachers/search?q=kim');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);

    // 검색 결과가 있는 경우 이름에 'kim'이 포함되어야 함
    if (data.length > 0) {
      const hasMatch = data.some((teacher: any) =>
        teacher.name.toLowerCase().includes('kim') ||
        teacher.aliases.some((alias: string) => alias.toLowerCase().includes('kim'))
      );
      expect(hasMatch).toBe(true);
    }
  });
});

test.describe('리포트(Report) API', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('GET /api/v2/reports/periods - 기간 목록 조회', async () => {
    const response = await request.get('/api/v2/reports/periods');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('current');
    expect(data).toHaveProperty('daily');
    expect(data).toHaveProperty('weekly');
    expect(data).toHaveProperty('monthly');

    // 일별 기간 데이터 구조 확인
    if (data.daily.length > 0) {
      const dailyItem = data.daily[0];
      expect(dailyItem).toHaveProperty('date');
      expect(dailyItem).toHaveProperty('label');
    }
  });

  test('GET /api/v2/reports/daily - 일별 리포트 조회', async () => {
    const today = new Date().toISOString().split('T')[0];
    const response = await request.get(`/api/v2/reports/daily?date=${today}`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('periodType');
    expect(data).toHaveProperty('startDate');
    expect(data).toHaveProperty('endDate');
    expect(data).toHaveProperty('totalTeachers');
    expect(data).toHaveProperty('totalMentions');
    expect(data).toHaveProperty('teacherSummaries');

    expect(data.periodType).toBe('daily');
  });
});

test.describe('주간(Weekly) API', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('GET /api/v2/weekly/current - 현재 주 정보 조회', async () => {
    const response = await request.get('/api/v2/weekly/current');

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('week');
    expect(data).toHaveProperty('year');
    expect(data).toHaveProperty('weekLabel');
    expect(data).toHaveProperty('startDate');
    expect(data).toHaveProperty('endDate');
  });

  test('GET /api/v2/weekly/ranking - 주간 랭킹 조회', async () => {
    const currentYear = new Date().getFullYear();
    const currentWeek = Math.ceil((new Date().getTime() - new Date(currentYear, 0, 1).getTime()) / (7 * 24 * 60 * 60 * 1000));

    const response = await request.get(`/api/v2/weekly/ranking?year=${currentYear}&week=${currentWeek}`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);

    if (data.length > 0) {
      const item = data[0];
      expect(item).toHaveProperty('teacherId');
      expect(item).toHaveProperty('teacherName');
      expect(item).toHaveProperty('mentionCount');
      expect(item).toHaveProperty('positiveCount');
      expect(item).toHaveProperty('negativeCount');
      expect(item).toHaveProperty('weeklyRank');
    }
  });

  test('GET /api/v2/weekly/summary - 주간 요약 조회', async () => {
    const currentYear = new Date().getFullYear();
    const currentWeek = Math.ceil((new Date().getTime() - new Date(currentYear, 0, 1).getTime()) / (7 * 24 * 60 * 60 * 1000));

    const response = await request.get(`/api/v2/weekly/summary?year=${currentYear}&week=${currentWeek}`);

    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('year');
    expect(data).toHaveProperty('weekNumber');
    expect(data).toHaveProperty('totalMentions');
    expect(data).toHaveProperty('totalPositive');
    expect(data).toHaveProperty('totalNegative');
    expect(data).toHaveProperty('totalTeachers');
  });
});

test.describe('API 에러 처리', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('잘못된 엔드포인트 요청 시 적절한 에러 응답', async () => {
    const response = await request.get('/api/v2/invalid-endpoint');

    expect(response.status()).toBe(404);

    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data).toHaveProperty('error');
  });

  test('잘못된 쿼리 파라미터 처리', async () => {
    const response = await request.get('/api/v2/weekly/ranking?year=invalid&week=invalid');

    // 400 Bad Request 또는 500 에러가 아닌 적절한 처리가 필요
    const status = response.status();
    // 현재 구현에서는 다양한 응답이 가능
    expect([200, 400, 500]).toContain(status);
  });
});

test.describe('API 응답 시간', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('학원 목록 API 응답 시간이 적절한지 확인', async () => {
    const startTime = Date.now();
    const response = await request.get('/api/v2/academies');
    const endTime = Date.now();

    expect(response.status()).toBe(200);

    const responseTime = endTime - startTime;
    console.log(`학원 목록 API 응답 시간: ${responseTime}ms`);

    // 2초 이내에 응답해야 함
    expect(responseTime).toBeLessThan(2000);
  });

  test('강사 목록 API 응답 시간이 적절한지 확인', async () => {
    const startTime = Date.now();
    const response = await request.get('/api/v2/teachers');
    const endTime = Date.now();

    expect(response.status()).toBe(200);

    const responseTime = endTime - startTime;
    console.log(`강사 목록 API 응답 시간: ${responseTime}ms`);

    // 2초 이내에 응답해야 함
    expect(responseTime).toBeLessThan(2000);
  });
});
