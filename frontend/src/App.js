import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import MainLayout from './layouts/MainLayout';
import { Dashboard, TeacherList, TeacherDetail, AcademyList, Reports, WeeklyReports } from './pages';

const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#1976d2',
        },
        secondary: {
            main: '#9c27b0',
        },
    },
});

function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <BrowserRouter>
                <Routes>
                    <Route element={<MainLayout />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/teachers" element={<TeacherList />} />
                        <Route path="/teachers/:id" element={<TeacherDetail />} />
                        <Route path="/academies" element={<AcademyList />} />
                        <Route path="/reports" element={<Reports />} />
                        <Route path="/weekly" element={<WeeklyReports />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </ThemeProvider>
    );
}

export default App;
