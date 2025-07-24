import { RegistrationRequest, AttendanceResponse, CalendarDay } from '../types';

class ApiService {
  private readonly baseUrl: string;

  constructor() {
    // Use window.location.origin as fallback if environment variable is not available
    this.baseUrl = (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) 
      ? process.env.REACT_APP_API_URL 
      : 'http://localhost:8000';
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Calendar endpoints
  async getCalendar(): Promise<CalendarDay[]> {
    return this.request<CalendarDay[]>('/api/calendar');
  }

  async configureCalendar(days: CalendarDay[]): Promise<void> {
    return this.request<void>('/api/calendar/configure', {
      method: 'POST',
      body: JSON.stringify(days),
    });
  }

  async getTodayStatus(): Promise<CalendarDay> {
    return this.request<CalendarDay>('/api/calendar/today');
  }

  // Registration endpoints
  async registerAttendance(data: RegistrationRequest): Promise<AttendanceResponse> {
    return this.request<AttendanceResponse>('/api/register', {
      method: 'POST',
      body: JSON.stringify({
        session_id: data.sessionId,
        runner_name: data.runnerName,
        timestamp: data.timestamp.toISOString(),
      }),
    });
  }

  async getTodayAttendance(): Promise<{ count: number; attendees: string[] }> {
    return this.request<{ count: number; attendees: string[] }>('/api/attendance/today');
  }

  async getAttendanceHistory(startDate?: string, endDate?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<any[]>(`/api/attendance/history${query}`);
  }

  // QR Code endpoints
  async getQRCode(sessionId: string): Promise<{ qr_code: string; session_id: string }> {
    return this.request<{ qr_code: string; session_id: string }>(`/api/qr/${sessionId}`);
  }

  async validateQRCode(token: string): Promise<{ valid: boolean; session_id?: string }> {
    return this.request<{ valid: boolean; session_id?: string }>(`/api/qr/validate/${token}`);
  }

  // Export endpoints
  async exportAttendance(startDate?: string, endDate?: string): Promise<Blob> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`${this.baseUrl}/api/attendance/export${query}`);
    
    if (!response.ok) {
      throw new Error(`Export failed! status: ${response.status}`);
    }
    
    return response.blob();
  }
}

export default new ApiService();