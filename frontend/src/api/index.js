/**
 * TeacherHub API Service
 * V2 API 클라이언트
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8081";

const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 에러 핸들링 인터셉터
api.interceptors.response.use(
    response => response,
    error => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

/**
 * 학원 API
 */
export const academyApi = {
    getAll: () => api.get('/api/v2/academies'),
    getById: (id) => api.get(`/api/v2/academies/${id}`),
    getStats: (id, date) => api.get(`/api/v2/academies/${id}/stats`, { params: { date } }),
    getTeachers: (id) => api.get(`/api/v2/academies/${id}/teachers`),
};

/**
 * 강사 API
 */
export const teacherApi = {
    getAll: (params) => api.get('/api/v2/teachers', { params }),
    getById: (id) => api.get(`/api/v2/teachers/${id}`),
    getByAcademy: (academyId) => api.get(`/api/v2/teachers`, { params: { academyId } }),
    getMentions: (id, params) => api.get(`/api/v2/teachers/${id}/mentions`, { params }),
    getReports: (id, params) => api.get(`/api/v2/teachers/${id}/reports`, { params }),
    search: (query) => api.get('/api/v2/teachers/search', { params: { q: query } }),
};

/**
 * 데일리 리포트 API
 */
export const reportApi = {
    getDaily: (date) => api.get('/api/v2/reports/daily', { params: { date } }),
    getTeacherReport: (teacherId, date) => api.get(`/api/v2/reports/teacher/${teacherId}`, { params: { date } }),
    getSummary: (date) => api.get('/api/v2/reports/summary', { params: { date } }),
    getTopMentioned: (date, limit = 10) => api.get('/api/v2/reports/top-mentioned', { params: { date, limit } }),
    getTrending: (days = 7) => api.get('/api/v2/reports/trending', { params: { days } }),
};

/**
 * 멘션 API
 */
export const mentionApi = {
    getRecent: (limit = 50) => api.get('/api/v2/mentions/recent', { params: { limit } }),
    getByTeacher: (teacherId, params) => api.get(`/api/v2/mentions/teacher/${teacherId}`, { params }),
    getByDate: (date) => api.get('/api/v2/mentions', { params: { date } }),
};

/**
 * 크롤링 API
 */
export const crawlApi = {
    getLogs: (limit = 10) => api.get('/api/v2/crawl/logs', { params: { limit } }),
    getStatus: () => api.get('/api/v2/crawl/status'),
    trigger: () => api.post('/api/v2/crawl/trigger'),
};

/**
 * 대시보드 API (집계 데이터)
 */
export const dashboardApi = {
    getSummary: () => api.get('/api/v2/dashboard/summary'),
    getAcademyRanking: (date) => api.get('/api/v2/dashboard/academy-ranking', { params: { date } }),
    getTeacherRanking: (date, limit = 20) => api.get('/api/v2/dashboard/teacher-ranking', { params: { date, limit } }),
    getSentimentTrend: (days = 7) => api.get('/api/v2/dashboard/sentiment-trend', { params: { days } }),
};

/**
 * 주간 리포트 API
 */
export const weeklyApi = {
    // 주간 리포트 조회
    getReport: (year, week) => api.get('/api/v2/weekly/report', { params: { year, week } }),

    // 강사별 주간 리포트
    getTeacherReport: (teacherId, year, week) =>
        api.get(`/api/v2/weekly/teacher/${teacherId}`, { params: { year, week } }),

    // 주간 랭킹
    getRanking: (year, week, limit = 20) =>
        api.get('/api/v2/weekly/ranking', { params: { year, week, limit } }),

    // 학원별 주간 통계
    getAcademyStats: (academyId, year, week) =>
        api.get(`/api/v2/weekly/academy/${academyId}`, { params: { year, week } }),

    // 강사 트렌드 (최근 N주)
    getTeacherTrend: (teacherId, weeks = 8) =>
        api.get(`/api/v2/weekly/teacher/${teacherId}/trend`, { params: { weeks } }),

    // 학원 트렌드
    getAcademyTrend: (academyId, weeks = 8) =>
        api.get(`/api/v2/weekly/academy/${academyId}/trend`, { params: { weeks } }),

    // 현재 주 정보
    getCurrentWeek: () => api.get('/api/v2/weekly/current'),

    // 전체 주간 요약
    getSummary: (year, week) =>
        api.get('/api/v2/weekly/summary', { params: { year, week } }),
};

// Legacy API (기존 호환성)
export const legacyApi = {
    getReputation: () => api.get('/api/reputation'),
    getStats: (keyword) => api.get('/api/stats', { params: { keyword } }),
};

export default api;
