import React from 'react';

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
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        textAlign: 'center'
      }}>
        <p>Admin Dashboard is loading...</p>
        <p>This is a minimal version to test if the basic component works.</p>
      </div>
    </div>
  );
};

export default AdminDashboard;