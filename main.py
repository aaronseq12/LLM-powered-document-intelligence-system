import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Toaster } from 'react-hot-toast';
import { theme } from './theme'; // Corrected path

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="app">
        <h1>Welcome to the Document Intelligence System</h1>
        <p>The application is running!</p>
      </div>
      <Toaster position="top-right" />
    </ThemeProvider>
  );
}

export default App;