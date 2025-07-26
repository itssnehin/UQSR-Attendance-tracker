import React, { useState, useEffect } from 'react';
import AdminAuth from './AdminAuth';
import AdminDashboard from '../AdminDashboard/AdminDashboard';

const ProtectedAdminRoute: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated
    const adminStatus = localStorage.getItem('isAdmin');
    if (adminStatus === 'true') {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const handleAuthenticated = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('isAdmin');
    setIsAuthenticated(false);
  };

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{
          color: '#3498db',
          fontSize: '1.2rem'
        }}>
          Loading...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AdminAuth onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div>
      {/* Admin Navigation */}
      <nav style={{
        backgroundColor: '#2c3e50',
        padding: '1rem 2rem',
        marginBottom: '2rem',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <h1 style={{
            color: 'white',
            margin: 0,
            fontSize: '1.5rem',
            fontWeight: 'bold'
          }}>
            🏃‍♂️ Runner Attendance Tracker - Admin
          </h1>
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: '#e74c3c',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              fontSize: '0.9rem',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#c0392b'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#e74c3c'}
          >
            🚪 Logout
          </button>
        </div>
      </nav>
      
      <AdminDashboard />
    </div>
  );
};

export default ProtectedAdminRoute;