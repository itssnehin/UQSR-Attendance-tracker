import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Simple test component for QR functionality
const QRTest: React.FC = () => {
  const [qrData, setQrData] = React.useState<string>('');
  const [sessionId, setSessionId] = React.useState<string>('test-session-123');

  const testQRGeneration = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/qr/${sessionId}`);
      const data = await response.json();
      setQrData(JSON.stringify(data, null, 2));
    } catch (error) {
      setQrData(`Error: ${error}`);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', margin: '10px', borderRadius: '5px' }}>
      <h2>🔗 QR Code Test</h2>
      <div>
        <input 
          value={sessionId} 
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Session ID"
          style={{ marginRight: '10px', padding: '8px', border: '1px solid #ccc', borderRadius: '3px' }}
        />
        <button onClick={testQRGeneration} style={{ padding: '8px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
          Generate QR Code
        </button>
      </div>
      <pre style={{ background: '#f8f9fa', padding: '15px', marginTop: '10px', borderRadius: '3px', overflow: 'auto', maxHeight: '300px' }}>
        {qrData || 'Click "Generate QR Code" to test...'}
      </pre>
    </div>
  );
};

// Simple test component for Registration
const RegistrationTest: React.FC = () => {
  const [result, setResult] = React.useState<string>('');
  const [runnerName, setRunnerName] = React.useState<string>('John Doe');
  const [sessionId, setSessionId] = React.useState<string>('test-session-123');

  const testRegistration = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          runner_name: runnerName,
          timestamp: new Date().toISOString()
        })
      });
      const data = await response.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setResult(`Error: ${error}`);
    }
  };

  const testGetTodayAttendance = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/attendance/today');
      const data = await response.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setResult(`Error: ${error}`);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', margin: '10px', borderRadius: '5px' }}>
      <h2>👥 Registration Test</h2>
      <div style={{ marginBottom: '10px' }}>
        <input 
          value={runnerName} 
          onChange={(e) => setRunnerName(e.target.value)}
          placeholder="Runner Name"
          style={{ marginRight: '10px', padding: '8px', border: '1px solid #ccc', borderRadius: '3px' }}
        />
        <input 
          value={sessionId} 
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="Session ID"
          style={{ marginRight: '10px', padding: '8px', border: '1px solid #ccc', borderRadius: '3px' }}
        />
        <button onClick={testRegistration} style={{ padding: '8px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', marginRight: '10px' }}>
          Register Attendance
        </button>
        <button onClick={testGetTodayAttendance} style={{ padding: '8px 15px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
          Get Today's Attendance
        </button>
      </div>
      <pre style={{ background: '#f8f9fa', padding: '15px', borderRadius: '3px', overflow: 'auto', maxHeight: '300px' }}>
        {result || 'Click a button to test...'}
      </pre>
    </div>
  );
};

// Simple test component for Calendar
const CalendarTest: React.FC = () => {
  const [calendarData, setCalendarData] = React.useState<string>('');
  const [configData, setConfigData] = React.useState<string>('');

  const testGetCalendar = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/calendar');
      const data = await response.json();
      setCalendarData(JSON.stringify(data, null, 2));
    } catch (error) {
      setCalendarData(`Error: ${error}`);
    }
  };

  const testConfigureCalendar = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch('http://localhost:8000/api/calendar/configure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          date: today,
          has_run: true
        })
      });
      const data = await response.json();
      setConfigData(JSON.stringify(data, null, 2));
    } catch (error) {
      setConfigData(`Error: ${error}`);
    }
  };

  const testGetTodayStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/calendar/today');
      const data = await response.json();
      setConfigData(JSON.stringify(data, null, 2));
    } catch (error) {
      setConfigData(`Error: ${error}`);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', margin: '10px', borderRadius: '5px' }}>
      <h2>📅 Calendar Test</h2>
      <div style={{ marginBottom: '10px' }}>
        <button onClick={testGetCalendar} style={{ padding: '8px 15px', backgroundColor: '#6f42c1', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', marginRight: '10px' }}>
          Get Calendar
        </button>
        <button onClick={testConfigureCalendar} style={{ padding: '8px 15px', backgroundColor: '#fd7e14', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', marginRight: '10px' }}>
          Configure Today as Run Day
        </button>
        <button onClick={testGetTodayStatus} style={{ padding: '8px 15px', backgroundColor: '#20c997', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>
          Get Today's Status
        </button>
      </div>
      <div>
        <h3>Calendar Data:</h3>
        <pre style={{ background: '#f8f9fa', padding: '15px', borderRadius: '3px', overflow: 'auto', maxHeight: '200px' }}>
          {calendarData || 'Click "Get Calendar" to test...'}
        </pre>
        <h3>Configuration/Status Result:</h3>
        <pre style={{ background: '#f8f9fa', padding: '15px', borderRadius: '3px', overflow: 'auto', maxHeight: '200px' }}>
          {configData || 'Click a configuration button to test...'}
        </pre>
      </div>
    </div>
  );
};

// Backend health check
const HealthCheck: React.FC = () => {
  const [healthData, setHealthData] = React.useState<string>('');

  const checkHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setHealthData(JSON.stringify(data, null, 2));
    } catch (error) {
      setHealthData(`Error: ${error}`);
    }
  };

  React.useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', margin: '10px', borderRadius: '5px', backgroundColor: '#e9ecef' }}>
      <h2>🏥 Backend Health Check</h2>
      <button onClick={checkHealth} style={{ padding: '8px 15px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', marginBottom: '10px' }}>
        Refresh Health Status
      </button>
      <pre style={{ background: '#f8f9fa', padding: '15px', borderRadius: '3px', overflow: 'auto' }}>
        {healthData || 'Checking backend health...'}
      </pre>
    </div>
  );
};

// Main test dashboard
const TestDashboard: React.FC = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: '#343a40', borderBottom: '2px solid #007bff', paddingBottom: '10px' }}>
        🏃‍♂️ Runner Attendance Tracker - Feature Tests
      </h1>
      <p style={{ color: '#6c757d', fontSize: '16px' }}>
        Backend should be running on <strong>http://localhost:8000</strong>
      </p>
      
      <div style={{ display: 'grid', gap: '0', marginTop: '20px' }}>
        <HealthCheck />
        <QRTest />
        <RegistrationTest />
        <CalendarTest />
      </div>
      
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#d1ecf1', border: '1px solid #bee5eb', borderRadius: '5px' }}>
        <h3 style={{ color: '#0c5460' }}>📋 Test Instructions:</h3>
        <ol style={{ color: '#0c5460' }}>
          <li>First, check that the backend health check shows "healthy"</li>
          <li>Test QR code generation with different session IDs</li>
          <li>Test runner registration with the same session ID from QR test</li>
          <li>Configure today as a run day in the calendar</li>
          <li>Check today's status to see the configuration</li>
          <li>Register more attendees and check today's attendance count</li>
        </ol>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Navigate to="/test" replace />} />
          <Route path="/test" element={<TestDashboard />} />
          <Route path="*" element={<Navigate to="/test" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;