/**
 * Dashboard Page
 * 메인 대시보드 페이지
 */
import React, { useState, useEffect } from 'react';
import {
    Container, Grid, Paper, Typography, Box, Card, CardContent,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Chip, CircularProgress, Alert, Tabs, Tab
} from '@mui/material';
import {
    TrendingUp, TrendingDown, People, School, Comment, ThumbUp
} from '@mui/icons-material';
import { dashboardApi } from '../api';

// 통계 카드 컴포넌트
const StatCard = ({ title, value, icon, change, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
        <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                        {title}
                    </Typography>
                    <Typography variant="h4" component="div">
                        {value}
                    </Typography>
                    {change !== undefined && (
                        <Box display="flex" alignItems="center" mt={1}>
                            {change >= 0 ? (
                                <TrendingUp fontSize="small" color="success" />
                            ) : (
                                <TrendingDown fontSize="small" color="error" />
                            )}
                            <Typography
                                variant="body2"
                                color={change >= 0 ? 'success.main' : 'error.main'}
                                ml={0.5}
                            >
                                {change >= 0 ? '+' : ''}{change}% 전일 대비
                            </Typography>
                        </Box>
                    )}
                </Box>
                <Box
                    sx={{
                        backgroundColor: `${color}.light`,
                        borderRadius: 2,
                        p: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}
                >
                    {icon}
                </Box>
            </Box>
        </CardContent>
    </Card>
);

// 감성 칩 컴포넌트
const SentimentChip = ({ sentiment, score }) => {
    const getColor = () => {
        if (sentiment === 'POSITIVE') return 'success';
        if (sentiment === 'NEGATIVE') return 'error';
        return 'default';
    };

    return (
        <Chip
            label={`${sentiment} ${score ? `(${(score * 100).toFixed(0)}%)` : ''}`}
            color={getColor()}
            size="small"
        />
    );
};

// 강사 랭킹 테이블
const TeacherRankingTable = ({ data, loading }) => {
    if (loading) {
        return <CircularProgress />;
    }

    return (
        <TableContainer>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>순위</TableCell>
                        <TableCell>강사명</TableCell>
                        <TableCell>학원</TableCell>
                        <TableCell>과목</TableCell>
                        <TableCell align="right">언급수</TableCell>
                        <TableCell>감성</TableCell>
                        <TableCell align="right">추천</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {data.map((teacher, index) => (
                        <TableRow key={teacher.teacherId} hover>
                            <TableCell>
                                <Typography
                                    fontWeight={index < 3 ? 'bold' : 'normal'}
                                    color={index < 3 ? 'primary' : 'inherit'}
                                >
                                    {index + 1}
                                </Typography>
                            </TableCell>
                            <TableCell>{teacher.teacherName}</TableCell>
                            <TableCell>{teacher.academyName}</TableCell>
                            <TableCell>{teacher.subjectName}</TableCell>
                            <TableCell align="right">{teacher.mentionCount}</TableCell>
                            <TableCell>
                                <SentimentChip
                                    sentiment={teacher.avgSentimentScore > 0.2 ? 'POSITIVE' : teacher.avgSentimentScore < -0.2 ? 'NEGATIVE' : 'NEUTRAL'}
                                    score={teacher.avgSentimentScore}
                                />
                            </TableCell>
                            <TableCell align="right">{teacher.recommendationCount}</TableCell>
                        </TableRow>
                    ))}
                    {data.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={7} align="center">
                                데이터가 없습니다.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

// 학원별 통계 테이블
const AcademyStatsTable = ({ data, loading }) => {
    if (loading) {
        return <CircularProgress />;
    }

    return (
        <TableContainer>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>학원</TableCell>
                        <TableCell align="right">총 언급</TableCell>
                        <TableCell align="right">강사 수</TableCell>
                        <TableCell>평균 감성</TableCell>
                        <TableCell>TOP 강사</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {data.map((academy) => (
                        <TableRow key={academy.academyId} hover>
                            <TableCell>
                                <Typography fontWeight="medium">{academy.academyName}</Typography>
                            </TableCell>
                            <TableCell align="right">{academy.totalMentions}</TableCell>
                            <TableCell align="right">{academy.totalTeachersMentioned}</TableCell>
                            <TableCell>
                                <SentimentChip
                                    sentiment={academy.avgSentimentScore > 0.2 ? 'POSITIVE' : academy.avgSentimentScore < -0.2 ? 'NEGATIVE' : 'NEUTRAL'}
                                    score={academy.avgSentimentScore}
                                />
                            </TableCell>
                            <TableCell>{academy.topTeacherName || '-'}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

function Dashboard() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tabValue, setTabValue] = useState(0);
    const [summary, setSummary] = useState({
        totalMentions: 0,
        totalTeachers: 0,
        totalAcademies: 0,
        positiveRatio: 0,
        mentionChange: 0
    });
    const [teacherRanking, setTeacherRanking] = useState([]);
    const [academyStats, setAcademyStats] = useState([]);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        setLoading(true);
        setError(null);

        try {
            // 병렬로 API 호출
            const [summaryRes, teacherRes, academyRes] = await Promise.all([
                dashboardApi.getSummary().catch(() => ({ data: {} })),
                dashboardApi.getTeacherRanking(null, 20).catch(() => ({ data: [] })),
                dashboardApi.getAcademyRanking().catch(() => ({ data: [] }))
            ]);

            setSummary(summaryRes.data || {});
            setTeacherRanking(teacherRes.data || []);
            setAcademyStats(academyRes.data || []);

        } catch (err) {
            console.error('Dashboard fetch error:', err);
            setError('데이터를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    return (
        <Container maxWidth="xl" sx={{ py: 3 }}>
            {/* 헤더 */}
            <Box mb={4}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    TeacherHub Dashboard
                </Typography>
                <Typography variant="subtitle1" color="textSecondary">
                    공무원 학원 강사 평판 분석 시스템
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            {/* 통계 카드 */}
            <Grid container spacing={3} mb={4}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="오늘 총 언급"
                        value={summary.totalMentions || 0}
                        icon={<Comment color="primary" />}
                        change={summary.mentionChange}
                        color="primary"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="언급된 강사"
                        value={summary.totalTeachers || 0}
                        icon={<People color="secondary" />}
                        color="secondary"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="모니터링 학원"
                        value={summary.totalAcademies || 4}
                        icon={<School color="info" />}
                        color="info"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="긍정 비율"
                        value={`${(summary.positiveRatio || 0).toFixed(1)}%`}
                        icon={<ThumbUp color="success" />}
                        color="success"
                    />
                </Grid>
            </Grid>

            {/* 탭 메뉴 */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="강사 랭킹" />
                    <Tab label="학원별 통계" />
                </Tabs>
            </Paper>

            {/* 탭 컨텐츠 */}
            <Paper sx={{ p: 2 }}>
                {tabValue === 0 && (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            오늘의 강사 언급 랭킹
                        </Typography>
                        <TeacherRankingTable data={teacherRanking} loading={loading} />
                    </Box>
                )}
                {tabValue === 1 && (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            학원별 통계
                        </Typography>
                        <AcademyStatsTable data={academyStats} loading={loading} />
                    </Box>
                )}
            </Paper>
        </Container>
    );
}

export default Dashboard;
