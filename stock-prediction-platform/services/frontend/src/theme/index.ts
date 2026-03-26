import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00bcd4' },
    secondary: { main: '#ff9800' },
    success: { main: '#4caf50' },
    error: { main: '#f44336' },
    background: { default: '#0a0e1a', paper: '#111827' },
    text: { primary: '#e8eaf6', secondary: '#9fa8da' },
  },
  typography: {
    fontFamily: '"IBM Plex Mono", "Roboto Mono", monospace',
    h4: { fontWeight: 700, letterSpacing: '0.05em' },
    h6: { fontWeight: 600 },
    body2: { fontSize: '0.8rem' },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(0,188,212,0.12)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#0d1117',
          color: '#9fa8da',
          fontWeight: 700,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
  },
});
