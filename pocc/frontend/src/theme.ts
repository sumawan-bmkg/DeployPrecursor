import { createTheme } from '@mui/material/styles';

const BMKG_BLUE = '#003087';
const BMKG_LIGHT_BLUE = '#0066CC';
const BMKG_GREEN = '#00A651';
const BMKG_RED = '#E30613';
const BMKG_AMBER = '#FFB300';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: BMKG_BLUE, light: BMKG_LIGHT_BLUE },
    secondary: { main: BMKG_GREEN },
    success: { main: BMKG_GREEN },
    warning: { main: BMKG_AMBER },
    error: { main: BMKG_RED },
    background: {
      default: '#0a0e1a',
      paper: '#111827',
    },
    text: {
      primary: '#e0e6ed',
      secondary: '#94a3b8',
    },
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif',
    h1: { fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.02em' },
    h2: { fontSize: '1.3rem', fontWeight: 600 },
    h3: { fontSize: '1.1rem', fontWeight: 600 },
    subtitle1: { fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase' as const, letterSpacing: '0.1em' },
    body2: { fontSize: '0.8rem', color: '#64748b' },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          background: '#111827',
          border: '1px solid #1e293b',
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});
