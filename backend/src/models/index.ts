// Data models and interfaces
export * from './Run';
export * from './Attendance';
export * from './CalendarConfig';

// Common types used across models
export interface DatabaseError {
  code: string;
  message: string;
  detail?: string;
}

export interface PaginationOptions {
  limit: number;
  offset: number;
}

export interface DateRange {
  startDate: Date;
  endDate: Date;
}