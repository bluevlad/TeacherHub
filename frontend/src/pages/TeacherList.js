/**
 * Teacher List Page
 * 강사 목록 페이지
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    Container, Grid, Paper, Typography, Box, Card, CardContent, CardActionArea,
    TextField, InputAdornment, Select, MenuItem, FormControl, InputLabel,
    Chip, CircularProgress, Alert, Avatar, Pagination
} from '@mui/material';
import { Search, School, TrendingUp, TrendingDown } from '@mui/icons-material';
import { teacherApi, academyApi } from '../api';

// 강사 카드 컴포넌트
const TeacherCard = ({ teacher, onClick }) => {
    const getSentimentColor = () => {
        if (!teacher.avgSentimentScore) return 'grey';
        if (teacher.avgSentimentScore > 0.2) return 'success.main';
        if (teacher.avgSentimentScore < -0.2) return 'error.main';
        return 'warning.main';
    };

    return (
        <Card sx={{ height: '100%' }}>
            <CardActionArea onClick={onClick} sx={{ height: '100%' }}>
                <CardContent>
                    <Box display="flex" alignItems="center" gap={2}>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                            {teacher.name?.[0]}
                        </Avatar>
                        <Box flex={1}>
                            <Typography variant="h6" component="div">
                                {teacher.name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                {teacher.academyName} · {teacher.subjectName}
                            </Typography>
                        </Box>
                    </Box>

                    <Box display="flex" gap={1} mt={2} flexWrap="wrap">
                        {teacher.mentionCount !== undefined && (
                            <Chip
                                size="small"
                                label={`언급 ${teacher.mentionCount}`}
                                variant="outlined"
                            />
                        )}
                        {teacher.recommendationCount > 0 && (
                            <Chip
                                size="small"
                                label={`추천 ${teacher.recommendationCount}`}
                                color="primary"
                                variant="outlined"
                            />
                        )}
                        {teacher.avgSentimentScore !== undefined && (
                            <Chip
                                size="small"
                                icon={teacher.avgSentimentScore > 0 ? <TrendingUp /> : <TrendingDown />}
                                label={`${(teacher.avgSentimentScore * 100).toFixed(0)}%`}
                                sx={{ color: getSentimentColor() }}
                            />
                        )}
                    </Box>
                </CardContent>
            </CardActionArea>
        </Card>
    );
};

function TeacherList() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [teachers, setTeachers] = useState([]);
    const [academies, setAcademies] = useState([]);
    const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
    const [selectedAcademy, setSelectedAcademy] = useState(searchParams.get('academy') || '');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const ITEMS_PER_PAGE = 12;

    useEffect(() => {
        fetchAcademies();
    }, []);

    useEffect(() => {
        fetchTeachers();
    }, [selectedAcademy, page]);

    const fetchAcademies = async () => {
        try {
            const response = await academyApi.getAll();
            setAcademies(response.data || []);
        } catch (err) {
            console.error('Failed to fetch academies:', err);
        }
    };

    const fetchTeachers = async () => {
        setLoading(true);
        setError(null);

        try {
            const params = {
                page: page - 1,
                size: ITEMS_PER_PAGE
            };

            if (selectedAcademy) {
                params.academyId = selectedAcademy;
            }

            const response = await teacherApi.getAll(params);
            const data = response.data;

            if (Array.isArray(data)) {
                setTeachers(data);
                setTotalPages(Math.ceil(data.length / ITEMS_PER_PAGE) || 1);
            } else if (data.content) {
                setTeachers(data.content);
                setTotalPages(data.totalPages || 1);
            } else {
                setTeachers([]);
            }

        } catch (err) {
            console.error('Failed to fetch teachers:', err);
            setError('강사 목록을 불러오는데 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchTerm.trim()) {
            fetchTeachers();
            return;
        }

        setLoading(true);
        try {
            const response = await teacherApi.search(searchTerm);
            setTeachers(response.data || []);
            setTotalPages(1);
            setSearchParams({ search: searchTerm });
        } catch (err) {
            setError('검색에 실패했습니다.');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    const handleAcademyChange = (e) => {
        setSelectedAcademy(e.target.value);
        setPage(1);
        if (e.target.value) {
            setSearchParams({ academy: e.target.value });
        } else {
            setSearchParams({});
        }
    };

    const handleTeacherClick = (teacherId) => {
        navigate(`/teachers/${teacherId}`);
    };

    const filteredTeachers = teachers.filter(teacher => {
        if (!searchTerm) return true;
        return teacher.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
               teacher.aliases?.some(a => a.toLowerCase().includes(searchTerm.toLowerCase()));
    });

    return (
        <Container maxWidth="lg" sx={{ py: 3 }}>
            {/* 헤더 */}
            <Box mb={4}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    강사 목록
                </Typography>
                <Typography variant="subtitle1" color="textSecondary">
                    공무원 학원 강사 {teachers.length}명
                </Typography>
            </Box>

            {/* 필터 */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={6} md={4}>
                        <TextField
                            fullWidth
                            size="small"
                            placeholder="강사명 검색"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyPress={handleKeyPress}
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <Search />
                                    </InputAdornment>
                                )
                            }}
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                        <FormControl fullWidth size="small">
                            <InputLabel>학원 필터</InputLabel>
                            <Select
                                value={selectedAcademy}
                                label="학원 필터"
                                onChange={handleAcademyChange}
                            >
                                <MenuItem value="">전체</MenuItem>
                                {academies.map((academy) => (
                                    <MenuItem key={academy.id} value={academy.id}>
                                        {academy.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>
                </Grid>
            </Paper>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
            )}

            {/* 강사 목록 */}
            {loading ? (
                <Box display="flex" justifyContent="center" py={5}>
                    <CircularProgress />
                </Box>
            ) : (
                <>
                    <Grid container spacing={2}>
                        {filteredTeachers.map((teacher) => (
                            <Grid item xs={12} sm={6} md={4} lg={3} key={teacher.id}>
                                <TeacherCard
                                    teacher={teacher}
                                    onClick={() => handleTeacherClick(teacher.id)}
                                />
                            </Grid>
                        ))}
                        {filteredTeachers.length === 0 && (
                            <Grid item xs={12}>
                                <Paper sx={{ p: 4, textAlign: 'center' }}>
                                    <Typography color="textSecondary">
                                        검색 결과가 없습니다.
                                    </Typography>
                                </Paper>
                            </Grid>
                        )}
                    </Grid>

                    {/* 페이지네이션 */}
                    {totalPages > 1 && (
                        <Box display="flex" justifyContent="center" mt={4}>
                            <Pagination
                                count={totalPages}
                                page={page}
                                onChange={(e, value) => setPage(value)}
                                color="primary"
                            />
                        </Box>
                    )}
                </>
            )}
        </Container>
    );
}

export default TeacherList;
