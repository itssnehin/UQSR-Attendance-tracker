import React, { useEffect, useState } from 'react';
import { useAppContext } from '../../context';
import socketService from '../../services/socketService';
import './AttendanceCounter.css';

const AttendanceCounter: React.FC = () => {
  const { state } = useAppContext();
  const [recentAttendees, setRecentAttendees] = useState<string[]>([]);
  const [animateCount, setAnimateCount] = useState(false);

  useEffect(() => {
    // Set up socket event listeners for new registrations
    socketService.on('registration_success', (data: { count: number; runner_name: string }) => {
      // Add new attendee to the recent list
      setRecentAttendees(prev => {
        const updated = [data.runner_name, ...prev].slice(0, 5); // Keep only the 5 most recent
        return updated;
      });
      
      // Trigger animation
      setAnimateCount(true);
      setTimeout(() => setAnimateCount(false), 1000);
    });

    return () => {
      socketService.off('registration_success');
    };
  }, []);

  return (
    <div className="attendance-counter">
      <div className="counter-header">
        <h2>Today's Attendance</h2>
        <div className={`counter-value ${animateCount ? 'animate' : ''}`}>
          {state.currentAttendance}
        </div>
      </div>
      
      {state.isConnected ? (
        <div className="connection-status connected">
          <span className="status-dot"></span> Live Updates Active
        </div>
      ) : (
        <div className="connection-status disconnected">
          <span className="status-dot"></span> Reconnecting...
        </div>
      )}

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