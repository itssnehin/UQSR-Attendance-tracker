import React from 'react';
import AttendanceCode from './AttendanceCode';

const AdminDashboard: React.FC = () => {
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
      </div>
    </div>
  );
};

export default AdminDashboard;