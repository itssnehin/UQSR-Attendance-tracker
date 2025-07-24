import React, { createContext, useContext, useReducer, ReactNode } from 'react';

// Define the state interface
interface AppState {
  currentAttendance: number;
  isConnected: boolean;
  todaySessionId: string | null;
  todayHasRun: boolean;
}

// Define action types
type AppAction = 
  | { type: 'SET_ATTENDANCE'; payload: number }
  | { type: 'SET_CONNECTION_STATUS'; payload: boolean }
  | { type: 'SET_TODAY_SESSION'; payload: { sessionId: string | null; hasRun: boolean } };

// Initial state
const initialState: AppState = {
  currentAttendance: 0,
  isConnected: false,
  todaySessionId: null,
  todayHasRun: false,
};

// Create context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}>({
  state: initialState,
  dispatch: () => null,
});

// Reducer function
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_ATTENDANCE':
      return {
        ...state,
        currentAttendance: action.payload,
      };
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        isConnected: action.payload,
      };
    case 'SET_TODAY_SESSION':
      return {
        ...state,
        todaySessionId: action.payload.sessionId,
        todayHasRun: action.payload.hasRun,
      };
    default:
      return state;
  }
};

// Provider component
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useAppContext = () => useContext(AppContext);