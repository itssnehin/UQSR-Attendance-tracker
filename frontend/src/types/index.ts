// Shared TypeScript interfaces matching backend data models

export interface RegistrationRequest {
  sessionId: string;
  runnerName: string;
  timestamp: Date;
}

export interface AttendanceResponse {
  success: boolean;
  message: string;
  current_count: number;
  runner_name?: string;
}

export interface CalendarDay {
  date: string;
  hasRun: boolean;
  attendanceCount?: number;
  sessionId?: string;
}

export interface Run {
  id: number;
  date: string;
  sessionId: string;
  isActive: boolean;
  createdAt: Date;
}

export interface Attendance {
  id: number;
  runId: number;
  runnerName: string;
  registeredAt: Date;
}

// Additional interfaces for frontend state management
export interface AppState {
  isLoading: boolean;
  error: string | null;
  currentAttendance: number;
  todayStatus: CalendarDay | null;
  calendar: CalendarDay[];
  isConnected: boolean;
}

export interface QRCodeData {
  qrCode: string;
  sessionId: string;
  expiresAt: Date;
}

export interface AttendanceHistoryItem {
  id: number;
  runDate: string;
  runnerName: string;
  registeredAt: string;
  sessionId: string;
}

export interface ExportOptions {
  startDate?: string;
  endDate?: string;
  format: 'csv' | 'json';
}

// Error handling types
export interface ApiError extends Error {
  status?: number;
  code?: string;
}

export interface NetworkError extends Error {
  name: 'NetworkError';
}

export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  retryCondition?: (error: Error) => boolean;
}