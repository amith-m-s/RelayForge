import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { OrgProvider } from './contexts/OrgContext';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import DashboardLayout from './layouts/DashboardLayout';
import { useAuth } from './hooks/useAuth';

const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const WebhooksPage = lazy(() => import('./pages/WebhooksPage'));
const PlaygroundPage = lazy(() => import('./pages/PlaygroundPage'));
const EventsPage = lazy(() => import('./pages/EventsPage'));
const DeliveriesPage = lazy(() => import('./pages/DeliveriesPage'));
const DeadLetterPage = lazy(() => import('./pages/DeadLetterPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;
  if (user) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
          <AuthProvider>
            <Suspense fallback={<div className="page-loader"><div className="loader-spinner" /></div>}>
              <Routes>
                <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
                <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
                <Route path="/" element={<ProtectedRoute><OrgProvider><DashboardLayout /></OrgProvider></ProtectedRoute>}>
                  <Route index element={<DashboardPage />} />
                  <Route path="webhooks" element={<WebhooksPage />} />
                  <Route path="playground" element={<PlaygroundPage />} />
                  <Route path="events" element={<EventsPage />} />
                  <Route path="deliveries" element={<DeliveriesPage />} />
                  <Route path="dead-letter" element={<DeadLetterPage />} />
                  <Route path="analytics" element={<AnalyticsPage />} />
                  <Route path="settings" element={<SettingsPage />} />
                </Route>
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </AuthProvider>
        </ToastProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
