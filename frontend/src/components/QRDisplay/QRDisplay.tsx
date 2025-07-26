import React from 'react';
import { useAppContext } from '../../context/AppContext';

const QRDisplay: React.FC = () => {
  const { state } = useAppContext();

  return (
    <div className="container">
      <h1>QR Code Display</h1>
      <div className="card">
        <h2>Today's Run QR Code</h2>
        {state.todayStatus?.hasRun ? (
          <div>
            <p>Session ID: {state.todayStatus.sessionId}</p>
            <p>QR Code will be displayed here</p>
          </div>
        ) : (
          <p>No run scheduled for today</p>
        )}
        <p>Connection Status: {state.isConnected ? 'Connected' : 'Disconnected'}</p>
      </div>
      {state.error && (
        <div className="card">
          <div className="error">Error: {state.error}</div>
        </div>
      )}
    </div>
  );
};

export default QRDisplay;