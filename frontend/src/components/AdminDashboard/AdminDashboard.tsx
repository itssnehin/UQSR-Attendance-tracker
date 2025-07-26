import React, { useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import Calendar from './Calendar';
import AttendanceCounter from './AttendanceCounter';
import AttendanceHistory from './AttendanceHistory';
import AttendanceCode from './AttendanceCode';
import DataExport from './DataExport';
import apiService from '../../services/apiService';

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



  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '2rem'
    }}>
      <h1 style={{
        color: '#2c3e50',
        textAlign: 'center',
        marginBottom: '2rem',
        fontSize: '2.5rem'
      }}>
        📊 Admin Dashboard
      </h1>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '2rem'
      }}>
        <AttendanceCode />
        <AttendanceCounter />
        <Calendar />
        <AttendanceHistory daysToShow={7} />
        <DataExport />
      </div>

      {state.error && (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '1rem',
          borderRadius: '4px',
          border: '1px solid #f5c6cb',
          marginTop: '2rem',
          textAlign: 'center'
        }}>
          Error: {state.error}
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;