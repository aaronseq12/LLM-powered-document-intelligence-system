import { createTheme, ThemeOptions } from '@mui/material/styles';

// ==============================================================================
// Material-UI Theme for the LLM Document Intelligence System
//
// This file defines the custom theme for the application's user interface,
// ensuring a consistent and professional look and feel.
// ==============================================================================

// --- Color Palette ---
// A carefully selected color palette to create a modern and accessible UI.
const colors = {
  primary: {
    main: '#0284c7', // A professional blue
    light: '#38bdf8',
    dark: '#0369a1',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#475569', // A neutral gray
    light: '#94a3b8',
    dark: '#334155',
    contrastText: '#ffffff',
  },
  success: {
    main: '#16a34a', // A clear green for success states
  },
  warning: {
    main: '#d97706', // A distinct yellow for warnings
  },
  error: {
    main: '#dc2626', // A strong red for errors
  },
  background: {
    default: '#f8fafc', // A light gray for the page background
    paper: '#ffffff',   // White for paper elements like cards
  },
  text: {
    primary: '#0f172a',   // A dark slate for primary text
    secondary: '#64748b', // A lighter gray for secondary text
  },
};

// --- Base Theme Configuration ---
// This object defines the core theme settings, including the color palette,
// typography, shape, and shadows.
const baseTheme: ThemeOptions = {
  palette: {
    mode: 'light',
    ...colors,
  },
  
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    h1: { fontSize: '2.5rem', fontWeight: 600 },
    h2: { fontSize: '2rem', fontWeight: 600 },
    h3: { fontSize: '1.75rem', fontWeight: 600 },
    button: {
      textTransform: 'none', // Buttons will use sentence case instead of uppercase
      fontWeight: 500,
    },
  },

  shape: {
    borderRadius: 8, // A modern, slightly rounded corner
  },

  // Custom shadows for a subtle depth effect
  shadows: [
    'none',
    '0px 1px 2px rgba(0, 0, 0, 0.05)',
    '0px 2px 4px rgba(0, 0, 0, 0.05)',
    '0px 4px 8px rgba(0, 0, 0, 0.05)',
    '0px 8px 16px rgba(0, 0, 0, 0.05)',
    ...Array(20).fill('none'),
  ],
};

// --- Component Overrides ---
// This section customizes the appearance of specific Material-UI components
// to match the application's design system.
const componentOverrides = {
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: baseTheme.shape?.borderRadius,
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: baseTheme.shadows?.[2],
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: baseTheme.shape?.borderRadius,
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: `1px solid ${colors.secondary.light}`,
        },
      },
    },
  },
};

// --- Create and Export the Theme ---
// The final theme is created by merging the base configuration with the
// component overrides.
export const theme = createTheme({
  ...baseTheme,
  ...componentOverrides,
});

export default theme;