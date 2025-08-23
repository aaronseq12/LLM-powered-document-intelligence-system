import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import eslint from 'vite-plugin-eslint'
import { checker } from 'vite-plugin-checker'
import tsconfigPaths from 'vite-tsconfig-paths'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const isDev = mode === 'development'
  const isProd = mode === 'production'
  
  return {
    plugins: [
      react({
        // Enable React Fast Refresh
        fastRefresh: true,
        // Exclude test files from Fast Refresh
        exclude: [/\.test\.(ts|tsx)$/, /\.spec\.(ts|tsx)$/],
      }),
      
      // TypeScript path mapping
      tsconfigPaths(),
      
      // ESLint integration
      eslint({
        include: ['src/**/*.{ts,tsx}'],
        exclude: ['node_modules', 'dist'],
        cache: false,
        fix: isDev,
      }),
      
      // TypeScript type checking
      checker({
        typescript: true,
        overlay: {
          initialIsOpen: false,
          position: 'br',
        },
      }),
      
      // Bundle analyzer (only in build mode)
      isProd && visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
    ].filter(Boolean),

    // Path resolution
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@/components': resolve(__dirname, 'src/components'),
        '@/pages': resolve(__dirname, 'src/pages'),
        '@/hooks': resolve(__dirname, 'src/hooks'),
        '@/utils': resolve(__dirname, 'src/utils'),
        '@/services': resolve(__dirname, 'src/services'),
        '@/types': resolve(__dirname, 'src/types'),
        '@/styles': resolve(__dirname, 'src/styles'),
        '@/assets': resolve(__dirname, 'src/assets'),
        '@/contexts': resolve(__dirname, 'src/contexts'),
        '@/store': resolve(__dirname, 'src/store'),
        '@/constants': resolve(__dirname, 'src/constants'),
      },
    },

    // Development server configuration
    server: {
      port: 3000,
      host: '0.0.0.0',
      strictPort: true,
      open: false,
      cors: true,
      proxy: {
        '/api': {
          target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        },
        '/ws': {
          target: process.env.VITE_WS_BASE_URL || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true,
        },
      },
    },

    // Preview server configuration
    preview: {
      port: 3000,
      host: '0.0.0.0',
      strictPort: true,
      open: false,
    },

    // Build configuration
    build: {
      target: 'es2020',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: isDev ? 'inline' : false,
      minify: isProd ? 'esbuild' : false,
      cssMinify: isProd,
      
      // Bundle splitting
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html'),
        },
        output: {
          manualChunks: {
            // Vendor chunks
            vendor: ['react', 'react-dom'],
            mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
            router: ['react-router-dom'],
            query: ['@tanstack/react-query'],
            
            // Utility chunks
            utils: ['lodash', 'date-fns', 'uuid'],
            charts: ['recharts', 'd3'],
            pdf: ['react-pdf', 'pdfjs-dist'],
            
            // Socket and HTTP
            network: ['socket.io-client', 'axios'],
          },
          chunkFileNames: isProd ? 'assets/[name]-[hash].js' : 'assets/[name].js',
          entryFileNames: isProd ? 'assets/[name]-[hash].js' : 'assets/[name].js',
          assetFileNames: isProd ? 'assets/[name]-[hash].[ext]' : 'assets/[name].[ext]',
        },
      },
      
      // Chunk size warnings
      chunkSizeWarningLimit: 1000,
      
      // Asset inlining threshold
      assetsInlineLimit: 4096,
      
      // CSS code splitting
      cssCodeSplit: true,
      
      // Report compressed size
      reportCompressedSize: isProd,
    },

    // CSS configuration
    css: {
      modules: {
        localsConvention: 'camelCaseOnly',
        generateScopedName: isDev ? '[name]__[local]__[hash:base64:5]' : '[hash:base64:8]',
      },
      devSourcemap: isDev,
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`,
        },
      },
    },

    // Dependency optimization
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@mui/material',
        '@mui/icons-material',
        '@emotion/react',
        '@emotion/styled',
        '@tanstack/react-query',
        'axios',
        'socket.io-client',
        'lodash',
        'date-fns',
        'uuid',
        'react-dropzone',
        'react-hook-form',
        'zod',
      ],
      exclude: ['@vite/client', '@vite/env'],
    },

    // Define global constants
    define: {
      __DEV__: isDev,
      __PROD__: isProd,
      __VERSION__: JSON.stringify(process.env.npm_package_version),
    },

    // Environment variables
    envPrefix: 'VITE_',
    envDir: '.',

    // Public directory
    publicDir: 'public',

    // Base public path
    base: '/',

    // Cache directory
    cacheDir: 'node_modules/.vite',

    // Log level
    logLevel: isDev ? 'info' : 'warn',

    // Clear screen
    clearScreen: false,

    // Worker configuration
    worker: {
      format: 'es',
      plugins: [],
    },

    // JSON configuration
    json: {
      namedExports: true,
      stringify: false,
    },

    // esbuild configuration
    esbuild: {
      logOverride: { 'this-is-undefined-in-esm': 'silent' },
      target: 'es2020',
      format: 'esm',
      platform: 'browser',
      keepNames: isDev,
      minifyIdentifiers: isProd,
      minifySyntax: isProd,
      minifyWhitespace: isProd,
      treeShaking: true,
      legalComments: isProd ? 'none' : 'inline',
    },
  }
})