import React from 'react';
import { AlertOctagon, RefreshCw, LogOut } from 'lucide-react';
import { clearTokens } from '../api/client';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  handleLogout = () => {
    clearTokens();
    window.location.href = '/login';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: '#090d16',
          color: '#e2e8f0',
          padding: '2rem',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textAlign: 'center'
        }}>
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            padding: '1.5rem',
            borderRadius: '50%',
            color: '#ef4444',
            marginBottom: '1.5rem',
            animation: 'pulse 2s infinite'
          }}>
            <AlertOctagon size={48} />
          </div>

          <h1 style={{ fontSize: '2rem', fontWeight: 700, margin: '0 0 0.5rem 0' }}>Something went wrong</h1>
          <p style={{ color: '#94a3b8', maxWidth: '480px', fontSize: '1rem', lineHeight: '1.6', margin: '0 0 2rem 0' }}>
            An unexpected client-side error occurred. You can try reloading the application or signing out.
          </p>

          {this.state.error && (
            <div style={{
              backgroundColor: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: '8px',
              padding: '1rem',
              maxWidth: '600px',
              width: '100%',
              textAlign: 'left',
              marginBottom: '2rem',
              overflowX: 'auto',
              maxHeight: '200px'
            }}>
              <div style={{ color: '#ef4444', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Error: {this.state.error.toString()}
              </div>
              {this.state.errorInfo && (
                <pre style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8', whiteSpace: 'pre-wrap' }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button 
              className="btn btn-primary"
              onClick={this.handleReset}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <RefreshCw size={16} />
              <span>Reload App</span>
            </button>
            <button 
              className="btn btn-ghost"
              onClick={this.handleLogout}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#94a3b8' }}
            >
              <LogOut size={16} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
