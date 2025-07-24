import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context';
import AdminDashboard from './components/AdminDashboard';
import RunnerRegistration from './components/RunnerRegistration';
import QRDisplay from './components/QRDisplay';
import './App.css';

const App: React.FC = () => {
  return (
    <AppProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Navigate to="/admin" replace />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/register/:sessionId?" element={<RunnerRegistration />} />
            <Route path="/qr" element={<QRDisplay />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </Routes>
        </div>
      </Router>
    </AppProvider>
  );
};

export default App;