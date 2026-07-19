import React from 'react';
import { Box, Card, CardContent } from '@mui/material';
import { SectionHeader } from '../components/Shared';
interface Props { data?: any }
export default function Predictions({ data }: Props) {
  return (
    <Box>
      <SectionHeader title="Predictions" subtitle="Inference results and fusion output" />
      <Card><CardContent sx={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <SectionHeader title="Prediction Table — Coming Soon" />
      </CardContent></Card>
    </Box>
  );
}
