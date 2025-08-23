import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider, CssBaseline, GlobalStyles } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { HelmetProvider } from 'react-helmet-async';
import { ErrorBoundary } from 'react-error-boundary';
import toast, { Toaster } from 'react-hot-toast';

// Theme and styles
import { theme } from './theme';
import { globalStyles } from '@/styles/globalStyles';

// Contexts
import { AuthProvider } from '@/contexts/AuthContext';
import { WebSocketProvider } from '@/contexts/WebSocketContext';
import { DocumentProvider } from '@/contexts/DocumentContext';
import { SettingsProvider } from '@/contexts/SettingsContext';

// Components
import Layout from '@/components/Layout/Layout';
import LoadingSpinner from '@/components/UI/LoadingSpinner';
import ErrorFallback from '@/components/Error/ErrorFallback';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';

// Lazy-loaded pages
const Dashboard = lazy(() => import('@/pages/Dashboard/Dashboard'));
const DocumentUpload = lazy(() => import('@/pages/DocumentUpload/DocumentUpload'));
const DocumentList = lazy(() => import('@/pages/DocumentList/DocumentList'));
const DocumentViewer = lazy(() => import('@/pages/DocumentViewer/DocumentViewer'));
const ProcessingQueue = lazy(() => import('@/pages/ProcessingQueue/ProcessingQueue'));
const Analytics = lazy(() => import('@/pages/Analytics/Analytics'));
const Settings = lazy(() => import('@/pages/Settings/Settings'));
const Profile = lazy(() => import('@/pages/Profile/Profile'));
const Login = lazy(() => import('@/pages/Auth/Login'));
const Register = lazy(() => import('@/pages/Auth/Register'));
const ForgotPassword = lazy(() => import('@/pages/Auth/ForgotPassword'));
const NotFound = lazy(() => import('@/pages/NotFound/NotFound'));

// React Query client configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnMount: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry mutations on client errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
      onError: (error: any) => {
        // Global error handling for mutations
        const errorMessage = error?.response?.data?.detail || error?.message || 'An error occurred';
        toast.error(errorMessage);
      },
    },
  },
});

// Error boundary error handler
const handleError = (error: Error, errorInfo: { componentStack: string }) => {
  console.error('Application Error:', error);
  console.error('Error Info:', errorInfo);
  
  // Send error to monitoring service in production
  if (process.env.NODE_ENV === 'production') {
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }
  
  toast.error('An unexpected error occurred. Please refresh the page.');
};

function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={handleError}>
      <HelmetProvider>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <CssBaseline />
              <GlobalStyles styles={globalStyles} />
              
              <SettingsProvider>
                <AuthProvider>
                  <WebSocketProvider>
                    <DocumentProvider>
                      <Router>
                        <div className="app">
                          <Routes>
                            {/* Public routes */}
                            <Route path="/login" element={
                              <Suspense fallback={<LoadingSpinner />}>
                                <Login />
                              </Suspense>
                            } />
                            <Route path="/register" element={
                              <Suspense fallback={<LoadingSpinner />}>
                                <Register />
                              </Suspense>
                            } />
                            <Route path="/forgot-password" element={
                              <Suspense fallback={<LoadingSpinner />}>
                                <ForgotPassword />
                              </Suspense>
                            } />
                            
                            {/* Protected routes with layout */}
                            <Route path="/" element={
                              <ProtectedRoute>
                                <Layout />
                              </ProtectedRoute>
                            }>
                              {/* Redirect root to dashboard */}
                              <Route index element={<Navigate to="/dashboard" replace />} />
                              
                              {/* Dashboard */}
                              <Route path="dashboard" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <Dashboard />
                                </Suspense>
                              } />
                              
                              {/* Document Management */}
                              <Route path="upload" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <DocumentUpload />
                                </Suspense>
                              } />
                              <Route path="documents" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <DocumentList />
                                </Suspense>
                              } />
                              <Route path="documents/:documentId" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <DocumentViewer />
                                </Suspense>
                              } />
                              
                              {/* Processing */}
                              <Route path="processing" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <ProcessingQueue />
                                </Suspense>
                              } />
                              
                              {/* Analytics */}
                              <Route path="analytics" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <Analytics />
                                </Suspense>
                              } />
                              
                              {/* User Management */}
                              <Route path="profile" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <Profile />
                                </Suspense>
                              } />
                              
                              {/* Settings */}
                              <Route path="settings" element={
                                <Suspense fallback={<LoadingSpinner />}>
                                  <Settings />
                                </Suspense>
                              } />
                            </Route>
                            
                            {/* 404 route */}
                            <Route path="*" element={
                              <Suspense fallback={<LoadingSpinner />}>
                                <NotFound />
                              </Suspense>
                            } />
                          </Routes>
                        </div>
                      </Router>
                      
                      {/* Global toast notifications */}
                      <Toaster
                        position="top-right"
                        reverseOrder={false}
                        gutter={8}
                        containerClassName=""
                        containerStyle={{}}
                        toastOptions={{
                          // Default options for all toasts
                          duration: 5000,
                          style: {
                            background: theme.palette.background.paper,
                            color: theme.palette.text.primary,
                            fontSize: '14px',
                            fontFamily: theme.typography.fontFamily,
                            boxShadow: theme.shadows[8],
                            borderRadius: theme.shape.borderRadius,
                            padding: '12px 16px',
                            maxWidth: '400px',
                          },
                          success: {
                            duration: 4000,
                            iconTheme: {
                              primary: theme.palette.success.main,
                              secondary: theme.palette.success.contrastText,
                            },
                          },
                          error: {
                            duration: 6000,
                            iconTheme: {
                              primary: theme.palette.error.main,
                              secondary: theme.palette.error.contrastText,
                            },
                          },
                          loading: {
                            duration: Infinity,
                            iconTheme: {
                              primary: theme.palette.primary.main,
                              secondary: theme.palette.primary.contrastText,
                            },
                          },
                        }}
                      />
                    </DocumentProvider>
                  </WebSocketProvider>
                </AuthProvider>
              </SettingsProvider>
            </LocalizationProvider>
          </ThemeProvider>
          
          {/* React Query DevTools (only in development) */}
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools 
              initialIsOpen={false}
              position="bottom-left"
              toggleButtonProps={{
                style: {
                  marginLeft: '5px',
                  transform: 'scale(0.8)',
                  transformOrigin: 'bottom left',
                },
              }}
            />
          )}
        </QueryClientProvider>
      </HelmetProvider>
    </ErrorBoundary>
  );
}

export default App;