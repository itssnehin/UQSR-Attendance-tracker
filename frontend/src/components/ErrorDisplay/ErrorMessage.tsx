import React from 'react';
// import './ErrorMessage.css'; // Temporarily disabled

interface ErrorMessageProps {
  error: string | Error | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'error' | 'warning' | 'info';
  className?: string;
  showRetry?: boolean;
  showDismiss?: boolean;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  error,
  onRetry,
  onDismiss,
  variant = 'error',
  className = '',
  showRetry = true,
  showDismiss = true,
}) => {
  if (!error) return null;

  const errorMessage = error instanceof Error ? error.message : error;
  
  const getIcon = () => {
    switch (variant) {
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  const variantStyles = {
    error: {
      backgroundColor: '#f8d7da',
      color: '#721c24',
      borderColor: '#f5c6cb'
    },
    warning: {
      backgroundColor: '#fff3cd',
      color: '#856404',
      borderColor: '#ffeaa7'
    },
    info: {
      backgroundColor: '#d1ecf1',
      color: '#0c5460',
      borderColor: '#bee5eb'
    }
  };

  return (
    <div style={{
      ...variantStyles[variant],
      padding: '0.75rem',
      borderRadius: '4px',
      border: `1px solid ${variantStyles[variant].borderColor}`,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      margin: '0.5rem 0'
    }} className={className}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        <span>{getIcon()}</span>
        <span>{errorMessage}</span>
      </div>
      
      <div style={{
        display: 'flex',
        gap: '0.5rem'
      }}>
        {showRetry && onRetry && (
          <button 
            onClick={onRetry}
            type="button"
            style={{
              backgroundColor: '#f39c12',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              padding: '0.25rem 0.5rem',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            Retry
          </button>
        )}
        {showDismiss && onDismiss && (
          <button 
            onClick={onDismiss}
            type="button"
            aria-label="Dismiss error"
            style={{
              backgroundColor: 'transparent',
              color: 'inherit',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '0 0.25rem'
            }}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;