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

// --- Theme and Styling ---
import { theme } from './theme';
import { globalStyles } from '@/styles/globalStyles';

// --- Application Contexts ---
// Provides a centralized way to manage application state and logic.
import { AuthProvider } from '@/contexts/AuthContext';
import { WebSocketProvider } from '@/contexts/WebSocketContext';
import { DocumentProvider } from '@/contexts/DocumentContext';
import { SettingsProvider } from '@/contexts/SettingsContext';

// --- UI Components ---
import Layout from '@/components/Layout/Layout';
import LoadingSpinner from '@/components/UI/LoadingSpinner';
import ErrorFallback from '@/components/Error/ErrorFallback';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';

// --- Page Components (Lazy Loaded) ---
// Lazy loading pages improves initial load time by splitting the code into smaller chunks.
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

// --- React Query Configuration ---
// Configures the data fetching and caching library, React Query.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Defines retry logic for failed queries.
      retry: (failureCount, error) => {
        // Do not retry on 4xx client errors (e.g., bad request, not found).
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        // Retry up to 3 times for other errors.
        return failureCount < 3;
      },
      staleTime: 5 * 60 * 1000, // Data is considered fresh for 5 minutes.
      cacheTime: 10 * 60 * 1000, // Data is kept in the cache for 10 minutes.
      refetchOnWindowFocus: false, // Prevents refetching when the window regains focus.
      refetchOnMount: true, // Refetches data when a component mounts.
      refetchOnReconnect: true, // Refetches data on network reconnection.
    },
    mutations: {
      // Defines retry logic for failed mutations.
      retry: (failureCount, error) => {
        // Do not retry mutations on client errors.
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
      // Global error handler for mutations.
      onError: (error) => {
        const errorMessage = error?.response?.data?.detail || error?.message || 'An error occurred';
        toast.error(errorMessage);
      },
    },
  },
});

// --- Error Boundary Handler ---
// A global error handler for the React application.
const handleError = (error, errorInfo) => {
  console.error('Application Error:', error);
  console.error('Error Info:', errorInfo);
  
  // In a production environment, you would send the error to a monitoring service.
  if (process.env.NODE_ENV === 'production') {
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }
  
  toast.error('An unexpected error occurred. Please refresh the page.');
};

/**
 * The main application component.
 * This component sets up the entire application structure, including routing,
 * context providers, and global error handling.
 */
function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={handleError}>
      <HelmetProvider>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <CssBaseline />
              <GlobalStyles styles={globalStyles} />
              
              {/* --- Context Providers --- */}
              <SettingsProvider>
                <AuthProvider>
                  <WebSocketProvider>
                    <DocumentProvider>
                      <Router>
                        <div className="app">
                          <Routes>
                            {/* --- Public Routes --- */}
                            <Route path="/login" element={<Suspense fallback={<LoadingSpinner />}><Login /></Suspense>} />
                            <Route path="/register" element={<Suspense fallback={<LoadingSpinner />}><Register /></Suspense>} />
                            <Route path="/forgot-password" element={<Suspense fallback={<LoadingSpinner />}><ForgotPassword /></Suspense>} />
                            
                            {/* --- Protected Routes --- */}
                            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                              <Route index element={<Navigate to="/dashboard" replace />} />
                              
                              {/* --- Application Pages --- */}
                              <Route path="dashboard" element={<Suspense fallback={<LoadingSpinner />}><Dashboard /></Suspense>} />
                              <Route path="upload" element={<Suspense fallback={<LoadingSpinner />}><DocumentUpload /></Suspense>} />
                              <Route path="documents" element={<Suspense fallback={<LoadingSpinner />}><DocumentList /></Suspense>} />
                              <Route path="documents/:documentId" element={<Suspense fallback={<LoadingSpinner />}><DocumentViewer /></Suspense>} />
                              <Route path="processing" element={<Suspense fallback={<LoadingSpinner />}><ProcessingQueue /></Suspense>} />
                              <Route path="analytics" element={<Suspense fallback={<LoadingSpinner />}><Analytics /></Suspense>} />
                              <Route path="profile" element={<Suspense fallback={<LoadingSpinner />}><Profile /></Suspense>} />
                              <Route path="settings" element={<Suspense fallback={<LoadingSpinner />}><Settings /></Suspense>} />
                            </Route>
                            
                            {/* --- 404 Not Found Route --- */}
                            <Route path="*" element={<Suspense fallback={<LoadingSpinner />}><NotFound /></Suspense>} />
                          </Routes>
                        </div>
                      </Router>
                      
                      {/* --- Global Toast Notifications --- */}
                      <Toaster
                        position="top-right"
                        reverseOrder={false}
                        gutter={8}
                        toastOptions={{
                          duration: 5000,
                          style: {
                            background: theme.palette.background.paper,
                            color: theme.palette.text.primary,
                            fontSize: '14px',
                            fontFamily: theme.typography.fontFamily,
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
                        }}
                      />
                    </DocumentProvider>
                  </WebSocketProvider>
                </AuthProvider>
              </SettingsProvider>
            </LocalizationProvider>
          </ThemeProvider>
          
          {/* --- React Query DevTools (Development Only) --- */}
          {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
        </QueryClientProvider>
      </HelmetProvider>
    </ErrorBoundary>
  );
}

export default App;