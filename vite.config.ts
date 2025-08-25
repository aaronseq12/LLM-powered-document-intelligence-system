import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'
import { visualizer } from 'rollup-plugin-visualizer'

// ==============================================================================
// Vite Configuration for the Frontend Application
//
// This file configures Vite, the build tool used for the React frontend.
// It sets up plugins, path aliases, the development server, and the build process.
//
// For more information on Vite configuration, see the official documentation:
// https://vitejs.dev/config/
// ==============================================================================

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  
  return {
    plugins: [
      // Enables React Fast Refresh in development for a better developer experience.
      react(),
      
      // Allows using path aliases defined in tsconfig.json (e.g., `@/*`).
      tsconfigPaths(),
      
      // Generates a bundle analysis report in production to help optimize bundle size.
      isProduction && visualizer({
        filename: 'dist/stats.html',
        open: false,
      }),
    ],

    // --- Path Resolution ---
    // Defines path aliases for easier imports.
    resolve: {
      alias: {
        '@': '/src',
      },
    },

    // --- Development Server Configuration ---
    server: {
      port: 3000,
      host: '0.0.0.0', // Makes the server accessible on the local network
      open: false, // Prevents Vite from opening a new browser tab
      proxy: {
        // Proxies API requests to the backend server to avoid CORS issues.
        '/api': {
          target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        // Proxies WebSocket connections.
        '/ws': {
          target: process.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
          ws: true,
        },
      },
    },

    // --- Build Configuration ---
    build: {
      outDir: 'dist',
      sourcemap: !isProduction,
      rollupOptions: {
        output: {
          // Splits the bundle into smaller chunks for better performance.
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            mui: ['@mui/material', '@emotion/react', '@emotion/styled'],
            query: ['@tanstack/react-query'],
          },
        },
      },
    },

    // --- Global Constants ---
    // Defines global constants that can be accessed in the application code.
    define: {
      __IS_PRODUCTION__: isProduction,
    },
  };
});