import React, { createContext, useContext } from 'react';
import { AppState, CalendarDay } from '../types';

export interface AppContextType {
  state: AppState;
  updateAttendance: (count: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setTodayStatus: (status: CalendarDay | null) => void;
  setCalendar: (calendar: CalendarDay[]) => void;
  setConnectionStatus: (connected: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext;