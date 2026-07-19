import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Table, TableBody, TableCell, TableRow } from '@mui/material';
import { SectionHeader, StatusBadge } from '../components/Shared';
interface Props { data?: any }
export default function BurnIn({ data }: Props) {
  const b = data?.burnin || {};
  const csv = data?.csv_tail || [];
  return (
    <Box>
      <SectionHeader title="Burn-in" subtitle="Operational stress test" />
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Card><CardContent>
            <Typography variant="h3">{b.status || 'IDLE'}</Typography>
            <Typography variant="body2">Status</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={4}>
          <Card><CardContent>
            <Typography variant="h3">{b.cycles || 0}/{b.max_cycles || 24}</Typography>
            <Typography variant="body2">Cycles</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={4}>
          <Card><CardContent>
            <Typography variant="h3">{csv.length}</Typography>
            <Typography variant="body2">Records</Typography>
          </CardContent></Card>
        </Grid>
        {csv.length > 0 && (
          <Grid item xs={12}>
            <Card><CardContent>
              <SectionHeader title="Latest Cycles" />
              <Table size="small">
                <TableBody>
                  {csv.slice(0, 5).map((r: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell>{r.cycle}</TableCell>
                      <TableCell>{r.timestamp?.slice(11,19)}</TableCell>
                      <TableCell>{r.total_s}s</TableCell>
                      <TableCell><StatusBadge status={r.fusion_decision === 'True' ? 'PASS' : 'STANDBY'} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent></Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}
