import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import MainLayout from './layouts/MainLayout';
import { Dashboard, TeacherList, TeacherDetail, AcademyList, Reports, WeeklyReports } from './pages';

// 테마 설정
const theme = createTheme({
    palette: {
        primary: {
            main: '#1976d2',
            light: '#e3f2fd',
        },
        secondary: {
            main: '#9c27b0',
        },
        success: {
            main: '#2e7d32',
        },
        error: {
            main: '#d32f2f',
        },
        background: {
            default: '#f5f5f5',
        },
    },
    typography: {
        fontFamily: [
            '-apple-system',
            'BlinkMacSystemFont',
            '"Segoe UI"',
            'Roboto',
            '"Helvetica Neue"',
            'Arial',
            'sans-serif',
        ].join(','),
    },
    components: {
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                },
            },
        },
    },
});

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<MainLayout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="teachers" element={<TeacherList />} />
                        <Route path="teachers/:id" element={<TeacherDetail />} />
                        <Route path="academies" element={<AcademyList />} />
                        <Route path="reports" element={<Reports />} />
                        <Route path="weekly" element={<WeeklyReports />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </ThemeProvider>
    );
}

export default App;
