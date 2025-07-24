import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import RunnerRegistration from './RunnerRegistration';
import AppProvider from '../../context/AppProvider';
import apiService from '../../services/apiService';
import { AttendanceResponse } from '../../types';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { describe } from 'node:test';

// Mock the API service
jest.mock('../../services/apiService');
const mockApiService = apiService as jest.Mocked<typeof apiService>;

// Mock socket service
jest.mock('../../services/socketService', () => ({
  connect: jest.fn(),
  disconnect: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
}));

// Mock react-router-dom hooks
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ sessionId: 'test-session-123' }),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
}));

// Mock getUserMedia for camera tests
const mockGetUserMedia = jest.fn();
Object.defineProperty(navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
  },
});

// Mock window.prompt for manual token input
const mockPrompt = jest.fn();
Object.defineProperty(window, 'prompt', {
  writable: true,
  value: mockPrompt,
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <AppProvider>
      {children}
    </AppProvider>
  </BrowserRouter>
);

describe('RunnerRegistration Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUserMedia.mockClear();
    mockPrompt.mockClear();
  });

  afterEach(() => {
    // Clean up any media streams
    if (mockGetUserMedia.mock.results.length > 0) {
      const stream = mockGetUserMedia.mock.results[0].value;
      if (stream && stream.getTracks) {
        stream.getTracks().forEach((track: any) => track.stop());
      }
    }
  });

  describe('Component Rendering', () => {
    it('renders registration form with all required fields', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      expect(screen.getByText('Runner Registration')).toBeInTheDocument();
      expect(screen.getByText('Register for today\'s social run')).toBeInTheDocument();
      expect(screen.getByLabelText('Session ID')).toBeInTheDocument();
      expect(screen.getByLabelText('Your Name')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register attendance/i })).toBeInTheDocument();
    });

    it('displays connection status', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      expect(screen.getByText(/connected|disconnected/i)).toBeInTheDocument();
    });

    it('pre-fills session ID from URL params', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const sessionInput = screen.getByLabelText('Session ID') as HTMLInputElement;
      expect(sessionInput.value).toBe('test-session-123');
    });

    it('shows camera and manual input buttons', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      expect(screen.getByTitle('Scan QR Code')).toBeInTheDocument();
      expect(screen.getByTitle('Enter manually')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('validates runner name is required', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      // Clear the input and trigger blur
      fireEvent.change(nameInput, { target: { value: '' } });
      fireEvent.blur(nameInput);

      expect(screen.getByText('Name is required')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });

    it('validates runner name minimum length', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      
      fireEvent.change(nameInput, { target: { value: 'A' } });
      fireEvent.blur(nameInput);

      expect(screen.getByText('Name must be at least 2 characters long')).toBeInTheDocument();
    });

    it('validates runner name contains only valid characters', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      
      fireEvent.change(nameInput, { target: { value: 'John123' } });
      fireEvent.blur(nameInput);

      expect(screen.getByText('Name can only contain letters, spaces, hyphens, and apostrophes')).toBeInTheDocument();
    });

    it('accepts valid runner names', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });
      
      fireEvent.change(nameInput, { target: { value: 'John Doe-Smith' } });
      fireEvent.blur(nameInput);

      expect(screen.queryByText(/Name must be/)).not.toBeInTheDocument();
      expect(submitButton).not.toBeDisabled();
    });

    it('validates session ID format', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const sessionInput = screen.getByLabelText('Session ID');
      
      fireEvent.change(sessionInput, { target: { value: 'invalid session!@#' } });
      fireEvent.blur(sessionInput);

      expect(screen.getByText('Invalid session ID format')).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const mockResponse: AttendanceResponse = {
        success: true,
        message: 'Registration successful!',
        currentCount: 5,
        runnerName: 'John Doe'
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockApiService.registerAttendance).toHaveBeenCalledWith({
          sessionId: 'test-session-123',
          runnerName: 'John Doe',
          timestamp: expect.any(Date)
        });
      });
    });

    it('displays success message on successful registration', async () => {
      const mockResponse: AttendanceResponse = {
        success: true,
        message: 'Registration successful!',
        currentCount: 5,
        runnerName: 'John Doe'
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Registration Successful!')).toBeInTheDocument();
        expect(screen.getByText('Registration successful!')).toBeInTheDocument();
        expect(screen.getByText(/Current attendance.*5/)).toBeInTheDocument();
      });
    });

    it('displays error message on failed registration', async () => {
      const mockResponse: AttendanceResponse = {
        success: false,
        message: 'Duplicate registration detected',
        currentCount: 0
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Duplicate registration detected')).toBeInTheDocument();
      });
    });

    it('handles network errors gracefully', async () => {
      mockApiService.registerAttendance.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('clears form after successful registration', async () => {
      const mockResponse: AttendanceResponse = {
        success: true,
        message: 'Registration successful!',
        currentCount: 5,
        runnerName: 'John Doe'
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name') as HTMLInputElement;
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Registration Successful!')).toBeInTheDocument();
      });

      expect(nameInput.value).toBe('');
    });
  });

  describe('QR Code Scanning', () => {
    it('opens camera when scan button is clicked', async () => {
      const mockStream = {
        getTracks: jest.fn(() => [{ stop: jest.fn() }])
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const scanButton = screen.getByTitle('Scan QR Code');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(mockGetUserMedia).toHaveBeenCalledWith({
          video: { facingMode: 'environment' }
        });
        expect(screen.getByText('Scan QR Code')).toBeInTheDocument();
      });
    });

    it('handles camera access denial', async () => {
      mockGetUserMedia.mockRejectedValue(new Error('Permission denied'));

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const scanButton = screen.getByTitle('Scan QR Code');
      fireEvent.click(scanButton);

      await waitFor(() => {
        expect(screen.getByText(/camera access denied or not available/i)).toBeInTheDocument();
      });
    });
  });

  describe('Manual Token Input', () => {
    it('opens prompt when manual input button is clicked', () => {
      mockPrompt.mockReturnValue('manual-token-123');

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const manualButton = screen.getByTitle('Enter manually');
      fireEvent.click(manualButton);

      expect(mockPrompt).toHaveBeenCalledWith('Enter the QR code token or session ID:');
      
      const sessionInput = screen.getByLabelText('Session ID') as HTMLInputElement;
      expect(sessionInput.value).toBe('manual-token-123');
    });

    it('handles cancelled prompt', () => {
      mockPrompt.mockReturnValue(null);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const sessionInput = screen.getByLabelText('Session ID') as HTMLInputElement;
      const originalValue = sessionInput.value;
      
      const manualButton = screen.getByTitle('Enter manually');
      fireEvent.click(manualButton);

      expect(sessionInput.value).toBe(originalValue);
    });
  });

  describe('Try Again Functionality', () => {
    it('shows try again button after successful registration', async () => {
      const mockResponse: AttendanceResponse = {
        success: true,
        message: 'Registration successful!',
        currentCount: 5,
        runnerName: 'John Doe'
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Registration Successful!')).toBeInTheDocument();
      });

      expect(screen.getByText('Register Another Runner')).toBeInTheDocument();
    });

    it('resets form when try again button is clicked', async () => {
      const mockResponse: AttendanceResponse = {
        success: true,
        message: 'Registration successful!',
        currentCount: 5,
        runnerName: 'John Doe'
      };

      mockApiService.registerAttendance.mockResolvedValue(mockResponse);

      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      const submitButton = screen.getByRole('button', { name: /register attendance/i });

      fireEvent.change(nameInput, { target: { value: 'John Doe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Registration Successful!')).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByText('Register Another Runner');
      fireEvent.click(tryAgainButton);

      expect(screen.queryByText('Registration Successful!')).not.toBeInTheDocument();
      expect(screen.getByLabelText('Your Name')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register attendance/i })).toBeInTheDocument();
    });
  });

  describe('Input Sanitization', () => {
    it('sanitizes user input to prevent XSS', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name') as HTMLInputElement;
      
      fireEvent.change(nameInput, { target: { value: 'John<script>alert("xss")</script>Doe' } });

      expect(nameInput.value).toBe('JohnscriptalertxssscriptDoe');
    });

    it('trims whitespace from inputs', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name') as HTMLInputElement;
      
      fireEvent.change(nameInput, { target: { value: '  John Doe  ' } });

      expect(nameInput.value).toBe('John Doe');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      expect(screen.getByLabelText('Session ID')).toBeInTheDocument();
      expect(screen.getByLabelText('Your Name')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /register attendance/i })).toBeInTheDocument();
    });

    it('shows error messages with proper accessibility', () => {
      render(
        <TestWrapper>
          <RunnerRegistration />
        </TestWrapper>
      );

      const nameInput = screen.getByLabelText('Your Name');
      
      fireEvent.change(nameInput, { target: { value: '' } });
      fireEvent.blur(nameInput);

      const errorMessage = screen.getByText('Name is required');
      expect(errorMessage).toBeInTheDocument();
      expect(errorMessage).toHaveClass('error-text');
    });
  });
});