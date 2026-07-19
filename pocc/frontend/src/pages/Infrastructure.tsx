import React from 'react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import { SectionHeader } from '../components/Shared';
interface Props { data?: any }
export default function Infrastructure({ data }: Props) {
  return (
    <Box>
      <SectionHeader title="Infrastructure" subtitle="System resources and health" />
      <Grid container spacing={2}>
        {['CPU','RAM','Disk','Network'].map(m => (
          <Grid item xs={3} key={m}>
            <Card><CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" sx={{ color: '#94a3b8' }}>--</Typography>
              <Typography variant="body2">{m}</Typography>
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
