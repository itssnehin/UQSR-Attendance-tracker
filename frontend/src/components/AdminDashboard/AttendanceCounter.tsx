import React, { useEffect, useState } from 'react';
import { useAppContext } from '../../context/AppContext';
import socketService from '../../services/socketService';
import { LoadingSpinner } from '../Loading';
import { ErrorMessage } from '../ErrorDisplay';
// import './AttendanceCounter.css'; // Temporarily disabled

const AttendanceCounter: React.FC = () => {
  const { state } = useAppContext();
  const [recentAttendees, setRecentAttendees] = useState<string[]>([]);
  const [animateCount, setAnimateCount] = useState(false);
  const [socketError, setSocketError] = useState<string>('');
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    // Set initial loading to false after component mounts
    const timer = setTimeout(() => {
      setIsInitialLoading(false);
    }, 1000);

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

    // Handle socket connection errors
    socketService.on('connect_error', (error: Error) => {
      setSocketError('Failed to connect to real-time updates');
      console.error('Socket connection error:', error);
    });

    socketService.on('disconnect', (reason: string) => {
      if (reason === 'io server disconnect') {
        setSocketError('Server disconnected. Attempting to reconnect...');
      }
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
    setSocketError('');
    socketService.connect();
  };

  return (
    <div className="attendance-counter">
      <div className="counter-header">
        <h2>Today's Attendance</h2>
        {isInitialLoading ? (
          <div className="counter-loading">
            <LoadingSpinner size="medium" />
          </div>
        ) : (
          <div className={`counter-value ${animateCount ? 'animate' : ''}`}>
            {state.currentAttendance}
          </div>
        )}
      </div>
      
      {/* Socket Error Display */}
      {socketError && (
        <ErrorMessage 
          error={socketError}
          variant="warning"
          onRetry={handleRetryConnection}
          onDismiss={() => setSocketError('')}
        />
      )}
      
      {/* Connection Status */}
      {!socketError && (
        <>
          {state.isConnected ? (
            <div className="connection-status connected">
              <span className="status-dot"></span> Live Updates Active
            </div>
          ) : (
            <div className="connection-status disconnected">
              <span className="status-dot"></span> Reconnecting...
            </div>
          )}
        </>
      )}

      {/* Recent Attendees */}
      {recentAttendees.length > 0 && (
        <div className="recent-attendees">
          <h3>Recent Check-ins</h3>
          <ul>
            {recentAttendees.map((name, index) => (
              <li key={`${name}-${index}`} className="attendee-item">
                {name}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default AttendanceCounter;