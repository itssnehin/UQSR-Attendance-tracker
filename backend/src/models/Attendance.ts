export interface Attendance {
  id: number;
  runId: number;
  runnerName: string;
  registeredAt: Date;
}

export interface CreateAttendanceRequest {
  runId: number;
  runnerName: string;
}

export interface AttendanceWithRunInfo extends Attendance {
  runDate: Date;
  sessionId: string;
}

export interface AttendanceSummary {
  date: Date;
  totalAttendees: number;
  attendees: string[];
}

export class AttendanceValidator {
  static validateCreateRequest(data: any): data is CreateAttendanceRequest {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.runId === 'number' &&
      data.runId > 0 &&
      typeof data.runnerName === 'string' &&
      data.runnerName.trim().length > 0 &&
      data.runnerName.length <= 255
    );
  }

  static validateRunnerName(name: string): boolean {
    if (typeof name !== 'string') return false;
    
    const trimmedName = name.trim();
    return (
      trimmedName.length > 0 &&
      trimmedName.length <= 255 &&
      /^[a-zA-Z\s\-'\.]+$/.test(trimmedName) // Allow letters, spaces, hyphens, apostrophes, and periods
    );
  }

  static sanitizeRunnerName(name: string): string {
    return name.trim().replace(/\s+/g, ' '); // Remove extra whitespace
  }

  static validateRunId(runId: number): boolean {
    return typeof runId === 'number' && runId > 0 && Number.isInteger(runId);
  }
}