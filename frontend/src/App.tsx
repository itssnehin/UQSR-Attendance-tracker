import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import AdminDashboard from './components/AdminDashboard/AdminDashboard';
import RunnerRegistration from './components/RunnerRegistration/RunnerRegistration';

// Navigation Component
const Navigation: React.FC = () => {
  return (
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
          🏃‍♂️ Runner Attendance Tracker
        </h1>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <Link
            to="/home"
            style={{
              color: 'white',
              textDecoration: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              backgroundColor: '#7f8c8d',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#95a5a6'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#7f8c8d'}
          >
            🏠 Home
          </Link>
          <Link
            to="/admin"
            style={{
              color: 'white',
              textDecoration: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              backgroundColor: '#34495e',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#4a6741'}
            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#34495e'}
          >
            📊 Admin Dashboard
          </Link>
        </div>
      </div>
    </nav>
  );
};

// Home Page Component
const HomePage: React.FC = () => {
  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '3rem',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{
          color: '#2c3e50',
          marginBottom: '1.5rem',
          fontSize: '2rem'
        }}>
          Welcome to Runner Attendance Tracker
        </h2>
        <p style={{
          color: '#7f8c8d',
          fontSize: '1.1rem',
          lineHeight: '1.6',
          marginBottom: '2rem'
        }}>
          Track attendance at your daily social runs with ease.
          Administrators can manage run schedules and view attendance data,
          while runners can quickly register their attendance using QR codes.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '2rem',
          marginTop: '3rem'
        }}>
          <div style={{
            padding: '2rem',
            backgroundColor: '#ecf0f1',
            borderRadius: '8px',
            border: '2px solid #bdc3c7'
          }}>
            <h3 style={{ color: '#2c3e50', marginBottom: '1rem' }}>
              📊 For Administrators
            </h3>
            <p style={{ color: '#7f8c8d', marginBottom: '1.5rem' }}>
              Manage run schedules, view real-time attendance, and export data for analysis.
            </p>
            <Link
              to="/admin"
              style={{
                display: 'inline-block',
                backgroundColor: '#3498db',
                color: 'white',
                padding: '0.75rem 1.5rem',
                textDecoration: 'none',
                borderRadius: '4px',
                fontWeight: 'bold',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2980b9'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#3498db'}
            >
              Go to Admin Dashboard
            </Link>
          </div>

          <div style={{
            padding: '2rem',
            backgroundColor: '#e8f5e8',
            borderRadius: '8px',
            border: '2px solid #a5d6a7'
          }}>
            <h3 style={{ color: '#2c3e50', marginBottom: '1rem' }}>
              🏃‍♂️ For Runners
            </h3>
            <p style={{ color: '#7f8c8d', marginBottom: '1.5rem' }}>
              Quickly register your attendance by scanning the QR code or entering your details.
            </p>
            <Link
              to="/register"
              style={{
                display: 'inline-block',
                backgroundColor: '#27ae60',
                color: 'white',
                padding: '0.75rem 1.5rem',
                textDecoration: 'none',
                borderRadius: '4px',
                fontWeight: 'bold',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#2ecc71'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#27ae60'}
            >
              Register Attendance
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="App" style={{
        minHeight: '100vh',
        backgroundColor: '#f8f9fa',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
      }}>
        <ErrorBoundary>
          <Navigation />
          <Routes>
            <Route path="/" element={<RunnerRegistration />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/register" element={<RunnerRegistration />} />
            <Route path="/register/:sessionId" element={<RunnerRegistration />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </div>
    </Router>
  );
};

export default App;