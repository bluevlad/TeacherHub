import React from 'react';
import ReputationList from './components/ReputationList';
import { Container, Typography, Box } from '@mui/material';

function App() {
    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    TeacherHub Dashboard
                </Typography>
                <Typography variant="subtitle1" gutterBottom color="text.secondary">
                    Real-time Sentiment Analysis Monitoring (Target: 한덕현)
                </Typography>

                <ReputationList />
            </Box>
        </Container>
    );
}

export default App;
