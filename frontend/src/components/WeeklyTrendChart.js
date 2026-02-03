/**
 * Weekly Trend Chart Component
 * 주간 트렌드 차트
 */
import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Chart.js 등록
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

/**
 * 주간 언급 트렌드 차트
 */
export const MentionTrendChart = ({ data, title = "주간 언급 트렌드" }) => {
    if (!data || data.length === 0) {
        return (
            <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="textSecondary">트렌드 데이터가 없습니다.</Typography>
            </Paper>
        );
    }

    const chartData = {
        labels: data.map(d => d.week_label || `W${d.week_number}`),
        datasets: [
            {
                label: '언급 수',
                data: data.map(d => d.mention_count),
                borderColor: 'rgb(25, 118, 210)',
                backgroundColor: 'rgba(25, 118, 210, 0.1)',
                fill: true,
                tension: 0.4
            },
            {
                label: '추천',
                data: data.map(d => d.recommendation_count),
                borderColor: 'rgb(76, 175, 80)',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                fill: false,
                tension: 0.4
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: title
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };

    return (
        <Box sx={{ height: 300 }}>
            <Line data={chartData} options={options} />
        </Box>
    );
};

/**
 * 감성 트렌드 차트
 */
export const SentimentTrendChart = ({ data, title = "주간 감성 트렌드" }) => {
    if (!data || data.length === 0) {
        return (
            <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="textSecondary">감성 데이터가 없습니다.</Typography>
            </Paper>
        );
    }

    const chartData = {
        labels: data.map(d => d.week_label || `W${d.week_number}`),
        datasets: [
            {
                label: '긍정',
                data: data.map(d => d.positive_count),
                backgroundColor: 'rgba(76, 175, 80, 0.8)',
            },
            {
                label: '중립',
                data: data.map(d => d.neutral_count || 0),
                backgroundColor: 'rgba(158, 158, 158, 0.8)',
            },
            {
                label: '부정',
                data: data.map(d => d.negative_count),
                backgroundColor: 'rgba(244, 67, 54, 0.8)',
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: title
            }
        },
        scales: {
            x: {
                stacked: true
            },
            y: {
                stacked: true,
                beginAtZero: true
            }
        }
    };

    return (
        <Box sx={{ height: 300 }}>
            <Bar data={chartData} options={options} />
        </Box>
    );
};

/**
 * 순위 변화 차트
 */
export const RankTrendChart = ({ data, title = "주간 순위 변화" }) => {
    if (!data || data.length === 0) {
        return (
            <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography color="textSecondary">순위 데이터가 없습니다.</Typography>
            </Paper>
        );
    }

    const chartData = {
        labels: data.map(d => d.week_label || `W${d.week_number}`),
        datasets: [
            {
                label: '전체 순위',
                data: data.map(d => d.weekly_rank),
                borderColor: 'rgb(156, 39, 176)',
                backgroundColor: 'rgba(156, 39, 176, 0.1)',
                fill: false,
                tension: 0.4
            }
        ]
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: title
            }
        },
        scales: {
            y: {
                reverse: true,  // 순위는 낮을수록 좋으므로 역순
                min: 1,
                ticks: {
                    stepSize: 1
                }
            }
        }
    };

    return (
        <Box sx={{ height: 300 }}>
            <Line data={chartData} options={options} />
        </Box>
    );
};

const WeeklyCharts = { MentionTrendChart, SentimentTrendChart, RankTrendChart };
export default WeeklyCharts;
