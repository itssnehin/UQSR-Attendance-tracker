import React from 'react';
// import './LoadingSpinner.css'; // Temporarily disabled

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: 'primary' | 'secondary' | 'white';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = 'primary',
  text,
  className = '',
}) => {
  const sizeMap = {
    small: '20px',
    medium: '40px',
    large: '60px'
  };

  const colorMap = {
    primary: '#3498db',
    secondary: '#95a5a6',
    white: '#ffffff'
  };

  const spinnerSize = sizeMap[size];
  const spinnerColor = colorMap[color];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem'
    }} className={className}>
      <div 
        role="status" 
        aria-label="Loading"
        style={{
          width: spinnerSize,
          height: spinnerSize,
          border: `3px solid ${spinnerColor}20`,
          borderTop: `3px solid ${spinnerColor}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}
      />
      {text && (
        <p style={{
          marginTop: '0.5rem',
          color: '#6c757d',
          fontSize: '0.9rem'
        }}>
          {text}
        </p>
      )}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default LoadingSpinner;