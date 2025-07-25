import React, { useState, useEffect, useCallback } from 'react';
import { CalendarDay } from '../../types';
import { useAppContext } from '../../context';
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
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
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

  const toggleRunDay = (date: Date) => {
    setSelectedDate(date);
    const dateString = getDateString(date);
    const existingDay = localCalendar.find(day => day.date === dateString);
    
    let updatedCalendar: CalendarDay[];
    
    if (existingDay) {
      // Toggle existing day
      updatedCalendar = localCalendar.map(day =>
        day.date === dateString 
          ? { ...day, hasRun: !day.hasRun }
          : day
      );
    } else {
      // Add new day
      const newDay: CalendarDay = {
        date: dateString,
        hasRun: true,
        attendanceCount: 0
      };
      updatedCalendar = [...localCalendar, newDay];
    }
    
    setLocalCalendar(updatedCalendar);
    setHasChanges(true);
  };
  
  const handleDateSelection = useCallback((date: Date) => {
    setSelectedDate(date);
  }, []);

  const saveChanges = async () => {
    try {
      setIsSaving(true);
      setError(null);
      
      await apiService.configureCalendar(localCalendar);
      setCalendar(localCalendar);
      setHasChanges(false);
      
      if (onSave) {
        onSave();
      }
    } catch (error) {
      setError('Failed to save calendar changes');
      console.error('Error saving calendar:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const resetChanges = () => {
    setLocalCalendar(state.calendar);
    setHasChanges(false);
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
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentYear, currentMonth, day);
      const dayData = getDayData(date);
      const isRunDay = dayData?.hasRun || false;
      const isTodayDate = isToday(date);
      const isSelected = selectedDate && isSameDay(date, selectedDate);
      
      days.push(
        <div
          key={day}
          className={`calendar-day ${isRunDay ? 'run-day' : ''} ${isTodayDate ? 'today' : ''} ${isSelected ? 'selected' : ''}`}
          onClick={() => toggleRunDay(date)}
          title={`${formatDate(date)}${isRunDay ? ' - Run Day' : ''}`}
          aria-label={`${formatDate(date)}${isRunDay ? ' - Run Day' : ''}${isTodayDate ? ' (Today)' : ''}`}
          aria-selected={isSelected}
          role="gridcell"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleRunDay(date);
            }
          }}
        >
          <span className="day-number">{day}</span>
          {isRunDay && <span className="run-indicator" aria-hidden="true">🏃</span>}
          {dayData?.attendanceCount !== undefined && dayData.attendanceCount > 0 && (
            <span className="attendance-count" title={`${dayData.attendanceCount} attendees`}>
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
    <div className="calendar-container" aria-label="Run Schedule Calendar">
      <div className="calendar-header">
        <button 
          className="nav-button"
          onClick={() => navigateMonth('prev')}
          disabled={state.isLoading}
          aria-label="Previous month"
        >
          ←
        </button>
        <h2 className="month-year">
          {monthNames[currentMonth]} {currentYear}
        </h2>
        <button 
          className="nav-button"
          onClick={() => navigateMonth('next')}
          disabled={state.isLoading}
          aria-label="Next month"
        >
          →
        </button>
      </div>

      <div className="calendar-grid" role="grid" aria-labelledby="month-year">
        {dayNames.map(dayName => (
          <div key={dayName} className="day-header" role="columnheader">
            {dayName}
          </div>
        ))}
        {renderCalendarDays()}
      </div>

      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-indicator run-day"></span>
          <span>Run Day</span>
        </div>
        <div className="legend-item">
          <span className="legend-indicator today"></span>
          <span>Today</span>
        </div>
        <div className="legend-item">
          <span className="legend-indicator selected"></span>
          <span>Selected</span>
        </div>
      </div>

      <div className="calendar-info">
        {selectedDate && (
          <div className="selected-date-info">
            <h3>Selected Date: {formatDate(selectedDate)}</h3>
            {getDayData(selectedDate) ? (
              <p>
                Status: {getDayData(selectedDate)?.hasRun ? 'Run Day' : 'No Run'} 
                {getDayData(selectedDate)?.attendanceCount ? 
                  ` | Attendance: ${getDayData(selectedDate)?.attendanceCount}` : ''}
              </p>
            ) : (
              <p>No configuration for this date yet</p>
            )}
          </div>
        )}
      </div>

      {hasChanges && (
        <div className="calendar-actions">
          <button 
            className="save-button"
            onClick={saveChanges}
            disabled={isSaving || state.isLoading}
            aria-label="Save calendar changes"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
          <button 
            className="reset-button"
            onClick={resetChanges}
            disabled={isSaving || state.isLoading}
            aria-label="Reset calendar changes"
          >
            Reset
          </button>
        </div>
      )}

      {state.isLoading && (
        <div className="loading-overlay" aria-live="polite">
          <div className="loading-spinner">Loading...</div>
        </div>
      )}
    </div>
  );
};

export default Calendar;