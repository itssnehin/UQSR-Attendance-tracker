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
    maxRetries: 1, // Reduce retries for faster response
    baseDelay: 500, // Reduce delay
    maxDelay: 2000, // Reduce max delay
    retryCondition: (error: Error) => {
      // Only retry on network errors, not server errors
      if (error instanceof NetworkError) return true;
      return false;
    }
  };

  constructor() {
    // Use production backend URL - ensure HTTPS
    let baseUrl = process.env.REACT_APP_API_URL || 'https://talented-intuition-production.up.railway.app';
    
    // Force HTTPS if HTTP is detected
    if (baseUrl.startsWith('http://')) {
      baseUrl = baseUrl.replace('http://', 'https://');
      console.warn('⚠️ Converted HTTP to HTTPS for security:', baseUrl);
    }
    
    this.baseUrl = baseUrl;
    console.log('🔧 API Service initialized with baseUrl:', this.baseUrl);
    console.log('🔧 Environment REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
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
    
    console.log(`🌐 API Request: ${fetchOptions.method || 'GET'} ${url}`);
    
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
        
        console.log(`📡 Response: ${response.status} ${response.statusText} for ${url}`);
        
        if (!response.ok) {
          const errorMessage = await this.getErrorMessage(response);
          const error = new ApiError(
            errorMessage || `HTTP error! status: ${response.status}`,
            response.status,
            response.status.toString()
          );
          console.error(`❌ API Error:`, error);
          throw error;
        }

        const data = await response.json();
        console.log(`✅ API Success:`, data);
        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
        
        // Convert fetch errors to NetworkError
        if (lastError.name === 'TypeError' && lastError.message.includes('fetch')) {
          lastError = new NetworkError('Network connection failed');
        }

        console.error(`❌ Request attempt ${attempt + 1} failed:`, lastError);

        // Don't retry on the last attempt or if retry condition is not met
        if (attempt === retryOptions.maxRetries || !retryOptions.retryCondition!(lastError)) {
          break;
        }

        // Calculate delay and wait before retry
        const delay = this.calculateDelay(attempt, retryOptions.baseDelay!, retryOptions.maxDelay!);
        console.warn(`🔄 Retrying in ${delay}ms...`);
        await this.sleep(delay);
      }
    }

    console.error('💥 API request failed after all retries:', lastError);
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
    const response = await this.request<{
      success: boolean;
      data: Array<{
        date: string;
        has_run: boolean;
        attendance_count: number;
        session_id: string;
      }>;
    }>('/api/calendar');
    
    // Transform backend response to frontend format
    return response.data.map(item => ({
      date: item.date,
      hasRun: item.has_run,
      attendanceCount: item.attendance_count,
      sessionId: item.session_id
    }));
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
    const response = await this.request<{
      success: boolean;
      count: number;
      has_run_today: boolean;
      session_id: string;
      message: string;
    }>('/api/attendance/today');
    
    // Transform backend response to frontend format
    return {
      count: response.count,
      attendees: [] // Backend doesn't return attendee names in this endpoint
    };
  }

  async getAttendanceHistory(startDate?: string, endDate?: string): Promise<any[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    const response = await this.request<{
      success: boolean;
      data: Array<{
        id: number;
        runner_name: string;
        registered_at: string;
        run_date: string;
        session_id: string;
      }>;
      total_count: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/api/attendance/history${query}`);
    
    // Transform backend response to frontend format
    return response.data.map(item => ({
      id: item.id,
      runnerName: item.runner_name,
      registeredAt: item.registered_at,
      runDate: item.run_date,
      sessionId: item.session_id
    }));
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