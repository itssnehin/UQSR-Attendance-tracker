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
      dispatch({ type: 'SET_LOADING', payload: true });
      
      try {
        // Import apiService dynamically to avoid circular dependency
        const { default: apiService } = await import('../services/apiService');
        
        console.log('🔄 Loading initial data...');
        
        // Load initial attendance count
        console.log('📊 Fetching today\'s attendance...');
        const todayData = await apiService.getTodayAttendance();
        console.log('📊 Today\'s attendance:', todayData);
        dispatch({ type: 'UPDATE_ATTENDANCE', payload: todayData.count });
        
        // Load calendar data
        console.log('📅 Fetching calendar data...');
        const calendarData = await apiService.getCalendar();
        console.log('📅 Calendar data:', calendarData);
        dispatch({ type: 'SET_CALENDAR', payload: calendarData });
        
        // Find today's status
        const today = new Date().toISOString().split('T')[0];
        const todayStatus = calendarData.find(day => day.date === today);
        dispatch({ type: 'SET_TODAY_STATUS', payload: todayStatus || null });
        
        console.log('✅ Initial data loaded successfully');
        dispatch({ type: 'SET_ERROR', payload: null });
        
      } catch (error) {
        console.error('❌ Failed to initialize app data:', error);
        dispatch({ type: 'SET_ERROR', payload: `Failed to load initial data: ${error instanceof Error ? error.message : 'Unknown error'}` });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    // Initialize data first, then socket
    initializeApp().then(() => {
      console.log('🔌 Connecting to WebSocket...');
      socketService.connect();
    });

    // Set up socket event listeners
    socketService.on('connect', () => {
      console.log('✅ WebSocket connected');
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: true });
    });

    socketService.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: false });
    });

    socketService.on('connect_error', (error: any) => {
      console.error('❌ WebSocket connection error:', error);
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: false });
    });

    socketService.on('attendance_update', (data: { count: number }) => {
      console.log('📊 Attendance update received:', data);
      dispatch({ type: 'UPDATE_ATTENDANCE', payload: data.count });
    });

    socketService.on('registration_success', (data: { count: number; runner_name: string }) => {
      console.log('✅ Registration success:', data);
      dispatch({ type: 'UPDATE_ATTENDANCE', payload: data.count });
    });

    // Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up connections...');
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