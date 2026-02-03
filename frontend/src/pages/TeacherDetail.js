/**
 * Teacher Detail Page
 * 강사 상세 페이지
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Container, Grid, Paper, Typography, Box,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Chip, CircularProgress, Alert, Button, Divider,
    List, ListItem, ListItemText, Avatar
} from '@mui/material';
import {
    ArrowBack, TrendingUp, TrendingDown, School, MenuBook,
    ThumbUp
} from '@mui/icons-material';
import { teacherApi, reportApi } from '../api';

// 감성 바 컴포넌트
const SentimentBar = ({ positive, negative, neutral }) => {
    const total = positive + negative + neutral;
    if (total === 0) return null;

    const posPercent = (positive / total) * 100;
    const negPercent = (negative / total) * 100;
    const neuPercent = (neutral / total) * 100;

    return (
        <Box sx={{ width: '100%', mt: 1 }}>
            <Box display="flex" height={20} borderRadius={1} overflow="hidden">
                <Box sx={{ width: `${posPercent}%`, bgcolor: 'success.main' }} />
                <Box sx={{ width: `${neuPercent}%`, bgcolor: 'grey.400' }} />
                <Box sx={{ width: `${negPercent}%`, bgcolor: 'error.main' }} />
            </Box>
            <Box display="flex" justifyContent="space-between" mt={0.5}>
                <Typography variant="caption" color="success.main">
                    긍정 {posPercent.toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="textSecondary">
                    중립 {neuPercent.toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="error.main">
                    부정 {negPercent.toFixed(0)}%
                </Typography>
            </Box>
        </Box>
    );
};

// 난이도 표시 컴포넌트
const DifficultyDisplay = ({ easy, medium, hard }) => {
    const total = easy + medium + hard;
    if (total === 0) return <Typography color="textSecondary">데이터 없음</Typography>;

    const getDominant = () => {
        if (easy >= medium && easy >= hard) return { label: '쉬움', color: 'success' };
        if (hard >= easy && hard >= medium) return { label: '어려움', color: 'error' };
        return { label: '보통', color: 'warning' };
    };

    const dominant = getDominant();

    return (
        <Box>
            <Chip label={dominant.label} color={dominant.color} size="small" />
            <Typography variant="caption" display="block" mt={0.5} color="textSecondary">
                쉬움 {easy} / 보통 {medium} / 어려움 {hard}
            </Typography>
        </Box>
    );
};

// 멘션 목록 컴포넌트
const MentionList = ({ mentions, loading }) => {
    if (loading) {
        return <CircularProgress />;
    }

    if (!mentions || mentions.length === 0) {
        return (
            <Typography color="textSecondary" align="center" py={3}>
                최근 멘션이 없습니다.
            </Typography>
        );
    }

    const getSentimentColor = (sentiment) => {
        if (sentiment === 'POSITIVE') return 'success.main';
        if (sentiment === 'NEGATIVE') return 'error.main';
        return 'text.secondary';
    };

    return (
        <List>
            {mentions.map((mention, index) => (
                <React.Fragment key={mention.id || index}>
                    <ListItem alignItems="flex-start">
                        <ListItemText
                            primary={
                                <Box display="flex" alignItems="center" gap={1}>
                                    <Chip
                                        label={mention.mentionType}
                                        size="small"
                                        variant="outlined"
                                    />
                                    <Chip
                                        label={mention.sentiment}
                                        size="small"
                                        sx={{ color: getSentimentColor(mention.sentiment) }}
                                    />
                                    {mention.isRecommended && (
                                        <Chip label="추천" size="small" color="primary" />
                                    )}
                                </Box>
                            }
                            secondary={
                                <Typography
                                    variant="body2"
                                    color="textSecondary"
                                    sx={{ mt: 1 }}
                                >
                                    {mention.context}
                                </Typography>
                            }
                        />
                    </ListItem>
                    {index < mentions.length - 1 && <Divider component="li" />}
                </React.Fragment>
            ))}
        </List>
    );
};

// 히스토리 차트 (간단한 테이블 형태)
const ReportHistory = ({ reports, loading }) => {
    if (loading) {
        return <CircularProgress />;
    }

    if (!reports || reports.length === 0) {
        return (
            <Typography color="textSecondary" align="center" py={3}>
                리포트 기록이 없습니다.
            </Typography>
        );
    }

    return (
        <TableContainer>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>날짜</TableCell>
                        <TableCell align="right">언급</TableCell>
                        <TableCell align="right">긍정</TableCell>
                        <TableCell align="right">부정</TableCell>
                        <TableCell align="right">추천</TableCell>
                        <TableCell>변화</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {reports.map((report) => (
                        <TableRow key={report.id}>
                            <TableCell>{report.reportDate}</TableCell>
                            <TableCell align="right">{report.mentionCount}</TableCell>
                            <TableCell align="right">{report.positiveCount}</TableCell>
                            <TableCell align="right">{report.negativeCount}</TableCell>
                            <TableCell align="right">{report.recommendationCount}</TableCell>
                            <TableCell>
                                {report.mentionChange !== 0 && (
                                    <Box display="flex" alignItems="center">
                                        {report.mentionChange > 0 ? (
                                            <TrendingUp fontSize="small" color="success" />
                                        ) : (
                                            <TrendingDown fontSize="small" color="error" />
                                        )}
                                        <Typography
                                            variant="body2"
                                            color={report.mentionChange > 0 ? 'success.main' : 'error.main'}
                                        >
                                            {report.mentionChange > 0 ? '+' : ''}{report.mentionChange}
                                        </Typography>
                                    </Box>
                                )}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

function TeacherDetail() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [teacher, setTeacher] = useState(null);
    const [todayReport, setTodayReport] = useState(null);
    const [mentions, setMentions] = useState([]);
    const [reportHistory, setReportHistory] = useState([]);

    useEffect(() => {
        if (id) {
            fetchTeacherData(id);
        }
    }, [id]);

    const fetchTeacherData = async (teacherId) => {
        setLoading(true);
        setError(null);

        try {
            const [teacherRes, reportRes, mentionsRes, historyRes] = await Promise.all([
                teacherApi.getById(teacherId).catch(() => ({ data: null })),
                reportApi.getTeacherReport(teacherId).catch(() => ({ data: null })),
                teacherApi.getMentions(teacherId, { limit: 10 }).catch(() => ({ data: [] })),
                teacherApi.getReports(teacherId, { days: 7 }).catch(() => ({ data: [] }))
            ]);

            setTeacher(teacherRes.data);
            setTodayReport(reportRes.data);
            setMentions(mentionsRes.data || []);
            setReportHistory(historyRes.data || []);

        } catch (err) {
            console.error('Teacher fetch error:', err);
            setError('강사 정보를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Container maxWidth="lg" sx={{ py: 3 }}>
                <Box display="flex" justifyContent="center" py={10}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    if (error || !teacher) {
        return (
            <Container maxWidth="lg" sx={{ py: 3 }}>
                <Alert severity="error">{error || '강사를 찾을 수 없습니다.'}</Alert>
                <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} sx={{ mt: 2 }}>
                    돌아가기
                </Button>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 3 }}>
            {/* 뒤로가기 버튼 */}
            <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} sx={{ mb: 2 }}>
                목록으로
            </Button>

            {/* 강사 프로필 */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Grid container spacing={3} alignItems="center">
                    <Grid item>
                        <Avatar
                            sx={{ width: 80, height: 80, bgcolor: 'primary.main', fontSize: 32 }}
                        >
                            {teacher.name?.[0]}
                        </Avatar>
                    </Grid>
                    <Grid item xs>
                        <Typography variant="h4" fontWeight="bold">
                            {teacher.name}
                        </Typography>
                        <Box display="flex" gap={2} mt={1}>
                            <Chip
                                icon={<School />}
                                label={teacher.academyName || '학원 정보 없음'}
                                variant="outlined"
                            />
                            <Chip
                                icon={<MenuBook />}
                                label={teacher.subjectName || '과목 정보 없음'}
                                variant="outlined"
                            />
                        </Box>
                        {teacher.aliases && teacher.aliases.length > 0 && (
                            <Typography variant="body2" color="textSecondary" mt={1}>
                                별명: {teacher.aliases.join(', ')}
                            </Typography>
                        )}
                    </Grid>
                </Grid>
            </Paper>

            <Grid container spacing={3}>
                {/* 오늘의 통계 */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, height: '100%' }}>
                        <Typography variant="h6" gutterBottom>
                            오늘의 통계
                        </Typography>
                        <Divider sx={{ mb: 2 }} />

                        {todayReport ? (
                            <Box>
                                <Box mb={2}>
                                    <Typography variant="body2" color="textSecondary">
                                        총 언급
                                    </Typography>
                                    <Typography variant="h4">
                                        {todayReport.mentionCount || 0}
                                        {todayReport.mentionChange !== 0 && (
                                            <Typography
                                                component="span"
                                                variant="body2"
                                                color={todayReport.mentionChange > 0 ? 'success.main' : 'error.main'}
                                                ml={1}
                                            >
                                                ({todayReport.mentionChange > 0 ? '+' : ''}{todayReport.mentionChange})
                                            </Typography>
                                        )}
                                    </Typography>
                                </Box>

                                <Box mb={2}>
                                    <Typography variant="body2" color="textSecondary">
                                        감성 분석
                                    </Typography>
                                    <SentimentBar
                                        positive={todayReport.positiveCount || 0}
                                        negative={todayReport.negativeCount || 0}
                                        neutral={todayReport.neutralCount || 0}
                                    />
                                </Box>

                                <Box mb={2}>
                                    <Typography variant="body2" color="textSecondary">
                                        난이도 평가
                                    </Typography>
                                    <DifficultyDisplay
                                        easy={todayReport.difficultyEasyCount || 0}
                                        medium={todayReport.difficultyMediumCount || 0}
                                        hard={todayReport.difficultyHardCount || 0}
                                    />
                                </Box>

                                <Box>
                                    <Typography variant="body2" color="textSecondary">
                                        추천 언급
                                    </Typography>
                                    <Box display="flex" alignItems="center" gap={1}>
                                        <ThumbUp color="primary" />
                                        <Typography variant="h5">
                                            {todayReport.recommendationCount || 0}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>
                        ) : (
                            <Typography color="textSecondary">
                                오늘 데이터가 없습니다.
                            </Typography>
                        )}
                    </Paper>
                </Grid>

                {/* 최근 멘션 */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            최근 멘션
                        </Typography>
                        <Divider sx={{ mb: 2 }} />
                        <MentionList mentions={mentions} loading={loading} />
                    </Paper>
                </Grid>

                {/* 리포트 히스토리 */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            최근 7일 리포트
                        </Typography>
                        <Divider sx={{ mb: 2 }} />
                        <ReportHistory reports={reportHistory} loading={loading} />
                    </Paper>
                </Grid>

                {/* AI 요약 */}
                {todayReport?.summary && (
                    <Grid item xs={12}>
                        <Paper sx={{ p: 2, bgcolor: 'primary.light' }}>
                            <Typography variant="h6" gutterBottom color="primary.contrastText">
                                AI 요약
                            </Typography>
                            <Typography color="primary.contrastText">
                                {todayReport.summary}
                            </Typography>
                        </Paper>
                    </Grid>
                )}
            </Grid>
        </Container>
    );
}

export default TeacherDetail;
