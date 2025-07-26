import React, { useReducer, useEffect, ReactNode } from 'react';
import AppContext, { AppContextType } from './AppContext';
import { AppState, CalendarDay } from '../types/index';
import socketService from '../services/socketService';

// Action types
type AppAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'UPDATE_ATTENDANCE'; payload: number }
  | { type: 'SET_TODAY_STATUS'; payload: CalendarDay | null }
  | { type: 'SET_CALENDAR'; payload: CalendarDay[] }
  | { type: 'SET_CONNECTION_STATUS'; payload: boolean };

// Initial state
const initialState: AppState = {
  isLoading: false,
  error: null,
  currentAttendance: 0,
  todayStatus: null,
  calendar: [],
  isConnected: false,
};

// Reducer function
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'UPDATE_ATTENDANCE':
      return { ...state, currentAttendance: action.payload };
    case 'SET_TODAY_STATUS':
      return { ...state, todayStatus: action.payload };
    case 'SET_CALENDAR':
      return { ...state, calendar: action.payload };
    case 'SET_CONNECTION_STATUS':
      return { ...state, isConnected: action.payload };
    default:
      return state;
  }
};

interface AppProviderProps {
  children: ReactNode;
}

const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Initialize socket connection and load initial data
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Import apiService dynamically to avoid circular dependency
        const { default: apiService } = await import('../services/apiService');
        
        // Load initial attendance count
        const todayData = await apiService.getTodayAttendance();
        dispatch({ type: 'UPDATE_ATTENDANCE', payload: todayData.count });
        
        // Load calendar data
        const calendarData = await apiService.getCalendar();
        dispatch({ type: 'SET_CALENDAR', payload: calendarData });
        
        // Find today's status
        const today = new Date().toISOString().split('T')[0];
        const todayStatus = calendarData.find(day => day.date === today);
        dispatch({ type: 'SET_TODAY_STATUS', payload: todayStatus || null });
        
      } catch (error) {
        console.error('Failed to initialize app data:', error);
        dispatch({ type: 'SET_ERROR', payload: 'Failed to load initial data' });
      }
    };

    initializeApp();
    socketService.connect();

    // Set up socket event listeners
    socketService.on('connect', () => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: true });
    });

    socketService.on('disconnect', () => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: false });
    });

    socketService.on('attendance_update', (data: { count: number }) => {
      dispatch({ type: 'UPDATE_ATTENDANCE', payload: data.count });
    });

    socketService.on('registration_success', (data: { count: number; runner_name: string }) => {
      dispatch({ type: 'UPDATE_ATTENDANCE', payload: data.count });
    });

    // Cleanup on unmount
    return () => {
      socketService.disconnect();
    };
  }, []);

  // Context value
  const contextValue: AppContextType = {
    state,
    updateAttendance: (count: number) => {
      dispatch({ type: 'UPDATE_ATTENDANCE', payload: count });
    },
    setLoading: (loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    },
    setError: (error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    },
    setTodayStatus: (status: CalendarDay | null) => {
      dispatch({ type: 'SET_TODAY_STATUS', payload: status });
    },
    setCalendar: (calendar: CalendarDay[]) => {
      dispatch({ type: 'SET_CALENDAR', payload: calendar });
    },
    setConnectionStatus: (connected: boolean) => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: connected });
    },
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

export default AppProvider;