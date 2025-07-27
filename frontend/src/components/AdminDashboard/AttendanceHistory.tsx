import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';
import { AttendanceHistoryItem } from '../../types';

interface AttendanceHistoryProps {
  daysToShow?: number;
}

const AttendanceHistory: React.FC<AttendanceHistoryProps> = ({ daysToShow = 7 }) => {
  const [historyData, setHistoryData] = useState<AttendanceHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDays, setSelectedDays] = useState<number>(daysToShow);

  // Helper function to get date string for n days ago
  function getDateString(daysAgo: number): string {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // Function to fetch attendance history
  const fetchAttendanceHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const startDate = getDateString(selectedDays);
      const endDate = getDateString(0);
      const data = await apiService.getAttendanceHistory(startDate, endDate);
      setHistoryData(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Failed to load attendance history');
      console.error('Error fetching attendance history:', err);
      setHistoryData([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount and when selected days change
  useEffect(() => {
    fetchAttendanceHistory();
  }, [selectedDays]);

  // Group attendance data by date (with safe handling)
  const groupedByDate = historyData.reduce<Record<string, { count: number; attendees: string[] }>>(
    (acc, item) => {
      if (!item || !item.runDate || !item.runnerName) return acc;
      
      const date = item.runDate;
      if (!acc[date]) {
        acc[date] = { count: 0, attendees: [] };
      }
      acc[date].count += 1;
      acc[date].attendees.push(item.runnerName);
      return acc;
    },
    {}
  );

  // Convert grouped data to array for rendering
  const dailyAttendance = Object.entries(groupedByDate).map(([date, data]) => ({
    date,
    count: data.count,
    attendees: data.attendees,
  }));

  // Sort by date (most recent first)
  dailyAttendance.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  // Handle date range change
  const handleDateRangeChange = (days: number) => {
    setSelectedDays(days);
  };

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '1.5rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      maxWidth: '500px'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem'
      }}>
        <h2 style={{
          color: '#2c3e50',
          margin: 0,
          fontSize: '1.5rem'
        }}>
          📋 Attendance History
        </h2>
        <div style={{
          display: 'flex',
          gap: '0.5rem'
        }}>
          {[7, 14, 30].map(days => (
            <button
              key={days}
              onClick={() => handleDateRangeChange(days)}
              style={{
                padding: '0.25rem 0.75rem',
                fontSize: '0.8rem',
                border: '1px solid #3498db',
                borderRadius: '4px',
                backgroundColor: selectedDays === days ? '#3498db' : 'white',
                color: selectedDays === days ? 'white' : '#3498db',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          color: '#6c757d'
        }}>
          Loading attendance history...
        </div>
      ) : error ? (
        <div style={{
          backgroundColor: '#f8d7da',
          color: '#721c24',
          padding: '1rem',
          borderRadius: '4px',
          border: '1px solid #f5c6cb',
          textAlign: 'center'
        }}>
          {error}
        </div>
      ) : dailyAttendance.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          color: '#6c757d'
        }}>
          No attendance data available for the selected period
        </div>
      ) : (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          {dailyAttendance.map((day) => (
            <div key={day.date} style={{
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              padding: '1rem'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.5rem'
              }}>
                <span style={{
                  fontWeight: 'bold',
                  color: '#2c3e50'
                }}>
                  {new Date(day.date).toLocaleDateString()}
                </span>
                <span style={{
                  backgroundColor: '#27ae60',
                  color: 'white',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '12px',
                  fontSize: '0.8rem'
                }}>
                  {day.count} runners
                </span>
              </div>
              <div style={{
                backgroundColor: '#f8f9fa',
                height: '8px',
                borderRadius: '4px',
                overflow: 'hidden',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  width: `${Math.min(100, (day.count / 20) * 100)}%`,
                  height: '100%',
                  backgroundColor: '#27ae60',
                  transition: 'width 0.3s ease'
                }} />
              </div>
              <div style={{
                fontSize: '0.9rem',
                color: '#6c757d'
              }}>
                {day.attendees.slice(0, 3).join(', ')}
                {day.attendees.length > 3 && ` +${day.attendees.length - 3} more`}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{
        textAlign: 'center',
        marginTop: '1rem'
      }}>
        <button 
          onClick={fetchAttendanceHistory}
          style={{
            backgroundColor: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}
        >
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
};

export default AttendanceHistory;