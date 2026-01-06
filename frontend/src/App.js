import React from 'react';
import ReputationList from './components/ReputationList';
import ReputationStats from './components/ReputationStats';
import { Container, Typography, Box } from '@mui/material';

function App() {
    const TARGET_KEYWORD = "윌비스";

    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                    TeacherHub Dashboard
                </Typography>
                <Typography variant="subtitle1" gutterBottom color="text.secondary">
                    Real-time Sentiment Analysis Monitoring
                </Typography>

                <Box sx={{ mt: 4, mb: 4 }}>
                    <ReputationStats keyword={TARGET_KEYWORD} />
                </Box>

                <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
                    Recent Activities
                </Typography>
                <ReputationList />
            </Box>
        </Container>
    );
}

export default App;
