import React from 'react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import MemoryIcon from '@mui/icons-material/Memory';
import AutoGraphIcon from '@mui/icons-material/AutoGraph';
import ScienceIcon from '@mui/icons-material/Science';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { KPICard, StatusBadge, Gauge, SectionHeader } from '../components/Shared';

interface Props { data?: any }

const NODES = [
  { label: 'Remote Server', status: 'NORMAL', time: '0.12s' },
  { label: 'Collector', status: 'STANDBY', time: '0.96s' },
  { label: 'Raw Repository', status: 'NORMAL', files: '400k+' },
  { label: 'Validation', status: 'NORMAL', time: '28.7s' },
  { label: 'PC3', status: 'NORMAL', time: '0.1s' },
  { label: 'Tensor', status: 'NORMAL', time: '3.7s' },
  { label: 'Inference', status: 'NORMAL', time: '0.0s' },
  { label: 'Fusion', status: 'NORMAL', time: '0.0s' },
  { label: 'Alert', status: 'STANDBY' },
  { label: 'Archive', status: 'NORMAL' },
  { label: 'Database', status: 'NORMAL' },
];

export default function MissionControl({ data }: Props) {
  const b = data?.burnin || {};
  const c = data?.collector || {};
  const r = data?.runtime || {};
  const s = data?.scientific || {};
  const rl = data?.release || {};

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h1" sx={{ color: '#4fc3f7' }}>
          PIMES Operational Command Center
        </Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          Physics-Informed Multi-station Earthquake System — Release Candidate 1
        </Typography>
      </Box>

      {/* Top KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard title="Overall Health" icon={<DashboardIcon />} color="#00e676"
            value={<StatusBadge status="NORMAL" />} subtitle="All systems nominal" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard title="Collector Status" icon={<CloudDownloadIcon />} color="#4fc3f7"
            value={`${c.stations_total || 0} stations`} subtitle={`${c.total_files?.toLocaleString() || 0} files`} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard title="Burn-in" icon={<AutoGraphIcon />} color={b.status === 'RUNNING' ? '#00e676' : '#ffb74d'}
            value={`${b.cycles || 0}/${b.max_cycles || 24}`} subtitle={b.status || 'IDLE'} />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard title="Release Status" icon={<ScienceIcon />} color={rl.erb_verdict === 'PASS' ? '#00e676' : '#ffb74d'}
            value={rl.rc_status || 'RC1 Candidate'} subtitle={`ERB: ${rl.erb_score || 0}%`} />
        </Grid>
      </Grid>

      {/* Pipeline Flow Visualization */}
      <SectionHeader title="Pipeline Status" subtitle="End-to-end operational chain" />
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{
            display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center',
            justifyContent: 'center', py: 2,
          }}>
            {NODES.map((node, i) => (
              <React.Fragment key={node.label}>
                <Box sx={{
                  textAlign: 'center', px: 1.5, py: 1, borderRadius: 2,
                  bgcolor: '#1b2838', border: '1px solid #2a3a4a', minWidth: 80,
                }}>
                  <Typography variant="caption" sx={{ color: '#94a3b8', display: 'block', fontSize: '0.65rem' }}>
                    {node.label}
                  </Typography>
                  <StatusBadge status={node.status} />
                  {node.time && <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.6rem', display: 'block' }}>
                    {node.time}
                  </Typography>}
                  {node.files && <Typography variant="caption" sx={{ color: '#64748b', fontSize: '0.6rem', display: 'block' }}>
                    {node.files}
                  </Typography>}
                </Box>
                {i < NODES.length - 1 && (
                  <Typography variant="caption" sx={{ color: '#2a3a4a', fontSize: '1.2rem' }}>→</Typography>
                )}
              </React.Fragment>
            ))}
          </Box>
        </CardContent>
      </Card>

      {/* Bottom Row: Scientific + Release */}
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <SectionHeader title="Scientific Stability" />
              <Grid container spacing={2}>
                <Grid item xs={4}><Gauge value={s.acceptance_score || 100} label="Acceptance" /></Grid>
                <Grid item xs={4}><Gauge value={s.equivalence_score || 85} label="Equivalence" /></Grid>
                <Grid item xs={4}><Gauge value={s.stability_index || 95} label="Stability" /></Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <SectionHeader title="Latest Prediction" />
              <Box sx={{ display: 'flex', justifyContent: 'space-around', py: 2 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" sx={{ color: '#94a3b8' }}>--</Typography>
                  <Typography variant="body2">Probability</Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" sx={{ color: '#94a3b8' }}>--</Typography>
                  <Typography variant="body2">Azimuth</Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" sx={{ color: '#94a3b8' }}>--</Typography>
                  <Typography variant="body2">Stations</Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <StatusBadge status="NORMAL" label="NO ALERT" />
                  <Typography variant="body2">Alert</Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
