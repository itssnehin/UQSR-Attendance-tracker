import React, { useState } from 'react';
import apiService from '../../services/apiService';
import { useAppContext } from '../../context/AppContext';
import { useAsyncOperation } from '../../hooks';
import { LoadingSpinner } from '../Loading';
import { ErrorMessage } from '../ErrorDisplay';
// import './DataExport.css'; // Temporarily disabled

interface ExportHistoryItem {
  id: string;
  filename: string;
  startDate?: string;
  endDate?: string;
  exportedAt: Date;
  status: 'success' | 'error';
  errorMessage?: string;
}

const DataExport: React.FC = () => {
  const { state, setError } = useAppContext();
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [exportHistory, setExportHistory] = useState<ExportHistoryItem[]>([]);
  const [validationError, setValidationError] = useState<string>('');

  const exportOperation = useAsyncOperation(
    (startDate?: string, endDate?: string) => apiService.exportAttendance(startDate, endDate),
    {
      onSuccess: (blob: Blob) => {
        const filename = generateFilename(startDate || undefined, endDate || undefined);
        downloadBlob(blob, filename);
        addToHistory(filename, startDate || undefined, endDate || undefined, 'success');
        
        // Clear form after successful export
        setStartDate('');
        setEndDate('');
        setValidationError('');
      },
      onError: (error: Error) => {
        const filename = generateFilename(startDate || undefined, endDate || undefined);
        const errorMessage = error.message;
        addToHistory(filename, startDate || undefined, endDate || undefined, 'error', errorMessage);
      }
    }
  );

  const generateFilename = (start?: string, end?: string): string => {
    const todayDate = new Date();
    const today = `${todayDate.getFullYear()}-${String(todayDate.getMonth() + 1).padStart(2, '0')}-${String(todayDate.getDate()).padStart(2, '0')}`;
    
    if (start && end) {
      return `attendance_export_${start}_to_${end}.csv`;
    } else if (start) {
      return `attendance_export_from_${start}.csv`;
    } else if (end) {
      return `attendance_export_until_${end}.csv`;
    } else {
      return `attendance_export_${today}.csv`;
    }
  };

  const addToHistory = (
    filename: string,
    start?: string,
    end?: string,
    status: 'success' | 'error' = 'success',
    errorMessage?: string
  ) => {
    const historyItem: ExportHistoryItem = {
      id: Date.now().toString(),
      filename,
      startDate: start,
      endDate: end,
      exportedAt: new Date(),
      status,
      errorMessage,
    };

    setExportHistory(prev => [historyItem, ...prev.slice(0, 9)]); // Keep last 10 exports
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const validateDates = (): boolean => {
    if (startDate && endDate && startDate > endDate) {
      setValidationError('Start date must be before or equal to end date');
      return false;
    }
    setValidationError('');
    return true;
  };

  const handleExport = async () => {
    if (!validateDates()) {
      return;
    }

    try {
      await exportOperation.execute(startDate || undefined, endDate || undefined);
    } catch (error) {
      // Error is already handled by the useAsyncOperation hook
      console.error('Export failed:', error);
    }
  };

  const handleQuickExport = async (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    const startStr = `${start.getFullYear()}-${String(start.getMonth() + 1).padStart(2, '0')}-${String(start.getDate()).padStart(2, '0')}`;
    const endStr = `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, '0')}-${String(end.getDate()).padStart(2, '0')}`;

    setStartDate(startStr);
    setEndDate(endStr);
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="data-export">
      <h3>Export Attendance Data</h3>
      
      <div className="export-form">
        <div className="date-range-section">
          <h4>Date Range Selection</h4>
          <div className="date-inputs">
            <div className="date-input-group">
              <label htmlFor="start-date">Start Date:</label>
              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={exportOperation.state.loading}
              />
            </div>
            <div className="date-input-group">
              <label htmlFor="end-date">End Date:</label>
              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={exportOperation.state.loading}
              />
            </div>
          </div>
          
          <div className="quick-select-buttons">
            <button
              type="button"
              onClick={() => handleQuickExport(7)}
              disabled={exportOperation.state.loading}
              className="quick-select-btn"
            >
              Last 7 Days
            </button>
            <button
              type="button"
              onClick={() => handleQuickExport(30)}
              disabled={exportOperation.state.loading}
              className="quick-select-btn"
            >
              Last 30 Days
            </button>
            <button
              type="button"
              onClick={() => handleQuickExport(90)}
              disabled={exportOperation.state.loading}
              className="quick-select-btn"
            >
              Last 90 Days
            </button>
          </div>
        </div>

        {/* Validation Error */}
        {validationError && (
          <ErrorMessage 
            error={validationError} 
            variant="warning"
            onDismiss={() => setValidationError('')}
            showRetry={false}
          />
        )}

        {/* Export Operation Error */}
        {exportOperation.state.error && (
          <ErrorMessage 
            error={exportOperation.state.error} 
            onRetry={exportOperation.retry}
            onDismiss={exportOperation.reset}
          />
        )}

        <div className="export-actions">
          <button
            onClick={handleExport}
            disabled={exportOperation.state.loading}
            className="export-btn"
          >
            {exportOperation.state.loading ? (
              <>
                <LoadingSpinner size="small" className="inline" />
                Exporting...
              </>
            ) : (
              'Export to CSV'
            )}
          </button>
          
          {!startDate && !endDate && (
            <p className="export-note">
              Leave dates empty to export all attendance data
            </p>
          )}
        </div>
      </div>

      {exportHistory.length > 0 && (
        <div className="export-history">
          <h4>Export History</h4>
          <div className="history-list">
            {exportHistory.map((item) => (
              <div key={item.id} className={`history-item ${item.status}`}>
                <div className="history-item-main">
                  <span className="filename">{item.filename}</span>
                  <span className="export-date">{formatDate(item.exportedAt)}</span>
                  <span className={`status-badge ${item.status}`}>
                    {item.status === 'success' ? '✓' : '✗'}
                  </span>
                </div>
                {item.status === 'error' && item.errorMessage && (
                  <div className="error-message">
                    Error: {item.errorMessage}
                  </div>
                )}
                {item.startDate || item.endDate ? (
                  <div className="date-range">
                    {item.startDate && item.endDate
                      ? `${item.startDate} to ${item.endDate}`
                      : item.startDate
                      ? `From ${item.startDate}`
                      : `Until ${item.endDate}`}
                  </div>
                ) : (
                  <div className="date-range">All data</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataExport;