import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';
import { SectionHeader } from '../components/Shared';
interface Props { data?: any }
export default function StationMap({ data }: Props) {
  return (
    <Box>
      <SectionHeader title="Station Map" subtitle="BMKG station monitoring" />
      <Card sx={{ height: 600, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#0a0e1a' }}>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          Interactive station map (Leaflet) — requires map tiles & coordinates
        </Typography>
      </Card>
    </Box>
  );
}
