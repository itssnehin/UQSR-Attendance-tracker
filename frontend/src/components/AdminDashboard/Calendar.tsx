import React, { useState, useEffect } from 'react';
import { CalendarDay } from '../../types/index';
import { useAppContext } from '../../context/AppContext';
import apiService from '../../services/apiService';
import {
  getDateString,
  getDaysInMonth,
  getFirstDayOfMonth,
  isToday,
  formatDate,
  isSameDay
} from '../../utils/dateUtils';
// import './Calendar.css'; // Temporarily disabled

interface CalendarProps {
  onSave?: () => void;
  initialMonth?: Date;
}

const Calendar: React.FC<CalendarProps> = ({ onSave, initialMonth }) => {
  const { state, setLoading, setError, setCalendar } = useAppContext();
  const [currentDate, setCurrentDate] = useState(initialMonth || new Date());
  const [localCalendar, setLocalCalendar] = useState<CalendarDay[]>([]);

  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth();
  const daysInMonth = getDaysInMonth(currentYear, currentMonth);
  const firstDayOfMonth = getFirstDayOfMonth(currentYear, currentMonth);

  // Load calendar data on component mount and when month changes
  useEffect(() => {
    loadCalendarData();
  }, [currentMonth, currentYear]);

  // Sync with global state
  useEffect(() => {
    setLocalCalendar(state.calendar);
  }, [state.calendar]);

  const loadCalendarData = async () => {
    try {
      setLoading(true);
      const calendarData = await apiService.getCalendar();
      setCalendar(calendarData);
      setError(null);
    } catch (error) {
      setError('Failed to load calendar data');
      console.error('Error loading calendar:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleRunDay = async (date: Date) => {
    setSelectedDate(date);
    const dateString = getDateString(date);
    const existingDay = localCalendar.find(day => day.date === dateString);

    let updatedDay: CalendarDay;
    let updatedCalendar: CalendarDay[];

    if (existingDay) {
      // Toggle existing day
      updatedDay = { ...existingDay, hasRun: !existingDay.hasRun };
      updatedCalendar = localCalendar.map(day =>
        day.date === dateString ? updatedDay : day
      );
    } else {
      // Add new day
      updatedDay = {
        date: dateString,
        hasRun: true,
        attendanceCount: 0
      };
      updatedCalendar = [...localCalendar, updatedDay];
    }

    // Update local state immediately
    setLocalCalendar(updatedCalendar);

    // Save to backend immediately - send single day configuration
    try {
      setLoading(true);
      await apiService.configureRunDay(date, updatedDay.hasRun);
      setCalendar(updatedCalendar); // Update global state
      setError(null);
    } catch (error) {
      setError('Failed to save calendar changes');
      console.error('Error saving calendar:', error);
      // Revert local changes on error
      setLocalCalendar(state.calendar);
    } finally {
      setLoading(false);
    }
  };





  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (direction === 'prev') {
      newDate.setMonth(currentMonth - 1);
    } else {
      newDate.setMonth(currentMonth + 1);
    }
    setCurrentDate(newDate);
  };

  const getDayData = (date: Date): CalendarDay | undefined => {
    const dateString = getDateString(date);
    return localCalendar.find(day => day.date === dateString);
  };

  const renderCalendarDays = () => {
    const days = [];

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(
        <div key={`empty-${i}`} style={{
          padding: '0.75rem',
          minHeight: '40px'
        }}></div>
      );
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentYear, currentMonth, day);
      const dayData = getDayData(date);
      const isRunDay = dayData?.hasRun || false;
      const isTodayDate = isToday(date);
      const isSelected = selectedDate && isSameDay(date, selectedDate);

      let backgroundColor = '#ffffff';
      let color = '#495057';
      let border = '1px solid #dee2e6';

      if (isRunDay) {
        backgroundColor = '#d4edda';
        border = '2px solid #27ae60';
        color = '#155724';
      }
      if (isTodayDate) {
        backgroundColor = isRunDay ? '#c3e6cb' : '#f8d7da';
        border = '2px solid #e74c3c';
        color = isRunDay ? '#155724' : '#721c24';
      }
      if (isSelected) {
        border = '2px solid #007bff';
      }

      days.push(
        <div
          key={day}
          onClick={() => toggleRunDay(date)}
          title={`${formatDate(date)}${isRunDay ? ' - Run Day' : ''}`}
          aria-label={`${formatDate(date)}${isRunDay ? ' - Run Day' : ''}${isTodayDate ? ' (Today)' : ''}`}
          aria-selected={isSelected || false}
          role="gridcell"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleRunDay(date);
            }
          }}
          style={{
            padding: '0.75rem',
            minHeight: '40px',
            backgroundColor,
            color,
            border,
            borderRadius: '4px',
            cursor: 'pointer',
            textAlign: 'center',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.9rem',
            fontWeight: isRunDay || isTodayDate ? 'bold' : 'normal',
            transition: 'all 0.2s ease'
          }}
          onMouseOver={(e) => {
            if (!state.isLoading) {
              e.currentTarget.style.transform = 'scale(1.05)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            }
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          <span>{day}</span>
          {isRunDay && <span style={{ fontSize: '0.7rem' }} aria-hidden="true">🏃</span>}
          {dayData?.attendanceCount !== undefined && dayData.attendanceCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              backgroundColor: '#007bff',
              color: 'white',
              borderRadius: '50%',
              width: '16px',
              height: '16px',
              fontSize: '0.6rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }} title={`${dayData.attendanceCount} attendees`}>
              {dayData.attendanceCount}
            </span>
          )}
        </div>
      );
    }

    return days;
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '1.5rem',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      maxWidth: '500px'
    }} aria-label="Run Schedule Calendar">
      
      <h2 style={{
        color: '#2c3e50',
        textAlign: 'center',
        marginBottom: '1.5rem',
        fontSize: '1.5rem'
      }}>
        📅 Run Schedule
      </h2>

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <button
          onClick={() => navigateMonth('prev')}
          disabled={state.isLoading}
          aria-label="Previous month"
          style={{
            background: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '0.5rem 1rem',
            cursor: state.isLoading ? 'not-allowed' : 'pointer',
            fontSize: '1rem'
          }}
        >
          ← Prev
        </button>
        <h3 style={{
          color: '#2c3e50',
          margin: 0,
          fontSize: '1.2rem'
        }}>
          {monthNames[currentMonth]} {currentYear}
        </h3>
        <button
          onClick={() => navigateMonth('next')}
          disabled={state.isLoading}
          aria-label="Next month"
          style={{
            background: '#3498db',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '0.5rem 1rem',
            cursor: state.isLoading ? 'not-allowed' : 'pointer',
            fontSize: '1rem'
          }}
        >
          Next →
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '2px',
        marginBottom: '1rem'
      }} role="grid" aria-labelledby="month-year">
        {dayNames.map(dayName => (
          <div key={dayName} style={{
            padding: '0.5rem',
            textAlign: 'center',
            fontWeight: 'bold',
            backgroundColor: '#f8f9fa',
            color: '#495057',
            fontSize: '0.8rem'
          }} role="columnheader">
            {dayName}
          </div>
        ))}
        {renderCalendarDays()}
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'space-around',
        marginBottom: '1rem',
        fontSize: '0.8rem',
        color: '#6c757d'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            width: '12px',
            height: '12px',
            backgroundColor: '#27ae60',
            borderRadius: '2px',
            display: 'inline-block'
          }}></span>
          <span>Run Day</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            width: '12px',
            height: '12px',
            backgroundColor: '#e74c3c',
            borderRadius: '2px',
            display: 'inline-block'
          }}></span>
          <span>Today</span>
        </div>
      </div>

      {selectedDate && (
        <div style={{
          backgroundColor: '#f8f9fa',
          padding: '1rem',
          borderRadius: '4px',
          marginBottom: '1rem'
        }}>
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#2c3e50' }}>
            Selected: {formatDate(selectedDate)}
          </h4>
          {getDayData(selectedDate) ? (
            <p style={{ margin: 0, color: '#495057' }}>
              Status: {getDayData(selectedDate)?.hasRun ? '🏃 Run Day' : '❌ No Run'}
              {getDayData(selectedDate)?.attendanceCount ?
                ` | Attendance: ${getDayData(selectedDate)?.attendanceCount}` : ''}
            </p>
          ) : (
            <p style={{ margin: 0, color: '#6c757d' }}>Click to toggle run day</p>
          )}
        </div>
      )}

      {state.isLoading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255,255,255,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '8px'
        }} aria-live="polite">
          <div style={{ color: '#3498db', fontSize: '1rem' }}>Loading...</div>
        </div>
      )}

      <div style={{
        backgroundColor: '#d1ecf1',
        color: '#0c5460',
        padding: '0.75rem',
        borderRadius: '4px',
        border: '1px solid #bee5eb',
        fontSize: '0.85rem',
        textAlign: 'center'
      }}>
        <strong>Instructions:</strong> Click on any day to toggle it as a run day. Changes save automatically.
      </div>
    </div>
  );
};

export default Calendar;