import React from 'react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import { SectionHeader, StatusBadge } from '../components/Shared';

interface Props { data?: any }
export default function DataAcquisition({ data }: Props) {
  return (
    <Box>
      <SectionHeader title="Data Acquisition" subtitle="Remote data server, collector, and repository status" />
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <SectionHeader title="Remote Server" />
            <Typography>Server: 202.90.198.224:4343</Typography>
            <Typography>Protocol: SSH/SFTP</Typography>
            <Typography>Latency: 0.12s</Typography>
            <Typography>Root: /home/precursor/SEISMO/DATA</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <SectionHeader title="Collector" />
            <StatusBadge status={data?.collector?.status || 'STANDBY'} />
            <Typography>Stations: {data?.collector?.stations_total || 0}</Typography>
            <Typography>Files: {(data?.collector?.total_files || 0).toLocaleString()}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12}>
          <Card><CardContent>
            <SectionHeader title="RDMC Summary" />
            <Typography variant="body2">RDMC v2.1 complete — 22 stations classified, ~400k files</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>
    </Box>
  );
}
