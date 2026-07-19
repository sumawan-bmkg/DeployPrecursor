import React from 'react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import { SectionHeader, KPICard } from '../components/Shared';
import MemoryIcon from '@mui/icons-material/Memory';

interface Props { data?: any }
export default function Runtime({ data }: Props) {
  const stages = ['Reader','Validation','PC3','Tensor','Inference','PredictionValidator','Evidence','Fusion','Alert','Archive','Database'];
  return (
    <Box>
      <SectionHeader title="Runtime" subtitle="RuntimeKernel stage monitoring" />
      <Grid container spacing={1}>
        {stages.map(s => (
          <Grid item xs={6} sm={4} md={3} key={s}>
            <Card><CardContent sx={{ p: 1.5, '&:last-child':{pb:1.5} }}>
              <Typography variant="subtitle1" sx={{ color: '#4fc3f7', fontSize: '0.7rem', mb: 0.5 }}>{s}</Typography>
              <Typography variant="caption" sx={{ color: '#64748b' }}>Standby</Typography>
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
