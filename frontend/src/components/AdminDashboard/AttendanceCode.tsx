import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../context/AppContext';
import apiService from '../../services/apiService';

const AttendanceCode: React.FC = () => {
  const { state } = useAppContext();
  const [attendanceCode, setAttendanceCode] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTodayStatus = async () => {
      try {
        setLoading(true);
        const response = await apiService.getTodayStatus();
        
        if (response.has_run_today && response.session_id) {
          setAttendanceCode(response.session_id);
          setError(null);
        } else {
          setAttendanceCode(null);
          setError(response.message || 'No run scheduled for today');
        }
      } catch (err) {
        setError('Failed to load attendance code');
        console.error('Error fetching today status:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTodayStatus();
  }, []);

  if (loading) {
    return (
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <h2 style={{ color: '#2c3e50', marginBottom: '1rem' }}>Today's Attendance Code</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error || !attendanceCode) {
    return (
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <h2 style={{ color: '#2c3e50', marginBottom: '1rem' }}>Today's Attendance Code</h2>
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '1rem',
          borderRadius: '4px',
          border: '1px solid #f5c6cb'
        }}>
          {error || 'No attendance code available'}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '2rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      textAlign: 'center'
    }}>
      <h2 style={{ color: '#2c3e50', marginBottom: '1rem' }}>Today's Attendance Code</h2>
      
      <div style={{
        backgroundColor: '#e8f5e8',
        border: '2px solid #27ae60',
        borderRadius: '8px',
        padding: '2rem',
        margin: '1rem 0'
      }}>
        <div style={{
          fontSize: '3rem',
          fontWeight: 'bold',
          color: '#27ae60',
          fontFamily: 'monospace',
          letterSpacing: '0.2em'
        }}>
          {attendanceCode}
        </div>
      </div>

      <div style={{
        backgroundColor: '#d1ecf1',
        color: '#0c5460',
        padding: '1rem',
        borderRadius: '4px',
        border: '1px solid #bee5eb',
        marginTop: '1rem'
      }}>
        <p style={{ margin: 0, fontSize: '0.9rem' }}>
          <strong>Instructions:</strong> Share this 5-digit code with runners. 
          They can enter it on the registration page to mark their attendance.
        </p>
      </div>

      <div style={{ marginTop: '1rem', color: '#6c757d', fontSize: '0.9rem' }}>
        Current attendance: <strong>{state.currentAttendance}</strong> runners
      </div>
    </div>
  );
};

export default AttendanceCode;