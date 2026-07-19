import React from 'react';
import { Box, Card, CardContent, Typography, Grid } from '@mui/material';
import { keyframes } from '@emotion/react';

const pulse = keyframes`0%,100%{opacity:1}50%{opacity:0.5}`;

interface Props { data?: any; title?: string; icon?: React.ReactNode; color?: string; value?: React.ReactNode; subtitle?: string; }

export function KPICard({ title, icon, color = '#4fc3f7', value, subtitle }: Props) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle1">{title}</Typography>
          {icon && <Box sx={{ color }}>{icon}</Box>}
        </Box>
        <Typography variant="h3" sx={{ color, fontWeight: 700 }}>
          {value ?? '--'}
        </Typography>
        {subtitle && <Typography variant="body2">{subtitle}</Typography>}
      </CardContent>
    </Card>
  );
}

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const colors: Record<string, string> = {
    NORMAL: '#00e676', STANDBY: '#4fc3f7', WARNING: '#ffb74d', FAILURE: '#ff5252', IDLE: '#94a3b8',
    OFFLINE: '#64748b', PASS: '#00e676', FAIL: '#ff5252',
  };
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Box sx={{
        width: 8, height: 8, borderRadius: '50%',
        bgcolor: colors[status] || '#94a3b8',
        animation: status === 'NORMAL' ? `${pulse} 2s infinite` : 'none',
      }} />
      <Typography variant="caption" sx={{ color: colors[status] || '#94a3b8' }}>
        {label || status}
      </Typography>
    </Box>
  );
}

export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <Box sx={{ mb: 2, pb: 1, borderBottom: '1px solid #1e293b' }}>
      <Typography variant="h2">{title}</Typography>
      {subtitle && <Typography variant="body2">{subtitle}</Typography>}
    </Box>
  );
}

export function Gauge({ value, max = 100, label, color }: { value: number; max?: number; label?: string; color?: string }) {
  const pct = Math.min(value / max, 1);
  const strokeColor = color || (pct > 0.8 ? '#00e676' : pct > 0.5 ? '#ffb74d' : '#ff5252');
  return (
    <Box sx={{ textAlign: 'center', position: 'relative' }}>
      <svg width="100" height="60" viewBox="0 0 100 60">
        <path d="M 10 55 A 40 40 0 1 1 90 55" fill="none" stroke="#1e293b" strokeWidth="8" />
        <path d="M 10 55 A 40 40 0 1 1 90 55" fill="none" stroke={strokeColor} strokeWidth="8"
          strokeDasharray={`${pct * 125.6} 125.6`} strokeLinecap="round" />
      </svg>
      <Typography variant="h4" sx={{ position: 'absolute', top: '20px', left: 0, right: 0, color: strokeColor, fontWeight: 700 }}>
        {value.toFixed(0)}%
      </Typography>
      {label && <Typography variant="body2" sx={{ mt: 1 }}>{label}</Typography>}
    </Box>
  );
}
