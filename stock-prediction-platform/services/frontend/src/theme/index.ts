import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:    { main: '#0EA5E9' },   // Sky blue
    secondary:  { main: '#8B5CF6' },   // Violet
    success:    { main: '#10B981' },   // Emerald
    error:      { main: '#F43F5E' },   // Rose
    warning:    { main: '#F59E0B' },   // Amber
    background: { default: '#050A14', paper: '#0A1120' },
    text:       { primary: '#E2E8F0', secondary: '#64748B' },
    divider:    'rgba(14, 165, 233, 0.1)',
  },
  typography: {
    fontFamily: '"IBM Plex Sans", ui-sans-serif, sans-serif',
    h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700, letterSpacing: '-0.01em' },
    h6: { fontWeight: 600, letterSpacing: '-0.01em' },
    subtitle1: { fontWeight: 600 },
    subtitle2: {
      fontWeight: 600,
      letterSpacing: '0.08em',
      textTransform: 'uppercase' as const,
      fontSize: '0.68rem',
      color: '#64748B',
    },
    body1: {
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: '0.875rem',
    },
    body2: {
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: '0.78rem',
    },
    caption: {
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: '0.7rem',
    },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#0A1120',
          border: '1px solid rgba(14, 165, 233, 0.12)',
          transition: 'border-color 0.2s ease',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
          backgroundColor: '#050A14',
          borderRight: '1px solid rgba(14, 165, 233, 0.1)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#050A14',
          color: '#64748B',
          fontFamily: '"IBM Plex Sans", sans-serif',
          fontWeight: 600,
          letterSpacing: '0.08em',
          fontSize: '0.68rem',
          textTransform: 'uppercase' as const,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '0.65rem',
          fontWeight: 500,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          fontFamily: '"IBM Plex Sans", sans-serif',
          fontWeight: 600,
          letterSpacing: '0.04em',
          textTransform: 'none' as const,
          fontSize: '0.8rem',
          borderRadius: 8,
        },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#0A1120',
          border: '1px solid rgba(14, 165, 233, 0.1)',
          '&:before': { display: 'none' },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: { borderColor: 'rgba(14, 165, 233, 0.1)' },
      },
    },
  },
});
