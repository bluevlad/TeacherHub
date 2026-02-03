/**
 * Weekly Reports Page
 * 주간 리포트 페이지
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
    Container, Grid, Paper, Typography, Box, Card, CardContent,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    CircularProgress, Alert, Chip, Divider, IconButton
} from '@mui/material';
import {
    TrendingUp, TrendingDown, ThumbUp, Comment,
    ChevronLeft, ChevronRight, EmojiEvents
} from '@mui/icons-material';
import { weeklyApi } from '../api';
import { MentionTrendChart, SentimentTrendChart } from '../components/WeeklyTrendChart';

// 주차 계산 유틸리티
const getISOWeek = (date) => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() + 4 - (d.getDay() || 7));
    const yearStart = new Date(d.getFullYear(), 0, 1);
    const weekNumber = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    return { year: d.getFullYear(), week: weekNumber };
};

// 요약 통계 카드
const SummaryCard = ({ title, value, icon, change, color = 'primary' }) => (
    <Card>
        <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                    <Typography color="textSecondary" variant="body2">
                        {title}
                    </Typography>
                    <Typography variant="h4">
                        {value}
                    </Typography>
                    {change !== undefined && change !== null && (
                        <Box display="flex" alignItems="center" mt={0.5}>
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
                                {change >= 0 ? '+' : ''}{change.toFixed(1)}% 전주대비
                            </Typography>
                        </Box>
                    )}
                </Box>
                <Box sx={{ color: `${color}.main` }}>
                    {icon}
                </Box>
            </Box>
        </CardContent>
    </Card>
);

// 주간 랭킹 테이블
const WeeklyRankingTable = ({ reports, loading }) => {
    if (loading) {
        return (
            <Box display="flex" justifyContent="center" py={3}>
                <CircularProgress />
            </Box>
        );
    }

    if (!reports || reports.length === 0) {
        return (
            <Typography color="textSecondary" align="center" py={3}>
                해당 주차의 리포트가 없습니다.
            </Typography>
        );
    }

    const getRankIcon = (rank) => {
        if (rank === 1) return <EmojiEvents sx={{ color: '#FFD700' }} />;
        if (rank === 2) return <EmojiEvents sx={{ color: '#C0C0C0' }} />;
        if (rank === 3) return <EmojiEvents sx={{ color: '#CD7F32' }} />;
        return null;
    };

    const getSentimentColor = (score) => {
        if (score > 0.2) return 'success';
        if (score < -0.2) return 'error';
        return 'default';
    };

    return (
        <TableContainer>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell width={60}>순위</TableCell>
                        <TableCell>강사명</TableCell>
                        <TableCell>학원</TableCell>
                        <TableCell align="right">총 언급</TableCell>
                        <TableCell align="right">긍정</TableCell>
                        <TableCell align="right">부정</TableCell>
                        <TableCell>감성</TableCell>
                        <TableCell align="right">추천</TableCell>
                        <TableCell>전주 대비</TableCell>
                        <TableCell>키워드</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {reports.map((report, index) => (
                        <TableRow key={report.id || index} hover>
                            <TableCell>
                                <Box display="flex" alignItems="center" gap={0.5}>
                                    {getRankIcon(report.weekly_rank || index + 1)}
                                    <Typography fontWeight={index < 3 ? 'bold' : 'normal'}>
                                        {report.weekly_rank || index + 1}
                                    </Typography>
                                </Box>
                            </TableCell>
                            <TableCell>
                                <Typography fontWeight="medium">
                                    {report.teacher_name}
                                </Typography>
                            </TableCell>
                            <TableCell>{report.academy_name}</TableCell>
                            <TableCell align="right">{report.mention_count}</TableCell>
                            <TableCell align="right">
                                <Typography color="success.main">
                                    {report.positive_count}
                                </Typography>
                            </TableCell>
                            <TableCell align="right">
                                <Typography color="error.main">
                                    {report.negative_count}
                                </Typography>
                            </TableCell>
                            <TableCell>
                                <Chip
                                    size="small"
                                    label={report.avg_sentiment_score ?
                                        `${(report.avg_sentiment_score * 100).toFixed(0)}%` :
                                        '-'
                                    }
                                    color={getSentimentColor(report.avg_sentiment_score)}
                                />
                            </TableCell>
                            <TableCell align="right">
                                <Box display="flex" alignItems="center" justifyContent="flex-end" gap={0.5}>
                                    <ThumbUp fontSize="small" color="primary" />
                                    {report.recommendation_count}
                                </Box>
                            </TableCell>
                            <TableCell>
                                {report.mention_change_rate !== null && report.mention_change_rate !== undefined && (
                                    <Box display="flex" alignItems="center" gap={0.5}>
                                        {report.mention_change_rate >= 0 ? (
                                            <TrendingUp fontSize="small" color="success" />
                                        ) : (
                                            <TrendingDown fontSize="small" color="error" />
                                        )}
                                        <Typography
                                            variant="body2"
                                            color={report.mention_change_rate >= 0 ? 'success.main' : 'error.main'}
                                        >
                                            {report.mention_change_rate >= 0 ? '+' : ''}
                                            {report.mention_change_rate.toFixed(1)}%
                                        </Typography>
                                    </Box>
                                )}
                            </TableCell>
                            <TableCell>
                                <Box display="flex" gap={0.5} flexWrap="wrap">
                                    {report.top_keywords?.slice(0, 3).map((keyword, idx) => (
                                        <Chip key={idx} label={keyword} size="small" variant="outlined" />
                                    ))}
                                </Box>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

function WeeklyReports() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedWeek, setSelectedWeek] = useState(() => getISOWeek(new Date()));
    const [summary, setSummary] = useState(null);
    const [reports, setReports] = useState([]);
    const [trendData, setTrendData] = useState([]);

    const fetchWeeklyData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const [summaryRes, rankingRes] = await Promise.all([
                weeklyApi.getSummary(selectedWeek.year, selectedWeek.week).catch(() => ({ data: null })),
                weeklyApi.getRanking(selectedWeek.year, selectedWeek.week, 30).catch(() => ({ data: [] }))
            ]);

            setSummary(summaryRes.data);
            setReports(rankingRes.data || []);

            // 상위 강사의 트렌드 데이터 조회
            if (rankingRes.data?.length > 0) {
                const topTeacherId = rankingRes.data[0].teacher_id;
                const trendRes = await weeklyApi.getTeacherTrend(topTeacherId, 8).catch(() => ({ data: [] }));
                setTrendData(trendRes.data || []);
            }

        } catch (err) {
            console.error('Failed to fetch weekly reports:', err);
            setError('주간 리포트를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    }, [selectedWeek]);

    useEffect(() => {
        fetchWeeklyData();
    }, [fetchWeeklyData]);

    const handlePrevWeek = () => {
        setSelectedWeek(prev => {
            let newWeek = prev.week - 1;
            let newYear = prev.year;
            if (newWeek < 1) {
                newYear -= 1;
                newWeek = 52;
            }
            return { year: newYear, week: newWeek };
        });
    };

    const handleNextWeek = () => {
        const current = getISOWeek(new Date());
        if (selectedWeek.year < current.year ||
            (selectedWeek.year === current.year && selectedWeek.week < current.week)) {
            setSelectedWeek(prev => {
                let newWeek = prev.week + 1;
                let newYear = prev.year;
                if (newWeek > 52) {
                    newYear += 1;
                    newWeek = 1;
                }
                return { year: newYear, week: newWeek };
            });
        }
    };

    const isCurrentWeek = () => {
        const current = getISOWeek(new Date());
        return selectedWeek.year === current.year && selectedWeek.week === current.week;
    };

    return (
        <Container maxWidth="xl" sx={{ py: 3 }}>
            {/* 헤더 */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
                <Box>
                    <Typography variant="h4" fontWeight="bold" gutterBottom>
                        주간 리포트
                    </Typography>
                    <Typography variant="subtitle1" color="textSecondary">
                        주간 강사 평판 분석 결과
                    </Typography>
                </Box>

                {/* 주차 선택 */}
                <Box display="flex" alignItems="center" gap={1}>
                    <IconButton onClick={handlePrevWeek}>
                        <ChevronLeft />
                    </IconButton>
                    <Paper sx={{ px: 3, py: 1 }}>
                        <Typography variant="h6">
                            {selectedWeek.year}년 {selectedWeek.week}주차
                            {isCurrentWeek() && (
                                <Chip label="현재" size="small" color="primary" sx={{ ml: 1 }} />
                            )}
                        </Typography>
                    </Paper>
                    <IconButton onClick={handleNextWeek} disabled={isCurrentWeek()}>
                        <ChevronRight />
                    </IconButton>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            {/* 요약 통계 */}
            {summary && (
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} sm={6} md={3}>
                        <SummaryCard
                            title="주간 총 언급"
                            value={summary.totalMentions || 0}
                            icon={<Comment fontSize="large" />}
                            change={summary.mentionChangeRate}
                            color="primary"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <SummaryCard
                            title="긍정 언급"
                            value={summary.totalPositive || 0}
                            icon={<ThumbUp fontSize="large" />}
                            color="success"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <SummaryCard
                            title="언급된 강사"
                            value={summary.totalTeachers || 0}
                            icon={<EmojiEvents fontSize="large" />}
                            color="secondary"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <SummaryCard
                            title="총 추천"
                            value={summary.totalRecommendations || 0}
                            icon={<TrendingUp fontSize="large" />}
                            color="info"
                        />
                    </Grid>
                </Grid>
            )}

            {/* 트렌드 차트 */}
            {trendData.length > 0 && (
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                            <MentionTrendChart data={trendData} title="TOP 강사 주간 언급 트렌드" />
                        </Paper>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                            <SentimentTrendChart data={trendData} title="TOP 강사 주간 감성 분포" />
                        </Paper>
                    </Grid>
                </Grid>
            )}

            {/* 주간 랭킹 테이블 */}
            <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                    {selectedWeek.year}년 {selectedWeek.week}주차 강사 랭킹
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <WeeklyRankingTable reports={reports} loading={loading} />
            </Paper>
        </Container>
    );
}

export default WeeklyReports;
