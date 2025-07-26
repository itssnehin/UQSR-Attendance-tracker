import React, { Component, ErrorInfo, ReactNode } from 'react';
// import './ErrorBoundary.css'; // Temporarily disabled

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to log this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: logErrorToService(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '400px',
          padding: '2rem',
          backgroundColor: '#f8f9fa'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '2rem',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            textAlign: 'center',
            maxWidth: '500px'
          }}>
            <div style={{
              fontSize: '3rem',
              marginBottom: '1rem'
            }}>⚠️</div>
            <h2 style={{
              color: '#e74c3c',
              marginBottom: '1rem'
            }}>Something went wrong</h2>
            <p style={{
              color: '#6c757d',
              marginBottom: '2rem',
              lineHeight: '1.5'
            }}>
              We're sorry, but something unexpected happened. Please try refreshing the page.
            </p>
            
            <div style={{
              display: 'flex',
              gap: '1rem',
              justifyContent: 'center'
            }}>
              <button 
                onClick={this.handleRetry}
                style={{
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                Try Again
              </button>
              <button 
                onClick={() => window.location.reload()}
                style={{
                  backgroundColor: '#27ae60',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.75rem 1.5rem',
                  cursor: 'pointer',
                  fontSize: '1rem'
                }}
              >
                Refresh Page
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={{
                marginTop: '2rem',
                textAlign: 'left',
                backgroundColor: '#f8f9fa',
                padding: '1rem',
                borderRadius: '4px'
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
                  Error Details (Development Only)
                </summary>
                <pre style={{
                  marginTop: '1rem',
                  fontSize: '0.8rem',
                  color: '#e74c3c',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;