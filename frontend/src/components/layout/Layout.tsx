import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import Navbar from './Navbar';
import { safeAreaStyles } from '../../utils/responsive';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    // Responsive typography
    h1: {
      fontSize: 'clamp(1.75rem, 4vw, 3rem)',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: 'clamp(1.5rem, 3.5vw, 2.5rem)',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: 'clamp(1.25rem, 3vw, 2rem)',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h4: {
      fontSize: 'clamp(1.125rem, 2.5vw, 1.75rem)',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: 'clamp(1rem, 2vw, 1.5rem)',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: 'clamp(0.875rem, 1.8vw, 1.25rem)',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    body1: {
      fontSize: 'clamp(0.875rem, 1.5vw, 1rem)',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: 'clamp(0.75rem, 1.4vw, 0.875rem)',
      lineHeight: 1.6,
    },
    caption: {
      fontSize: 'clamp(0.7rem, 1.2vw, 0.75rem)',
      lineHeight: 1.4,
    },
  },
  breakpoints: {
    values: {
      xs: 0,
      sm: 576,
      md: 768,
      lg: 992,
      xl: 1200,
    },
  },
  spacing: 8, // Base spacing unit
  components: {
    // Global responsive component overrides
    MuiContainer: {
      styleOverrides: {
        root: {
          paddingLeft: 16,
          paddingRight: 16,
          '@media (min-width: 576px)': {
            paddingLeft: 24,
            paddingRight: 24,
          },
          '@media (min-width: 768px)': {
            paddingLeft: 32,
            paddingRight: 32,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          minHeight: 44, // Touch-friendly
          '@media (max-width: 767px)': {
            fontSize: '0.875rem',
            padding: '8px 16px',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minWidth: 44,
          minHeight: 44, // Touch-friendly
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          '@media (max-width: 767px)': {
            fontSize: '0.75rem',
            height: 24,
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          margin: 16,
          '@media (max-width: 767px)': {
            margin: 8,
            width: 'calc(100% - 16px)',
            maxWidth: 'none',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          '@media (max-width: 767px)': {
            padding: '8px',
            fontSize: '0.875rem',
          },
        },
      },
    },
  },
});

const Layout: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        minHeight: '100vh',
        ...safeAreaStyles.safeArea 
      }}>
        <Navbar />
        <Box 
          component="main" 
          sx={{ 
            flex: 1, 
            pt: { xs: 7, sm: 8 }, // Responsive top padding
            px: { xs: 1, sm: 2 }, // Responsive horizontal padding
            pb: { xs: 2, sm: 3 } // Responsive bottom padding
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default Layout;