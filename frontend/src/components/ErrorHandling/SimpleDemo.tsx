import React, { useState } from 'react';
import { LoadingSpinner } from '../Loading';
import { ErrorMessage } from '../ErrorDisplay';
import ErrorBoundary from '../ErrorBoundary';

// Simple demo component to test our error handling and loading states
const SimpleDemo: React.FC = () => {
  const [showLoading, setShowLoading] = useState(false);
  const [showError, setShowError] = useState(false);
  const [throwError, setThrowError] = useState(false);

  const ThrowingComponent: React.FC = () => {
    if (throwError) {
      throw new Error('This is a test error for the error boundary!');
    }
    return <div>Component is working fine!</div>;
  };

  const simulateLoading = () => {
    setShowLoading(true);
    setTimeout(() => {
      setShowLoading(false);
    }, 3000);
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Error Handling & Loading States Demo</h1>
      
      {/* Loading Spinners Demo */}
      <section style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Loading Spinners</h2>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <p>Small:</p>
            <LoadingSpinner size="small" />
          </div>
          <div>
            <p>Medium:</p>
            <LoadingSpinner size="medium" text="Loading..." />
          </div>
          <div>
            <p>Large:</p>
            <LoadingSpinner size="large" color="secondary" />
          </div>
        </div>
        <button onClick={simulateLoading} disabled={showLoading}>
          {showLoading ? 'Loading...' : 'Simulate Loading'}
        </button>
        {showLoading && (
          <div style={{ marginTop: '1rem' }}>
            <LoadingSpinner size="medium" text="Simulating a loading operation..." />
          </div>
        )}
      </section>

      {/* Error Messages Demo */}
      <section style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Error Messages</h2>
        <button onClick={() => setShowError(!showError)} style={{ marginBottom: '1rem' }}>
          {showError ? 'Hide Error' : 'Show Error'}
        </button>
        
        {showError && (
          <div>
            <ErrorMessage 
              error="This is an error message with retry functionality" 
              onRetry={() => alert('Retry clicked!')}
              onDismiss={() => setShowError(false)}
            />
            <ErrorMessage 
              error="This is a warning message" 
              variant="warning"
              onDismiss={() => console.log('Warning dismissed')}
              showRetry={false}
            />
            <ErrorMessage 
              error="This is an info message" 
              variant="info"
              showDismiss={false}
            />
          </div>
        )}
      </section>

      {/* Error Boundary Demo */}
      <section style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Error Boundary</h2>
        <label style={{ marginBottom: '1rem', display: 'block' }}>
          <input
            type="checkbox"
            checked={throwError}
            onChange={(e) => setThrowError(e.target.checked)}
          />
          Simulate Component Error
        </label>
        
        <ErrorBoundary
          onError={(error, errorInfo) => {
            console.log('Error boundary caught:', error, errorInfo);
          }}
        >
          <div style={{ 
            padding: '1rem', 
            border: '1px solid #ddd', 
            borderRadius: '4px',
            backgroundColor: throwError ? '#ffe6e6' : '#e6ffe6'
          }}>
            <ThrowingComponent />
          </div>
        </ErrorBoundary>
      </section>

      {/* Combined Demo */}
      <section style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Combined Demo</h2>
        <p>This section demonstrates how loading states and error handling work together:</p>
        
        <button 
          onClick={() => {
            setShowLoading(true);
            setTimeout(() => {
              setShowLoading(false);
              setShowError(true);
            }, 2000);
          }}
          disabled={showLoading}
          style={{ marginBottom: '1rem' }}
        >
          Simulate API Call with Error
        </button>

        {showLoading && (
          <div style={{ marginBottom: '1rem' }}>
            <LoadingSpinner size="medium" text="Making API call..." />
          </div>
        )}
      </section>

      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
        <h3>Features Demonstrated:</h3>
        <ul>
          <li>✅ Loading spinners with different sizes and colors</li>
          <li>✅ Error messages with different variants (error, warning, info)</li>
          <li>✅ Error boundary for catching React component errors</li>
          <li>✅ Retry and dismiss functionality</li>
          <li>✅ Proper accessibility attributes</li>
        </ul>
      </div>
    </div>
  );
};

export default SimpleDemo;