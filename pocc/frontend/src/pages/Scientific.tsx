import React from 'react';
import { Box, Grid, Card, CardContent } from '@mui/material';
import { SectionHeader, Gauge } from '../components/Shared';
interface Props { data?: any }
export default function Scientific({ data }: Props) {
  const s = data?.scientific || {};
  return (
    <Box>
      <SectionHeader title="Scientific" subtitle="Scientific stability and traceability" />
      <Grid container spacing={2}>
        {['Acceptance', 'Equivalence', 'Reproducibility', 'Operational'].map((l, i) => (
          <Grid item xs={3} key={l}>
            <Card><CardContent>
              <Gauge value={[100,85,90,95][i]} label={l} />
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
