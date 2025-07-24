import React, { useEffect } from 'react';
import { useAppContext } from '../../context';
import Calendar from './Calendar';
import AttendanceCounter from './AttendanceCounter';
import AttendanceHistory from './AttendanceHistory';
import QRCodeDisplay from './QRCodeDisplay';
import apiService from '../../services/apiService';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const { state, updateAttendance, setError } = useAppContext();

  // Fetch initial attendance data
  useEffect(() => {
    const fetchTodayAttendance = async () => {
      try {
        const data = await apiService.getTodayAttendance();
        updateAttendance(data.count);
      } catch (err) {
        console.error('Error fetching today\'s attendance:', err);
        setError('Failed to load today\'s attendance data');
      }
    };

    fetchTodayAttendance();
  }, [updateAttendance, setError]);

  const handleCalendarSave = () => {
    // Optional callback when calendar is saved
    console.log('Calendar configuration saved successfully');
  };

  return (
    <div className="container">
      <h1>Admin Dashboard</h1>
      
      <div className="dashboard-grid">
        <div className="dashboard-column">
          <AttendanceCounter />
          <AttendanceHistory daysToShow={7} />
        </div>
        
        <div className="dashboard-column">
          <div className="card">
            <h2>Run Calendar Configuration</h2>
            <p>Click on dates to mark them as run days. Changes will be saved when you click "Save Changes".</p>
            <Calendar onSave={handleCalendarSave} />
          </div>
        </div>
      </div>
      
      <div className="qr-code-section">
        <QRCodeDisplay refreshInterval={300000} />
      </div>

      {state.error && (
        <div className="card error-card">
          <div className="error">Error: {state.error}</div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;