import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedAdminRoute from './components/Auth/ProtectedAdminRoute';
import RunnerRegistration from './components/RunnerRegistration/RunnerRegistration';
import AppProvider from './context/AppProvider';

// Simple Navigation for Runners
const RunnerNavigation: React.FC = () => {
  return (
    <nav style={{
      backgroundColor: '#27ae60',
      padding: '1rem 2rem',
      marginBottom: '2rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'center',
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
          🏃‍♂️ Runner Attendance Registration
        </h1>
      </div>
    </nav>
  );
};



const App: React.FC = () => {
  return (
    <AppProvider>
      <Router>
        <div className="App" style={{
          minHeight: '100vh',
          backgroundColor: '#f8f9fa',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
        }}>
          <ErrorBoundary>
            <Routes>
              {/* Default route - Runner Registration */}
              <Route path="/" element={
                <>
                  <RunnerNavigation />
                  <RunnerRegistration />
                </>
              } />
              
              {/* Admin route - Protected */}
              <Route path="/admin" element={<ProtectedAdminRoute />} />
              
              {/* Legacy routes redirect to main registration */}
              <Route path="/register" element={<Navigate to="/" replace />} />
              <Route path="/register/:sessionId" element={<Navigate to="/" replace />} />
              <Route path="/home" element={<Navigate to="/" replace />} />
              
              {/* Catch all - redirect to registration */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </Router>
    </AppProvider>
  );
};

export default App;