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

  return (
    <div className={`error-message ${variant} ${className}`}>
      <div className="error-content">
        <span className="error-icon">{getIcon()}</span>
        <span className="error-text">{errorMessage}</span>
      </div>
      
      <div className="error-actions">
        {showRetry && onRetry && (
          <button 
            onClick={onRetry}
            className="error-action-button retry-button"
            type="button"
          >
            Retry
          </button>
        )}
        {showDismiss && onDismiss && (
          <button 
            onClick={onDismiss}
            className="error-action-button dismiss-button"
            type="button"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;