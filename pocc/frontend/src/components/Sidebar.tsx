import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Typography, Divider } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SatelliteAltIcon from '@mui/icons-material/SatelliteAlt';
import MapIcon from '@mui/icons-material/Map';
import ScienceIcon from '@mui/icons-material/Science';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import TimelineIcon from '@mui/icons-material/Timeline';
import MemoryIcon from '@mui/icons-material/Memory';
import DnsIcon from '@mui/icons-material/Dns';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import AssessmentIcon from '@mui/icons-material/Assessment';

const DRAWER_WIDTH = 260;
const NAV_ITEMS = [
  { label: 'Mission Control', icon: <DashboardIcon />, path: '/' },
  { label: 'Data Acquisition', icon: <SatelliteAltIcon />, path: '/acquisition' },
  { label: 'Station Map', icon: <MapIcon />, path: '/stations' },
  { label: 'Scientific', icon: <ScienceIcon />, path: '/scientific' },
  { label: 'Burn-in', icon: <LocalFireDepartmentIcon />, path: '/burnin' },
  { label: 'Predictions', icon: <TimelineIcon />, path: '/predictions' },
  { label: 'Runtime', icon: <MemoryIcon />, path: '/runtime' },
  { label: 'Infrastructure', icon: <DnsIcon />, path: '/infrastructure' },
  { label: 'Release', icon: <RocketLaunchIcon />, path: '/release' },
  { label: 'Reports', icon: <AssessmentIcon />, path: '/reports' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          bgcolor: '#0f1629',
          borderRight: '1px solid #1e293b',
        },
      }}
    >
      <Box sx={{ p: 2.5, textAlign: 'center', borderBottom: '1px solid #1e293b' }}>
        <Typography variant="h6" sx={{ color: '#4fc3f7', fontWeight: 700, letterSpacing: '0.05em' }}>
          PIMES
        </Typography>
        <Typography variant="caption" sx={{ color: '#64748b', display: 'block', mt: 0.5 }}>
          Operational Command Center
        </Typography>
        <Box sx={{
          display: 'inline-block', mt: 1, px: 1.5, py: 0.25,
          bgcolor: '#1b2838', borderRadius: 1, border: '1px solid #2a3a4a',
        }}>
          <Typography variant="caption" sx={{ color: '#ffb74d', fontSize: '0.7rem' }}>
            RC1 Candidate
          </Typography>
        </Box>
      </Box>
      <List sx={{ px: 1, pt: 1 }}>
        {NAV_ITEMS.map((item) => (
          <ListItemButton
            key={item.path}
            selected={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              '&.Mui-selected': {
                bgcolor: 'rgba(79, 195, 247, 0.12)',
                '& .MuiListItemIcon-root': { color: '#4fc3f7' },
                '& .MuiListItemText-primary': { color: '#4fc3f7', fontWeight: 600 },
              },
              '&:hover': { bgcolor: 'rgba(79, 195, 247, 0.08)' },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: '#64748b' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} sx={{ '& .MuiListItemText-primary': { fontSize: '0.85rem', color: '#94a3b8' } }} />
          </ListItemButton>
        ))}
      </List>
      <Box sx={{ mt: 'auto', p: 2, borderTop: '1px solid #1e293b' }}>
        <Typography variant="caption" sx={{ color: '#475569', display: 'block', textAlign: 'center' }}>
          BMKG — PIMES v0.1.0-rc1
        </Typography>
      </Box>
    </Drawer>
  );
}
