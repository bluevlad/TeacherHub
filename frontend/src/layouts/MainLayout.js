/**
 * Main Layout Component
 * 공통 레이아웃 (네비게이션 바 포함)
 */
import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
    AppBar, Box, Toolbar, Typography, Button, IconButton, Drawer,
    List, ListItem, ListItemIcon, ListItemText, ListItemButton,
    useTheme, useMediaQuery, Divider
} from '@mui/material';
import {
    Menu as MenuIcon, Dashboard, People, School, Assessment,
    Settings, ChevronLeft
} from '@mui/icons-material';

const DRAWER_WIDTH = 240;

const menuItems = [
    { text: '대시보드', icon: <Dashboard />, path: '/' },
    { text: '강사 목록', icon: <People />, path: '/teachers' },
    { text: '학원별 통계', icon: <School />, path: '/academies' },
    { text: '리포트', icon: <Assessment />, path: '/reports' },
];

function MainLayout() {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const navigate = useNavigate();
    const location = useLocation();

    const [drawerOpen, setDrawerOpen] = useState(!isMobile);

    const handleDrawerToggle = () => {
        setDrawerOpen(!drawerOpen);
    };

    const handleNavigation = (path) => {
        navigate(path);
        if (isMobile) {
            setDrawerOpen(false);
        }
    };

    const isActive = (path) => {
        if (path === '/') {
            return location.pathname === '/';
        }
        return location.pathname.startsWith(path);
    };

    const drawer = (
        <Box>
            <Toolbar>
                <Typography variant="h6" noWrap component="div" fontWeight="bold">
                    TeacherHub
                </Typography>
                {isMobile && (
                    <IconButton onClick={handleDrawerToggle} sx={{ ml: 'auto' }}>
                        <ChevronLeft />
                    </IconButton>
                )}
            </Toolbar>
            <Divider />
            <List>
                {menuItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            onClick={() => handleNavigation(item.path)}
                            selected={isActive(item.path)}
                            sx={{
                                '&.Mui-selected': {
                                    backgroundColor: 'primary.light',
                                    '&:hover': {
                                        backgroundColor: 'primary.light',
                                    },
                                },
                            }}
                        >
                            <ListItemIcon
                                sx={{
                                    color: isActive(item.path) ? 'primary.main' : 'inherit'
                                }}
                            >
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
            <Divider />
            <List>
                <ListItem disablePadding>
                    <ListItemButton onClick={() => handleNavigation('/settings')}>
                        <ListItemIcon>
                            <Settings />
                        </ListItemIcon>
                        <ListItemText primary="설정" />
                    </ListItemButton>
                </ListItem>
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex' }}>
            {/* 앱바 */}
            <AppBar
                position="fixed"
                sx={{
                    width: { md: `calc(100% - ${drawerOpen ? DRAWER_WIDTH : 0}px)` },
                    ml: { md: `${drawerOpen ? DRAWER_WIDTH : 0}px` },
                    transition: theme.transitions.create(['margin', 'width'], {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2 }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
                        {menuItems.find(item => isActive(item.path))?.text || 'TeacherHub'}
                    </Typography>
                    <Typography variant="body2" color="inherit">
                        공무원 학원 강사 평판 분석
                    </Typography>
                </Toolbar>
            </AppBar>

            {/* 사이드바 */}
            <Drawer
                variant={isMobile ? 'temporary' : 'persistent'}
                open={drawerOpen}
                onClose={handleDrawerToggle}
                sx={{
                    width: DRAWER_WIDTH,
                    flexShrink: 0,
                    '& .MuiDrawer-paper': {
                        width: DRAWER_WIDTH,
                        boxSizing: 'border-box',
                    },
                }}
            >
                {drawer}
            </Drawer>

            {/* 메인 컨텐츠 */}
            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 0,
                    width: { md: `calc(100% - ${drawerOpen ? DRAWER_WIDTH : 0}px)` },
                    ml: { md: drawerOpen ? 0 : `-${DRAWER_WIDTH}px` },
                    transition: theme.transitions.create(['margin', 'width'], {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
                }}
            >
                <Toolbar /> {/* 앱바 높이만큼 여백 */}
                <Outlet />
            </Box>
        </Box>
    );
}

export default MainLayout;
