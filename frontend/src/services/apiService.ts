import { RegistrationRequest, AttendanceResponse, CalendarDay } from '../types/index';

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  retryCondition?: (error: Error) => boolean;
}

interface RequestOptions extends RequestInit {
  retry?: RetryOptions;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class NetworkError extends Error {
  constructor(message: string = 'Network connection failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

class ApiService {
  private readonly baseUrl: string;
  private readonly defaultRetryOptions: RetryOptions = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    retryCondition: (error: Error) => {
      // Retry on network errors and 5xx server errors
      if (error instanceof NetworkError) return true;
      if (error instanceof ApiError) {
        return error.status ? error.status >= 500 : false;
      }
      return false;
    }
  };

  constructor() {
    // Use window.location.origin as fallback if environment variable is not available
    this.baseUrl = (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) 
      ? process.env.REACT_APP_API_URL 
      : 'http://localhost:8000';
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateDelay(attempt: number, baseDelay: number, maxDelay: number): number {
    // Exponential backoff with jitter
    const exponentialDelay = baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 0.1 * exponentialDelay;
    return Math.min(exponentialDelay + jitter, maxDelay);
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { retry, ...fetchOptions } = options;
    const retryOptions = { ...this.defaultRetryOptions, ...retry };
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      ...fetchOptions,
    };

    let lastError: Error = new Error('Unknown error');

    for (let attempt = 0; attempt <= retryOptions.maxRetries!; attempt++) {
      try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
          const errorMessage = await this.getErrorMessage(response);
          throw new ApiError(
            errorMessage || `HTTP error! status: ${response.status}`,
            response.status,
            response.status.toString()
          );
        }

        return await response.json();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        // Convert fetch errors to NetworkError
        if (lastError.name === 'TypeError' && lastError.message.includes('fetch')) {
          lastError = new NetworkError('Network connection failed');
        }

        // Don't retry on the last attempt or if retry condition is not met
        if (attempt === retryOptions.maxRetries || !retryOptions.retryCondition!(lastError)) {
          break;
        }

        // Calculate delay and wait before retry
        const delay = this.calculateDelay(attempt, retryOptions.baseDelay!, retryOptions.maxDelay!);
        console.warn(`API request failed (attempt ${attempt + 1}/${retryOptions.maxRetries! + 1}), retrying in ${delay}ms:`, lastError.message);
        await this.sleep(delay);
      }
    }

    console.error('API request failed after all retries:', lastError);
    throw lastError;
  }

  private async getErrorMessage(response: Response): Promise<string> {
    try {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        return errorData.message || errorData.detail || 'Request failed';
      } else {
        return await response.text() || `HTTP ${response.status} error`;
      }
    } catch {
      return `HTTP ${response.status} error`;
    }
  }

  // Calendar endpoints
  async getCalendar(): Promise<CalendarDay[]> {
    return this.request<CalendarDay[]>('/api/calendar');
  }

  async configureCalendar(day: CalendarDay): Promise<void> {
    return this.request<void>('/api/calendar/configure', {
      method: 'POST',
      body: JSON.stringify({
        date: day.date,
        has_run: day.hasRun
      }),
    });
  }

  async configureRunDay(date: Date, hasRun: boolean): Promise<void> {
    const dateString = date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    return this.request<void>('/api/calendar/configure', {
      method: 'POST',
      body: JSON.stringify({
        date: dateString,
        has_run: hasRun
      }),
    });
  }

  async getTodayStatus(): Promise<{
    success: boolean;
    has_run_today: boolean;
    session_id: string | null;
    attendance_count: number;
    message: string;
  }> {
    return this.request<{
      success: boolean;
      has_run_today: boolean;
      session_id: string | null;
      attendance_count: number;
      message: string;
    }>('/api/calendar/today');
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
    const url = `${this.baseUrl}/api/attendance/export${query}`;
    
    // Use custom fetch for blob response with retry logic
    const retryOptions = { ...this.defaultRetryOptions };
    let lastError: Error = new Error('Unknown error');

    for (let attempt = 0; attempt <= retryOptions.maxRetries!; attempt++) {
      try {
        const response = await fetch(url);
        
        if (!response.ok) {
          const errorMessage = await this.getErrorMessage(response);
          throw new ApiError(
            errorMessage || `Export failed! status: ${response.status}`,
            response.status,
            response.status.toString()
          );
        }
        
        return response.blob();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        // Convert fetch errors to NetworkError
        if (lastError.name === 'TypeError' && lastError.message.includes('fetch')) {
          lastError = new NetworkError('Network connection failed');
        }

        // Don't retry on the last attempt or if retry condition is not met
        if (attempt === retryOptions.maxRetries || !retryOptions.retryCondition!(lastError)) {
          break;
        }

        // Calculate delay and wait before retry
        const delay = this.calculateDelay(attempt, retryOptions.baseDelay!, retryOptions.maxDelay!);
        console.warn(`Export request failed (attempt ${attempt + 1}/${retryOptions.maxRetries! + 1}), retrying in ${delay}ms:`, lastError.message);
        await this.sleep(delay);
      }
    }

    console.error('Export request failed after all retries:', lastError);
    throw lastError;
  }
}

export default new ApiService();