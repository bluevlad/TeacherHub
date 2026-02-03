import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Box, Card, CardContent, Typography, Grid, Paper, CircularProgress
} from '@mui/material';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

const API_URL = process.env.REACT_APP_API_URL || "http://teacherhub.unmong.com:8081";

function ReputationStats({ keyword }) {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 10000);
        return () => clearInterval(interval);
    }, [keyword]);

    const fetchStats = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/reputation/stats?keyword=${keyword}`);
            setStats(response.data);
            setLoading(false);
        } catch (error) {
            console.error("Error fetching stats:", error);
            setLoading(false);
        }
    };

    if (loading) return <CircularProgress />;
    if (!stats) return <Typography>No statistics available.</Typography>;

    // Prepare Chart Data
    const monthlyData = {
        labels: stats.monthlyStats.map(m => m.month),
        datasets: [
            {
                label: 'Number of Posts',
                data: stats.monthlyStats.map(m => m.postCount),
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Monthly Post Trend (Last 1 Year)' },
        },
    };

    return (
        <Box sx={{ flexGrow: 1, mb: 4 }}>
            <Grid container spacing={3}>
                {/* Summary Cards */}
                <Grid item xs={12} md={4}>
                    <Card sx={{ bgcolor: '#e3f2fd' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Current Keyword
                            </Typography>
                            <Typography variant="h5" component="div">
                                {stats.keyword}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Card sx={{ bgcolor: '#ede7f6' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Total Posts (Collected)
                            </Typography>
                            <Typography variant="h4" component="div">
                                {stats.totalPosts}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} md={4}>
                    <Card sx={{ bgcolor: '#e0f2f1' }}>
                        <CardContent>
                            <Typography color="text.secondary" gutterBottom>
                                Total Comments
                            </Typography>
                            <Typography variant="h4" component="div">
                                {stats.totalComments}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Chart */}
                <Grid item xs={12}>
                    <Paper sx={{ p: 2 }}>
                        {stats.monthlyStats.length > 0 ? (
                            <Bar options={chartOptions} data={monthlyData} height={100} />
                        ) : (
                            <Box p={3} textAlign="center">
                                <Typography>Not enough data for chart yet.</Typography>
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
}

export default ReputationStats;
