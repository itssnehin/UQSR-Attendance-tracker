import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';
import { AttendanceHistoryItem } from '../../types';
import './AttendanceHistory.css';

interface AttendanceHistoryProps {
  daysToShow?: number;
}

const AttendanceHistory: React.FC<AttendanceHistoryProps> = ({ daysToShow = 7 }) => {
  const [historyData, setHistoryData] = useState<AttendanceHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<{ startDate: string; endDate: string }>({
    startDate: getDateString(daysToShow),
    endDate: getDateString(0),
  });

  // Helper function to get date string for n days ago
  function getDateString(daysAgo: number): string {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return date.toISOString().split('T')[0];
  }

  // Function to fetch attendance history
  const fetchAttendanceHistory = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAttendanceHistory(
        dateRange.startDate,
        dateRange.endDate
      );
      setHistoryData(data);
      setError(null);
    } catch (err) {
      setError('Failed to load attendance history');
      console.error('Error fetching attendance history:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount and when date range changes
  useEffect(() => {
    fetchAttendanceHistory();
  }, [dateRange.startDate, dateRange.endDate]);

  // Group attendance data by date
  const groupedByDate = historyData.reduce<Record<string, { count: number; attendees: string[] }>>(
    (acc, item) => {
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
    setDateRange({
      startDate: getDateString(days),
      endDate: getDateString(0),
    });
  };

  return (
    <div className="attendance-history">
      <div className="history-header">
        <h2>Attendance History</h2>
        <div className="date-range-selector">
          <button
            className={daysToShow === 7 ? 'active' : ''}
            onClick={() => handleDateRangeChange(7)}
          >
            7 Days
          </button>
          <button
            className={daysToShow === 14 ? 'active' : ''}
            onClick={() => handleDateRangeChange(14)}
          >
            14 Days
          </button>
          <button
            className={daysToShow === 30 ? 'active' : ''}
            onClick={() => handleDateRangeChange(30)}
          >
            30 Days
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading attendance history...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : dailyAttendance.length === 0 ? (
        <div className="no-data">No attendance data available for the selected period</div>
      ) : (
        <div className="history-chart">
          {dailyAttendance.map((day) => (
            <div key={day.date} className="history-day">
              <div className="day-header">
                <span className="day-date">{new Date(day.date).toLocaleDateString()}</span>
                <span className="day-count">{day.count} runners</span>
              </div>
              <div className="attendance-bar-container">
                <div 
                  className="attendance-bar" 
                  style={{ width: `${Math.min(100, (day.count / 20) * 100)}%` }}
                  title={`${day.count} runners attended`}
                ></div>
              </div>
              <div className="day-attendees">
                {day.attendees.slice(0, 3).join(', ')}
                {day.attendees.length > 3 && ` +${day.attendees.length - 3} more`}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="refresh-button-container">
        <button className="refresh-button" onClick={fetchAttendanceHistory}>
          Refresh Data
        </button>
      </div>
    </div>
  );
};

export default AttendanceHistory;