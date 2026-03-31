import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:    { main: '#7C3AED' },   // Vivid purple
    secondary:  { main: '#00F5FF' },   // Neon cyan
    success:    { main: '#00FF87' },   // Neon green
    error:      { main: '#FF2D78' },   // Hot pink/red
    warning:    { main: '#FFD60A' },   // Electric gold
    background: { default: '#02000A', paper: '#0D0A24' },
    text:       { primary: '#F0EEFF', secondary: '#6B60A8' },
    divider:    'rgba(124, 58, 237, 0.2)',
  },
  typography: {
    fontFamily: '"Inter", ui-sans-serif, sans-serif',
    h4: { fontWeight: 800, letterSpacing: '-0.03em' },
    h5: { fontWeight: 700, letterSpacing: '-0.02em' },
    h6: { fontWeight: 700, letterSpacing: '-0.01em' },
    subtitle1: { fontWeight: 600 },
    subtitle2: {
      fontWeight: 700,
      letterSpacing: '0.1em',
      textTransform: 'uppercase' as const,
      fontSize: '0.65rem',
      color: '#6B60A8',
    },
    body1: {
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: '0.875rem',
    },
    body2: {
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: '0.78rem',
    },
    caption: {
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: '0.68rem',
    },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(13, 10, 36, 0.7)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(124, 58, 237, 0.22)',
          transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
          '&:hover': {
            borderColor: 'rgba(0, 245, 255, 0.3)',
            boxShadow: '0 0 24px rgba(124, 58, 237, 0.12)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(13, 10, 36, 0.7)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(124, 58, 237, 0.22)',
          borderRadius: 16,
          transition: 'border-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease',
          '&:hover': {
            borderColor: 'rgba(0, 245, 255, 0.35)',
            boxShadow: '0 0 32px rgba(124, 58, 237, 0.18), 0 8px 32px rgba(0,0,0,0.4)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundImage: 'none',
          backgroundColor: '#07041A',
          borderRight: '1px solid rgba(124, 58, 237, 0.15)',
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
          backgroundColor: 'rgba(7, 4, 26, 0.9)',
          color: '#6B60A8',
          fontFamily: '"Inter", sans-serif',
          fontWeight: 700,
          letterSpacing: '0.1em',
          fontSize: '0.65rem',
          textTransform: 'uppercase' as const,
        },
        body: {
          borderColor: 'rgba(124, 58, 237, 0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '0.65rem',
          fontWeight: 600,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          fontFamily: '"Inter", sans-serif',
          fontWeight: 700,
          letterSpacing: '0.04em',
          textTransform: 'none' as const,
          fontSize: '0.82rem',
          borderRadius: 10,
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #7C3AED, #EC4899)',
          boxShadow: '0 0 20px rgba(124, 58, 237, 0.4)',
          '&:hover': {
            background: 'linear-gradient(135deg, #9D5CF6, #F06292)',
            boxShadow: '0 0 30px rgba(124, 58, 237, 0.6)',
          },
        },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: 'rgba(13, 10, 36, 0.7)',
          border: '1px solid rgba(124, 58, 237, 0.18)',
          '&:before': { display: 'none' },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: { borderColor: 'rgba(124, 58, 237, 0.15)' },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: 'rgba(13, 10, 36, 0.95)',
          border: '1px solid rgba(124, 58, 237, 0.3)',
          borderRadius: 8,
          fontFamily: '"JetBrains Mono", monospace',
          fontSize: '0.7rem',
        },
      },
    },
  },
});
