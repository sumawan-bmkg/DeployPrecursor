import React from 'react';
import { Box, Typography, Chip } from '@mui/material';

interface Props { data?: any }

export default function Header({ data }: Props) {
  return (
    <Box sx={{
      position: 'fixed', top: 0, right: 0, left: 260, zIndex: 1100,
      height: 64, bgcolor: '#0f1629', borderBottom: '1px solid #1e293b',
      display: 'flex', alignItems: 'center', px: 3, gap: 2,
    }}>
      <Typography variant="h6" sx={{ color: '#e0e6ed', fontWeight: 600, fontSize: '1rem' }}>
        Mission Control
      </Typography>
      <Box sx={{ flexGrow: 1 }} />
      <Chip label={`UTC: ${data?.utc?.slice(11,19) || '--'}`} size="small" sx={{ color: '#94a3b8', bgcolor: '#1b2838' }} />
      <Chip label={`WITA: ${data?.wita?.slice(11,19) || '--'}`} size="small" sx={{ color: '#94a3b8', bgcolor: '#1b2838' }} />
      <Chip
        label={data?.health || 'NORMAL'}
        size="small"
        sx={{ color: '#00e676', bgcolor: '#0a2e1a', border: '1px solid #00e676' }}
      />
    </Box>
  );
}
