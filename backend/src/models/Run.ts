export interface Run {
  id: number;
  date: Date;
  sessionId: string;
  isActive: boolean;
  createdAt: Date;
}

export interface CreateRunRequest {
  date: Date;
  sessionId: string;
  isActive?: boolean;
}

export interface UpdateRunRequest {
  isActive?: boolean;
}

export interface RunWithAttendanceCount extends Run {
  attendanceCount: number;
}

export class RunValidator {
  static validateCreateRequest(data: any): data is CreateRunRequest {
    return (
      data &&
      typeof data === 'object' &&
      data.date instanceof Date &&
      typeof data.sessionId === 'string' &&
      data.sessionId.length > 0 &&
      (data.isActive === undefined || typeof data.isActive === 'boolean')
    );
  }

  static validateUpdateRequest(data: any): data is UpdateRunRequest {
    return (
      data &&
      typeof data === 'object' &&
      (data.isActive === undefined || typeof data.isActive === 'boolean')
    );
  }

  static validateSessionId(sessionId: string): boolean {
    return typeof sessionId === 'string' && sessionId.length > 0 && sessionId.length <= 255;
  }

  static validateDate(date: Date): boolean {
    return date instanceof Date && !isNaN(date.getTime());
  }
}