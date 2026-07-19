import React from 'react';
import { Box, Grid, Card, CardContent } from '@mui/material';
import { SectionHeader, Gauge, StatusBadge } from '../components/Shared';
interface Props { data?: any }
export default function Release({ data }: Props) {
  const rl = data?.release || {};
  const checks = ['Acceptance','Scientific Equivalence','Reproducibility','Operational','Burn-in','Failure Injection','Shadow Mode','RC1','RC2','Production'];
  return (
    <Box>
      <SectionHeader title="Release" subtitle="Release engineering and certification" />
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Card><CardContent>
            <SectionHeader title="ERB Score" />
            <Gauge value={rl.erb_score || 0} max={100} label={rl.erb_verdict || 'PENDING'} />
          </CardContent></Card>
        </Grid>
        <Grid item xs={8}>
          <Card><CardContent>
            <SectionHeader title="Readiness Checklist" />
            {checks.map(c => (
              <Box key={c} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid #1e293b' }}>
                <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>{c}</span>
                <StatusBadge status={['Acceptance','Operational'].includes(c) ? 'PASS' : 'STANDBY'} />
              </Box>
            ))}
          </CardContent></Card>
        </Grid>
      </Grid>
    </Box>
  );
}
