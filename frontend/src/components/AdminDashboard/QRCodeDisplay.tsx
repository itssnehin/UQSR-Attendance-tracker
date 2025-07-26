import React, { useState, useEffect, useCallback } from 'react';
import apiService from '../../services/apiService';
import { useAppContext } from '../../context/AppContext';
// import './QRCodeDisplay.css'; // Temporarily disabled

interface QRCodeDisplayProps {
  refreshInterval?: number; // in milliseconds, default 5 minutes
}

const QRCodeDisplay: React.FC<QRCodeDisplayProps> = ({ refreshInterval = 300000 }) => {
  const { state } = useAppContext();
  const { todayStatus } = state;
  const todaySessionId = todayStatus?.sessionId;
  const todayHasRun = todayStatus?.hasRun;
  
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Function to fetch QR code
  const fetchQRCode = useCallback(async () => {
    if (!todaySessionId || !todayHasRun) {
      setQrCode(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await apiService.getQRCode(todaySessionId);
      setQrCode(response.qr_code);
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      setError('Failed to load QR code');
      console.error('Error fetching QR code:', err);
    } finally {
      setLoading(false);
    }
  }, [todaySessionId, todayHasRun]);

  // Fetch QR code on component mount and when session ID changes
  useEffect(() => {
    fetchQRCode();
  }, [fetchQRCode]);

  // Set up auto-refresh interval
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchQRCode();
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [fetchQRCode, refreshInterval]);

  // Format time for display
  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Handle manual refresh
  const handleRefresh = () => {
    fetchQRCode();
  };

  // Handle print
  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="qr-code-display">
      <div className="qr-code-header">
        <h2>Today's QR Code</h2>
        <div className="qr-code-actions">
          <button className="refresh-button" onClick={handleRefresh}>
            Refresh QR Code
          </button>
          <button className="print-button" onClick={handlePrint}>
            Print QR Code
          </button>
        </div>
      </div>

      <div className="qr-code-container">
        {loading ? (
          <div className="loading">Loading QR code...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : !todayHasRun ? (
          <div className="no-run">No run scheduled for today</div>
        ) : !qrCode ? (
          <div className="no-qr">QR code not available</div>
        ) : (
          <div className="qr-code-content">
            <div className="qr-code-image-container">
              <img 
                src={`data:image/png;base64,${qrCode}`} 
                alt="QR Code for today's run" 
                className="qr-code-image" 
              />
            </div>
            <div className="qr-code-info">
              <p className="qr-code-date">
                <strong>Date:</strong> {new Date().toLocaleDateString()}
              </p>
              <p className="qr-code-session">
                <strong>Session ID:</strong> {todaySessionId}
              </p>
              <p className="qr-code-refresh">
                <strong>Last updated:</strong> {formatTime(lastRefresh)}
              </p>
              <p className="qr-code-instructions">
                Scan this QR code to register your attendance for today's run
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="qr-code-footer print-hide">
        <p>QR code automatically refreshes every {refreshInterval / 60000} minutes</p>
        <p>This QR code is valid for today's run only</p>
      </div>
    </div>
  );
};

export default QRCodeDisplay;