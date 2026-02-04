/**
 * Dashboard Page
 * 메인 대시보드 페이지 - 일별/주별/월별 기간 선택
 */
import React, { useState } from 'react';
import {
    Container, Grid, Paper, Typography, Box, Card, CardContent,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Chip, CircularProgress, Alert, Tabs, Tab
} from '@mui/material';
import {
    TrendingUp, TrendingDown, People, School, Comment, ThumbUp
} from '@mui/icons-material';
import PeriodSelector from '../components/PeriodSelector';
import { reportApi, dashboardApi } from '../api';

// 통계 카드 컴포넌트
const StatCard = ({ title, value, icon, subValue, color = 'primary' }) => (
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
                    {subValue && (
                        <Typography variant="body2" color="textSecondary" mt={1}>
                            {subValue}
                        </Typography>
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
const SentimentChip = ({ score }) => {
    let sentiment = 'NEUTRAL';
    let color = 'default';

    if (score > 0.2) {
        sentiment = 'POSITIVE';
        color = 'success';
    } else if (score < -0.2) {
        sentiment = 'NEGATIVE';
        color = 'error';
    }

    const label = score !== null && score !== undefined
        ? `${sentiment} (${(score * 100).toFixed(0)}%)`
        : 'N/A';

    return (
        <Chip label={label} color={color} size="small" />
    );
};

// 강사 랭킹 테이블
const TeacherRankingTable = ({ data, loading, periodLabel }) => {
    if (loading) {
        return (
            <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
            </Box>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Box p={3} textAlign="center">
                <Typography color="textSecondary">
                    해당 기간에 데이터가 없습니다.
                </Typography>
            </Box>
        );
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
                        <TableCell align="center">긍정/부정</TableCell>
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
                                    color={index === 0 ? 'error' : index < 3 ? 'primary' : 'inherit'}
                                >
                                    {index + 1}
                                </Typography>
                            </TableCell>
                            <TableCell>
                                <Typography fontWeight="medium">
                                    {teacher.teacherName}
                                </Typography>
                            </TableCell>
                            <TableCell>{teacher.academyName}</TableCell>
                            <TableCell>{teacher.subjectName}</TableCell>
                            <TableCell align="right">
                                <Typography fontWeight="medium">
                                    {teacher.mentionCount}
                                </Typography>
                            </TableCell>
                            <TableCell align="center">
                                <Box display="flex" gap={0.5} justifyContent="center">
                                    <Chip
                                        label={teacher.positiveCount}
                                        size="small"
                                        color="success"
                                        variant="outlined"
                                    />
                                    <Chip
                                        label={teacher.negativeCount}
                                        size="small"
                                        color="error"
                                        variant="outlined"
                                    />
                                </Box>
                            </TableCell>
                            <TableCell>
                                <SentimentChip score={teacher.avgSentimentScore} />
                            </TableCell>
                            <TableCell align="right">{teacher.recommendationCount}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

// 학원별 통계 테이블
const AcademyStatsTable = ({ data, loading }) => {
    if (loading) {
        return (
            <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
            </Box>
        );
    }

    if (!data || data.length === 0) {
        return (
            <Box p={3} textAlign="center">
                <Typography color="textSecondary">
                    해당 기간에 데이터가 없습니다.
                </Typography>
            </Box>
        );
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
                        <TableRow key={academy.academyName} hover>
                            <TableCell>
                                <Typography fontWeight="medium">{academy.academyName}</Typography>
                            </TableCell>
                            <TableCell align="right">{academy.totalMentions}</TableCell>
                            <TableCell align="right">{academy.totalTeachersMentioned}</TableCell>
                            <TableCell>
                                <SentimentChip score={academy.avgSentimentScore} />
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
    const [currentPeriod, setCurrentPeriod] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [academyStats, setAcademyStats] = useState([]);

    // 기간 변경 핸들러
    const handlePeriodChange = async (periodParams) => {
        setLoading(true);
        setError(null);
        setCurrentPeriod(periodParams);

        try {
            let response;

            switch (periodParams.periodType) {
                case 'daily':
                    response = await reportApi.getDaily(periodParams.date);
                    break;
                case 'weekly':
                    response = await reportApi.getWeekly(periodParams.year, periodParams.week);
                    break;
                case 'monthly':
                    response = await reportApi.getMonthly(periodParams.year, periodParams.month);
                    break;
                default:
                    response = await reportApi.getDaily();
            }

            setReportData(response.data);

            // 학원별 통계도 로드
            try {
                const academyRes = await dashboardApi.getAcademyRanking();
                setAcademyStats(academyRes.data || []);
            } catch (e) {
                console.error('Academy stats error:', e);
            }

        } catch (err) {
            console.error('Report fetch error:', err);
            setError('데이터를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleTabChange = (event, newValue) => {
        setTabValue(newValue);
    };

    // 기간 유형 한글 변환
    const getPeriodTypeLabel = (type) => {
        switch (type) {
            case 'daily': return '일별';
            case 'weekly': return '주별';
            case 'monthly': return '월별';
            default: return '';
        }
    };

    return (
        <Container maxWidth="xl" sx={{ py: 3 }}>
            {/* 헤더 */}
            <Box mb={3}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    TeacherHub Dashboard
                </Typography>
                <Typography variant="subtitle1" color="textSecondary">
                    공무원 학원 강사 평판 분석 시스템
                </Typography>
            </Box>

            {/* 기간 선택 */}
            <PeriodSelector onPeriodChange={handlePeriodChange} />

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            {/* 현재 기간 표시 */}
            {currentPeriod && reportData && (
                <Box mb={3}>
                    <Chip
                        label={`${getPeriodTypeLabel(currentPeriod.periodType)} | ${reportData.periodLabel || currentPeriod.label}`}
                        color="primary"
                        variant="outlined"
                    />
                    {reportData.startDate !== reportData.endDate && (
                        <Typography variant="body2" color="textSecondary" mt={1}>
                            {reportData.startDate} ~ {reportData.endDate}
                        </Typography>
                    )}
                </Box>
            )}

            {/* 통계 카드 */}
            <Grid container spacing={3} mb={4}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="총 언급"
                        value={reportData?.totalMentions || 0}
                        icon={<Comment color="primary" />}
                        subValue={`${reportData?.totalTeachers || 0}명 강사`}
                        color="primary"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="긍정 언급"
                        value={reportData?.totalPositive || 0}
                        icon={<TrendingUp color="success" />}
                        subValue={`${reportData?.positiveRatio || 0}%`}
                        color="success"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="부정 언급"
                        value={reportData?.totalNegative || 0}
                        icon={<TrendingDown color="error" />}
                        color="error"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="평균 감성점수"
                        value={reportData?.avgSentimentScore?.toFixed(2) || '0.00'}
                        icon={<ThumbUp color="info" />}
                        subValue={reportData?.avgSentimentScore > 0.2 ? '긍정적' : reportData?.avgSentimentScore < -0.2 ? '부정적' : '중립'}
                        color="info"
                    />
                </Grid>
            </Grid>

            {/* 탭 메뉴 */}
            <Paper sx={{ mb: 3 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                    <Tab label="강사 랭킹" icon={<People />} iconPosition="start" />
                    <Tab label="학원별 통계" icon={<School />} iconPosition="start" />
                </Tabs>
            </Paper>

            {/* 탭 컨텐츠 */}
            <Paper sx={{ p: 2 }}>
                {tabValue === 0 && (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            {currentPeriod?.label || '오늘'} 강사 언급 랭킹
                        </Typography>
                        <TeacherRankingTable
                            data={reportData?.teacherSummaries}
                            loading={loading}
                            periodLabel={currentPeriod?.label}
                        />
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
