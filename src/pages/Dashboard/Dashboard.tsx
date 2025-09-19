import React, { ReactNode } from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { Article, Cached, CheckCircle } from '@mui/icons-material';

// Define an interface for the component's props
interface StatCardProps {
    title: string;
    value: string;
    icon: ReactNode;
    color: string;
}

const StatCard = ({ title, value, icon, color }: StatCardProps) => (
    <Card sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
        <Box sx={{ color: color, fontSize: 40, mr: 2 }}>{icon}</Box>
        <Box>
            <Typography color="text.secondary" gutterBottom>
                {title}
            </Typography>
            <Typography variant="h5" component="div">
                {value}
            </Typography>
        </Box>
    </Card>
);

const Dashboard = () => {
    return (
        <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" gutterBottom>
                Dashboard Overview
            </Typography>
            <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Total Documents"
                        value="1,204"
                        icon={<Article fontSize="inherit" />}
                        color="primary.main"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Processing"
                        value="15"
                        icon={<Cached fontSize="inherit" />}
                        color="warning.main"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Completed"
                        value="1,189"
                        icon={<CheckCircle fontSize="inherit" />}
                        color="success.main"
                    />
                </Grid>
            </Grid>
        </Box>
    );
};

export default Dashboard;