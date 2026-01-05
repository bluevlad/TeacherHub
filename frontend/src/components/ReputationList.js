import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip
} from '@mui/material';

// Use environment variable or fallback
const API_URL = process.env.REACT_APP_API_URL || "http://teacherhub.unmong.com:8081";

function ReputationList() {
    const [data, setData] = useState([]);

    useEffect(() => {
        fetchData();
        // Poll every 10 seconds for real-time update
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/reputation`);
            setData(response.data);
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    };

    const getSentimentColor = (sentiment) => {
        if (sentiment === 'POSITIVE') return 'success';
        if (sentiment === 'NEGATIVE') return 'error';
        return 'default';
    };

    return (
        <TableContainer component={Paper} sx={{ mt: 3 }}>
            <Table aria-label="reputation table">
                <TableHead>
                    <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Keyword</TableCell>
                        <TableCell>Site</TableCell>
                        <TableCell>Title</TableCell>
                        <TableCell>Sentiment</TableCell>
                        <TableCell>Score</TableCell>
                        <TableCell>Date</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {data.map((row) => (
                        <TableRow key={row.id}>
                            <TableCell>{row.id}</TableCell>
                            <TableCell>{row.keyword}</TableCell>
                            <TableCell>{row.siteName}</TableCell>
                            <TableCell>
                                <a href={row.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: 'inherit' }}>
                                    {row.title.length > 30 ? row.title.substring(0, 30) + '...' : row.title}
                                </a>
                            </TableCell>
                            <TableCell>
                                <Chip label={row.sentiment} color={getSentimentColor(row.sentiment)} size="small" />
                            </TableCell>
                            <TableCell>{row.score}</TableCell>
                            <TableCell>{new Date(row.createdAt).toLocaleString()}</TableCell>
                        </TableRow>
                    ))}
                    {data.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={7} align="center">No data collected yet.</TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </TableContainer>
    );
}

export default ReputationList;
