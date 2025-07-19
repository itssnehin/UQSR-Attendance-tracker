export interface CalendarConfig {
  id: number;
  date: Date;
  hasRun: boolean;
  updatedAt: Date;
}

export interface CreateCalendarConfigRequest {
  date: Date;
  hasRun: boolean;
}

export interface UpdateCalendarConfigRequest {
  hasRun: boolean;
}

export interface CalendarDay {
  date: string; // ISO date string for frontend compatibility
  hasRun: boolean;
  attendanceCount?: number;
  sessionId?: string;
}

export interface CalendarMonth {
  year: number;
  month: number; // 1-12
  days: CalendarDay[];
}

export class CalendarConfigValidator {
  static validateCreateRequest(data: any): data is CreateCalendarConfigRequest {
    return (
      data &&
      typeof data === 'object' &&
      data.date instanceof Date &&
      !isNaN(data.date.getTime()) &&
      typeof data.hasRun === 'boolean'
    );
  }

  static validateUpdateRequest(data: any): data is UpdateCalendarConfigRequest {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.hasRun === 'boolean'
    );
  }

  static validateDate(date: Date): boolean {
    return date instanceof Date && !isNaN(date.getTime());
  }

  static validateDateString(dateString: string): boolean {
    const date = new Date(dateString);
    return !isNaN(date.getTime()) && dateString === date.toISOString().split('T')[0];
  }

  static parseDateString(dateString: string): Date | null {
    try {
      const date = new Date(dateString + 'T00:00:00.000Z');
      return isNaN(date.getTime()) ? null : date;
    } catch {
      return null;
    }
  }

  static formatDateForDatabase(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  static formatDateForFrontend(date: Date): string {
    return date.toISOString().split('T')[0];
  }
}