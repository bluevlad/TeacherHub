/**
 * Academy List Page
 * 학원별 통계 페이지
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Container, Grid, Paper, Typography, Box, Card, CardContent, CardActionArea,
    CircularProgress, Alert, Avatar, Chip, Divider,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import { School, People, TrendingUp, TrendingDown, ThumbUp } from '@mui/icons-material';
import { academyApi, dashboardApi } from '../api';

// 학원 카드 컴포넌트
const AcademyCard = ({ academy, stats, onClick }) => {
    const getSentimentIcon = () => {
        if (!stats?.avgSentimentScore) return null;
        return stats.avgSentimentScore > 0 ? (
            <TrendingUp color="success" />
        ) : (
            <TrendingDown color="error" />
        );
    };

    return (
        <Card sx={{ height: '100%' }}>
            <CardActionArea onClick={onClick} sx={{ height: '100%' }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                        <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                            <School />
                        </Avatar>
                        <Box>
                            <Typography variant="h6" fontWeight="bold">
                                {academy.name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                코드: {academy.code}
                            </Typography>
                        </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {stats ? (
                        <Grid container spacing={2}>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="textSecondary">
                                    오늘 언급
                                </Typography>
                                <Typography variant="h5">
                                    {stats.totalMentions || 0}
                                </Typography>
                            </Grid>
                            <Grid item xs={6}>
                                <Typography variant="body2" color="textSecondary">
                                    언급된 강사
                                </Typography>
                                <Typography variant="h5">
                                    {stats.totalTeachersMentioned || 0}명
                                </Typography>
                            </Grid>
                            <Grid item xs={12}>
                                <Box display="flex" alignItems="center" gap={1}>
                                    <Typography variant="body2" color="textSecondary">
                                        평균 감성:
                                    </Typography>
                                    {getSentimentIcon()}
                                    <Typography
                                        color={stats.avgSentimentScore > 0 ? 'success.main' : 'error.main'}
                                    >
                                        {stats.avgSentimentScore ?
                                            `${(stats.avgSentimentScore * 100).toFixed(0)}%` :
                                            '-'
                                        }
                                    </Typography>
                                </Box>
                            </Grid>
                            {stats.topTeacherName && (
                                <Grid item xs={12}>
                                    <Chip
                                        size="small"
                                        icon={<ThumbUp />}
                                        label={`TOP: ${stats.topTeacherName}`}
                                        color="primary"
                                        variant="outlined"
                                    />
                                </Grid>
                            )}
                        </Grid>
                    ) : (
                        <Typography color="textSecondary" align="center">
                            통계 데이터 없음
                        </Typography>
                    )}
                </CardContent>
            </CardActionArea>
        </Card>
    );
};

// 학원 상세 테이블
const AcademyTeachersTable = ({ teachers, loading }) => {
    if (loading) {
        return <CircularProgress />;
    }

    if (!teachers || teachers.length === 0) {
        return (
            <Typography color="textSecondary" align="center" py={3}>
                강사 데이터가 없습니다.
            </Typography>
        );
    }

    return (
        <TableContainer>
            <Table size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>강사명</TableCell>
                        <TableCell>과목</TableCell>
                        <TableCell align="right">언급</TableCell>
                        <TableCell align="right">긍정</TableCell>
                        <TableCell align="right">부정</TableCell>
                        <TableCell align="right">추천</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {teachers.map((teacher) => (
                        <TableRow key={teacher.id} hover>
                            <TableCell>{teacher.name}</TableCell>
                            <TableCell>{teacher.subjectName}</TableCell>
                            <TableCell align="right">{teacher.mentionCount || 0}</TableCell>
                            <TableCell align="right">{teacher.positiveCount || 0}</TableCell>
                            <TableCell align="right">{teacher.negativeCount || 0}</TableCell>
                            <TableCell align="right">{teacher.recommendationCount || 0}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

function AcademyList() {
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [academies, setAcademies] = useState([]);
    const [academyStats, setAcademyStats] = useState({});
    const [selectedAcademy, setSelectedAcademy] = useState(null);
    const [academyTeachers, setAcademyTeachers] = useState([]);
    const [teachersLoading, setTeachersLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        setError(null);

        try {
            const [academiesRes, statsRes] = await Promise.all([
                academyApi.getAll(),
                dashboardApi.getAcademyRanking()
            ]);

            setAcademies(academiesRes.data || []);

            // 학원 ID별 통계 매핑
            const statsMap = {};
            (statsRes.data || []).forEach(stat => {
                statsMap[stat.academyId] = stat;
            });
            setAcademyStats(statsMap);

        } catch (err) {
            console.error('Failed to fetch academies:', err);
            setError('학원 정보를 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleAcademyClick = async (academy) => {
        if (selectedAcademy?.id === academy.id) {
            setSelectedAcademy(null);
            return;
        }

        setSelectedAcademy(academy);
        setTeachersLoading(true);

        try {
            const response = await academyApi.getTeachers(academy.id);
            setAcademyTeachers(response.data || []);
        } catch (err) {
            console.error('Failed to fetch academy teachers:', err);
        } finally {
            setTeachersLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ py: 3 }}>
            {/* 헤더 */}
            <Box mb={4}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    학원별 통계
                </Typography>
                <Typography variant="subtitle1" color="textSecondary">
                    공무원 학원 {academies.length}개
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            {loading ? (
                <Box display="flex" justifyContent="center" py={5}>
                    <CircularProgress />
                </Box>
            ) : (
                <>
                    {/* 학원 카드 */}
                    <Grid container spacing={3} mb={4}>
                        {academies.map((academy) => (
                            <Grid item xs={12} sm={6} md={3} key={academy.id}>
                                <AcademyCard
                                    academy={academy}
                                    stats={academyStats[academy.id]}
                                    onClick={() => handleAcademyClick(academy)}
                                />
                            </Grid>
                        ))}
                    </Grid>

                    {/* 선택된 학원의 강사 목록 */}
                    {selectedAcademy && (
                        <Paper sx={{ p: 3 }}>
                            <Typography variant="h6" gutterBottom>
                                {selectedAcademy.name} 강사 현황
                            </Typography>
                            <Divider sx={{ mb: 2 }} />
                            <AcademyTeachersTable
                                teachers={academyTeachers}
                                loading={teachersLoading}
                            />
                        </Paper>
                    )}
                </>
            )}
        </Container>
    );
}

export default AcademyList;
