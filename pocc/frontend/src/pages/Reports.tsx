import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Button, Table, TableBody, TableCell, TableRow } from '@mui/material';
import { SectionHeader } from '../components/Shared';
interface Props { data?: any }
export default function Reports({ data }: Props) {
  const reports = [
    'Acceptance Report', 'Scientific Equivalence', 'Reproducibility Report',
    'Operational Report', 'Burn-in Report', 'PDAC Certificate',
    'RDMC Report', 'ERB Executive Report',
  ].map(r => ({ name: r, generated: '2026-07-15', format: 'JSON+MD' }));
  return (
    <Box>
      <SectionHeader title="Report Center" subtitle="All certification, burn-in, and operational reports" />
      <Card>
        <CardContent>
          <Table size="small">
            <TableBody>
              {reports.map((r, i) => (
                <TableRow key={i}>
                  <TableCell>{r.name}</TableCell>
                  <TableCell>{r.generated}</TableCell>
                  <TableCell>{r.format}</TableCell>
                  <TableCell><Button size="small" variant="outlined" sx={{ color: '#4fc3f7', borderColor: '#4fc3f7' }}>Download</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  );
}
