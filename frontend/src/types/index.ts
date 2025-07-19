// Shared TypeScript interfaces matching backend data models

export interface RegistrationRequest {
  sessionId: string;
  runnerName: string;
  timestamp: Date;
}

export interface AttendanceResponse {
  success: boolean;
  message: string;
  currentCount: number;
  runnerName?: string;
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