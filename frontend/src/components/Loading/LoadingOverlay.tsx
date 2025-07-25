import React from 'react';
import LoadingSpinner from './LoadingSpinner';
// import './LoadingSpinner.css'; // Temporarily disabled

interface LoadingOverlayProps {
  isVisible: boolean;
  text?: string;
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isVisible,
  text = 'Loading...',
  className = '',
}) => {
  if (!isVisible) return null;

  return (
    <div className={`loading-overlay ${className}`}>
      <LoadingSpinner size="large" text={text} />
    </div>
  );
};

export default LoadingOverlay;