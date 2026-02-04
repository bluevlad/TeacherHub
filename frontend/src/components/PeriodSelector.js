/**
 * PeriodSelector Component
 * 기간 선택 컴포넌트 (일별/주별/월별)
 */
import React, { useState, useEffect } from 'react';
import {
    Box, Tabs, Tab, Select, MenuItem, FormControl, InputLabel,
    Typography, Chip, Paper
} from '@mui/material';
import {
    CalendarToday, DateRange, CalendarMonth
} from '@mui/icons-material';
import { reportApi } from '../api';

function PeriodSelector({ onPeriodChange, initialPeriodType = 'daily' }) {
    const [periodType, setPeriodType] = useState(initialPeriodType);
    const [periods, setPeriods] = useState(null);
    const [selectedDaily, setSelectedDaily] = useState('');
    const [selectedWeekly, setSelectedWeekly] = useState('');
    const [selectedMonthly, setSelectedMonthly] = useState('');
    const [loading, setLoading] = useState(true);

    // 기간 목록 로드
    useEffect(() => {
        const fetchPeriods = async () => {
            try {
                const response = await reportApi.getPeriods();
                setPeriods(response.data);

                // 기본값 설정
                if (response.data.daily?.length > 0) {
                    setSelectedDaily(response.data.daily[0].date);
                }
                if (response.data.weekly?.length > 0) {
                    const w = response.data.weekly[0];
                    setSelectedWeekly(`${w.year}-${w.week}`);
                }
                if (response.data.monthly?.length > 0) {
                    const m = response.data.monthly[0];
                    setSelectedMonthly(`${m.year}-${m.month}`);
                }

                setLoading(false);
            } catch (error) {
                console.error('Failed to fetch periods:', error);
                setLoading(false);
            }
        };

        fetchPeriods();
    }, []);

    // 초기 데이터 로드
    useEffect(() => {
        if (!loading && periods) {
            handlePeriodSelect();
        }
    }, [loading, periodType]);

    // 기간 유형 변경
    const handleTabChange = (event, newValue) => {
        setPeriodType(newValue);
    };

    // 기간 선택 핸들러
    const handlePeriodSelect = () => {
        if (!periods) return;

        let params = { periodType };

        switch (periodType) {
            case 'daily':
                if (selectedDaily) {
                    params.date = selectedDaily;
                    const selected = periods.daily?.find(d => d.date === selectedDaily);
                    params.label = selected?.label || selectedDaily;
                }
                break;
            case 'weekly':
                if (selectedWeekly) {
                    const [year, week] = selectedWeekly.split('-').map(Number);
                    params.year = year;
                    params.week = week;
                    const selected = periods.weekly?.find(w => w.year === year && w.week === week);
                    params.label = selected?.label || `${year}년 ${week}주차`;
                }
                break;
            case 'monthly':
                if (selectedMonthly) {
                    const [year, month] = selectedMonthly.split('-').map(Number);
                    params.year = year;
                    params.month = month;
                    const selected = periods.monthly?.find(m => m.year === year && m.month === month);
                    params.label = selected?.label || `${year}년 ${month}월`;
                }
                break;
            default:
                break;
        }

        if (onPeriodChange) {
            onPeriodChange(params);
        }
    };

    // 일별 선택 변경
    const handleDailyChange = (event) => {
        setSelectedDaily(event.target.value);
    };

    // 주별 선택 변경
    const handleWeeklyChange = (event) => {
        setSelectedWeekly(event.target.value);
    };

    // 월별 선택 변경
    const handleMonthlyChange = (event) => {
        setSelectedMonthly(event.target.value);
    };

    // 선택 변경 시 데이터 로드
    useEffect(() => {
        if (!loading) {
            handlePeriodSelect();
        }
    }, [selectedDaily, selectedWeekly, selectedMonthly]);

    if (loading || !periods) {
        return <Box p={2}>로딩 중...</Box>;
    }

    return (
        <Paper sx={{ mb: 3 }}>
            {/* 기간 유형 탭 */}
            <Tabs
                value={periodType}
                onChange={handleTabChange}
                variant="fullWidth"
                sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
                <Tab
                    value="daily"
                    label="일별"
                    icon={<CalendarToday />}
                    iconPosition="start"
                />
                <Tab
                    value="weekly"
                    label="주별"
                    icon={<DateRange />}
                    iconPosition="start"
                />
                <Tab
                    value="monthly"
                    label="월별"
                    icon={<CalendarMonth />}
                    iconPosition="start"
                />
            </Tabs>

            {/* 기간 선택 */}
            <Box sx={{ p: 2 }}>
                {periodType === 'daily' && (
                    <FormControl fullWidth size="small">
                        <InputLabel>날짜 선택</InputLabel>
                        <Select
                            value={selectedDaily}
                            onChange={handleDailyChange}
                            label="날짜 선택"
                        >
                            {periods.daily?.map((d) => (
                                <MenuItem key={d.date} value={d.date}>
                                    {d.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {periodType === 'weekly' && (
                    <FormControl fullWidth size="small">
                        <InputLabel>주차 선택</InputLabel>
                        <Select
                            value={selectedWeekly}
                            onChange={handleWeeklyChange}
                            label="주차 선택"
                        >
                            {periods.weekly?.map((w) => (
                                <MenuItem key={`${w.year}-${w.week}`} value={`${w.year}-${w.week}`}>
                                    {w.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {periodType === 'monthly' && (
                    <FormControl fullWidth size="small">
                        <InputLabel>월 선택</InputLabel>
                        <Select
                            value={selectedMonthly}
                            onChange={handleMonthlyChange}
                            label="월 선택"
                        >
                            {periods.monthly?.map((m) => (
                                <MenuItem key={`${m.year}-${m.month}`} value={`${m.year}-${m.month}`}>
                                    {m.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {/* 현재 선택 정보 */}
                <Box mt={2} display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2" color="textSecondary">
                        현재:
                    </Typography>
                    <Chip
                        size="small"
                        color="primary"
                        label={
                            periodType === 'daily' ? periods.daily?.find(d => d.date === selectedDaily)?.label :
                            periodType === 'weekly' ? periods.weekly?.find(w => `${w.year}-${w.week}` === selectedWeekly)?.label :
                            periods.monthly?.find(m => `${m.year}-${m.month}` === selectedMonthly)?.label
                        }
                    />
                </Box>
            </Box>
        </Paper>
    );
}

export default PeriodSelector;
