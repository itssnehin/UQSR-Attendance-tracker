import React, { useState } from 'react';
import { useAsyncOperation } from '../../hooks';
import { LoadingSpinner } from '../Loading';
import { ErrorMessage } from '../ErrorDisplay';
import ErrorBoundary from '../ErrorBoundary';
import apiService from '../../services/apiService';

// Demo component showing comprehensive error handling and loading states
const ErrorHandlingDemo: React.FC = () => {
  const [simulateError, setSimulateError] = useState(false);

  // Example async operation with error handling
  const attendanceOperation = useAsyncOperation(
    async () => {
      if (simulateError) {
        throw new Error('Simulated network error');
      }
      return await apiService.getTodayAttendance();
    },
    {
      onSuccess: (data) => {
        console.log('Success:', data);
      },
      onError: (error) => {
        console.error('Operation failed:', error);
      }
    }
  );

  const ThrowingComponent: React.FC = () => {
    if (simulateError) {
      throw new Error('Component error for testing error boundary');
    }
    return <div>Component rendered successfully</div>;
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Error Handling & Loading States Demo</h2>
      
      {/* Error Boundary Demo */}
      <section style={{ marginBottom: '2rem' }}>
        <h3>Error Boundary</h3>
        <label>
          <input
            type="checkbox"
            checked={simulateError}
            onChange={(e) => setSimulateError(e.target.checked)}
          />
          Simulate Component Error
        </label>
        
        <ErrorBoundary
          onError={(error, errorInfo) => {
            console.log('Error boundary caught:', error, errorInfo);
          }}
        >
          <div style={{ padding: '1rem', border: '1px solid #ccc', marginTop: '1rem' }}>
            <ThrowingComponent />
          </div>
        </ErrorBoundary>
      </section>

      {/* Loading States Demo */}
      <section style={{ marginBottom: '2rem' }}>
        <h3>Loading Spinners</h3>
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
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
      </section>

      {/* Error Messages Demo */}
      <section style={{ marginBottom: '2rem' }}>
        <h3>Error Messages</h3>
        <ErrorMessage 
          error="This is an error message" 
          onRetry={() => console.log('Retry clicked')}
          onDismiss={() => console.log('Dismiss clicked')}
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
      </section>

      {/* Async Operation Demo */}
      <section style={{ marginBottom: '2rem' }}>
        <h3>Async Operation with Error Handling</h3>
        <div style={{ marginBottom: '1rem' }}>
          <label>
            <input
              type="checkbox"
              checked={simulateError}
              onChange={(e) => setSimulateError(e.target.checked)}
            />
            Simulate API Error
          </label>
        </div>
        
        <button
          onClick={() => attendanceOperation.execute()}
          disabled={attendanceOperation.state.loading}
          style={{ marginRight: '1rem' }}
        >
          {attendanceOperation.state.loading ? (
            <>
              <LoadingSpinner size="small" className="inline" />
              Loading...
            </>
          ) : (
            'Fetch Attendance Data'
          )}
        </button>

        <button onClick={attendanceOperation.reset}>
          Reset
        </button>

        {attendanceOperation.state.error && (
          <ErrorMessage
            error={attendanceOperation.state.error}
            onRetry={attendanceOperation.retry}
            onDismiss={attendanceOperation.reset}
          />
        )}

        {attendanceOperation.state.data && (
          <div style={{ 
            marginTop: '1rem', 
            padding: '1rem', 
            backgroundColor: '#d4edda', 
            border: '1px solid #c3e6cb',
            borderRadius: '4px'
          }}>
            <strong>Success!</strong> Data loaded: {JSON.stringify(attendanceOperation.state.data)}
          </div>
        )}
      </section>
    </div>
  );
};

export default ErrorHandlingDemo;