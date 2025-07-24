// Types for the Runner Attendance Tracker application

// Registration request data
export interface RegistrationRequest {
  sessionId: string;
  runnerName: string;
  timestamp: Date;
}

// Response from attendance registration
export interface AttendanceResponse {
  success: boolean;
  message: string;
  current_count: number;
  runner_name?: string;
}

// Calendar day configuration
export interface CalendarDay {
  date: string; // ISO date string (YYYY-MM-DD)
  has_run: boolean;
  attendance_count?: number;
  session_id?: string;
}

// Attendance history item
export interface AttendanceHistoryItem {
  id: number;
  runDate: string;
  runnerName: string;
  registeredAt: string;
  sessionId: string;
}

// QR code response from API
export interface QRCodeResponse {
  qr_code: string; // Base64 encoded image
  session_id: string;
}