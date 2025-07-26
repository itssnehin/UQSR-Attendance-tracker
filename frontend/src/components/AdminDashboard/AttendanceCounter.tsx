import React, { useEffect, useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import socketService from '../../services/socketService';

// Add pulse animation styles
const pulseKeyframes = `
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = pulseKeyframes;
  document.head.appendChild(style);
}

const AttendanceCounter: React.FC = () => {
  const { state } = useAppContext();
  const [recentAttendees, setRecentAttendees] = useState<string[]>([]);
  const [animateCount, setAnimateCount] = useState(false);
  const [socketError, setSocketError] = useState<string>('');
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    // Reduce initial loading time
    const timer = setTimeout(() => {
      setIsInitialLoading(false);
    }, 300);

    // Set up socket event listeners for new registrations
    socketService.on('registration_success', (data: { count: number; runner_name: string }) => {
      // Clear any socket errors on successful registration
      setSocketError('');
      
      // Add new attendee to the recent list
      setRecentAttendees(prev => {
        const updated = [data.runner_name, ...prev].slice(0, 5); // Keep only the 5 most recent
        return updated;
      });
      
      // Trigger animation
      setAnimateCount(true);
      setTimeout(() => setAnimateCount(false), 1000);
    });

    // Handle socket connection errors with better messaging
    socketService.on('connect_error', (error: Error) => {
      setSocketError('⚠️ Failed to connect to real-time updates');
      console.error('Socket connection error:', error);
    });

    socketService.on('disconnect', (reason: string) => {
      if (reason === 'io server disconnect') {
        setSocketError('🔄 Server disconnected. Reconnecting...');
      } else {
        setSocketError('🔄 Connection lost. Reconnecting...');
      }
    });

    socketService.on('connect', () => {
      setSocketError('');
    });

    socketService.on('reconnect', () => {
      setSocketError('');
    });

    return () => {
      clearTimeout(timer);
      socketService.off('registration_success');
      socketService.off('connect_error');
      socketService.off('disconnect');
      socketService.off('reconnect');
    };
  }, []);

  const handleRetryConnection = () => {
    setSocketError('🔄 Reconnecting...');
    socketService.reconnect();
  };

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '1.5rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      maxWidth: '400px'
    }}>
      <div style={{
        textAlign: 'center',
        marginBottom: '1rem'
      }}>
        <h2 style={{
          color: '#2c3e50',
          marginBottom: '1rem',
          fontSize: '1.5rem'
        }}>
          📊 Today's Attendance
        </h2>
        {isInitialLoading ? (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '60px'
          }}>
            <div style={{
              color: '#3498db',
              fontSize: '1rem'
            }}>Loading...</div>
          </div>
        ) : (
          <div style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: '#27ae60',
            padding: '1rem',
            backgroundColor: '#e8f5e8',
            borderRadius: '8px',
            border: '2px solid #27ae60',
            transform: animateCount ? 'scale(1.1)' : 'scale(1)',
            transition: 'transform 0.3s ease'
          }}>
            {state.currentAttendance}
          </div>
        )}
      </div>
      
      {/* Socket Error Display */}
      {socketError && (
        <div style={{
          backgroundColor: '#fff3cd',
          color: '#856404',
          padding: '0.75rem',
          borderRadius: '4px',
          border: '1px solid #ffeaa7',
          marginBottom: '1rem',
          textAlign: 'center',
          fontSize: '0.9rem'
        }}>
          {socketError}
          <button
            onClick={handleRetryConnection}
            style={{
              marginLeft: '0.5rem',
              padding: '0.25rem 0.5rem',
              backgroundColor: '#f39c12',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer',
              fontSize: '0.8rem'
            }}
          >
            Retry
          </button>
        </div>
      )}
      
      {/* Connection Status */}
      {!socketError && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1rem',
          fontSize: '0.9rem',
          color: state.isConnected ? '#27ae60' : '#e74c3c'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: state.isConnected ? '#27ae60' : '#e74c3c',
            marginRight: '0.5rem',
            animation: state.isConnected ? 'none' : 'pulse 1.5s infinite'
          }}></span>
          {state.isConnected ? '✅ Live Updates Active' : '🔄 Reconnecting...'}
        </div>
      )}

      {/* Recent Attendees */}
      {recentAttendees.length > 0 && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '1rem',
          borderRadius: '4px',
          marginTop: '1rem'
        }}>
          <h3 style={{
            color: '#2c3e50',
            fontSize: '1rem',
            marginBottom: '0.5rem'
          }}>
            🕒 Recent Check-ins
          </h3>
          <ul style={{
            listStyle: 'none',
            padding: 0,
            margin: 0
          }}>
            {recentAttendees.map((name, index) => (
              <li key={`${name}-${index}`} style={{
                padding: '0.25rem 0',
                color: '#495057',
                fontSize: '0.9rem',
                borderBottom: index < recentAttendees.length - 1 ? '1px solid #dee2e6' : 'none'
              }}>
                • {name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AttendanceCounter;