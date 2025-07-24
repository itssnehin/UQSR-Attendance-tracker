import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import QRCodeDisplay from './QRCodeDisplay';
import apiService from '../../services/apiService';
import { useAppContext } from '../../context';

// Mock the context hook
jest.mock('../../context', () => ({
  useAppContext: jest.fn(),
}));

// Mock the API service
jest.mock('../../services/apiService', () => ({
  getQRCode: jest.fn(),
}));

// Mock window.print
const mockPrint = jest.fn();
window.print = mockPrint;

describe('QRCodeDisplay', () => {
  const mockUseAppContext = useAppContext as jest.Mock;
  const mockQRCode = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation for context
    mockUseAppContext.mockReturnValue({
      state: {
        todaySessionId: 'test-session-123',
        todayHasRun: true,
      },
    });
    
    // Default mock implementation for API
    (apiService.getQRCode as jest.Mock).mockResolvedValue({
      qr_code: mockQRCode,
      session_id: 'test-session-123',
    });
  });

  test('renders loading state initially', () => {
    render(<QRCodeDisplay />);
    expect(screen.getByText('Loading QR code...')).toBeInTheDocument();
  });

  test('renders QR code after loading', async () => {
    render(<QRCodeDisplay />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading QR code...')).not.toBeInTheDocument();
    });
    
    // Check for QR code image
    const qrImage = screen.getByAltText('QR Code for today\'s run');
    expect(qrImage).toBeInTheDocument();
    expect(qrImage).toHaveAttribute('src', `data:image/png;base64,${mockQRCode}`);
    
    // Check for session ID
    expect(screen.getByText(/Session ID:/)).toBeInTheDocument();
    expect(screen.getByText(/test-session-123/)).toBeInTheDocument();
    
    // Check for date
    expect(screen.getByText(/Date:/)).toBeInTheDocument();
    
    // Check for instructions
    expect(screen.getByText(/Scan this QR code to register your attendance for today's run/)).toBeInTheDocument();
  });

  test('shows error message when API call fails', async () => {
    (apiService.getQRCode as jest.Mock).mockRejectedValue(new Error('API error'));
    
    render(<QRCodeDisplay />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load QR code')).toBeInTheDocument();
    });
  });

  test('shows no run message when no run is scheduled', async () => {
    mockUseAppContext.mockReturnValue({
      state: {
        todaySessionId: null,
        todayHasRun: false,
      },
    });
    
    render(<QRCodeDisplay />);
    
    await waitFor(() => {
      expect(screen.getByText('No run scheduled for today')).toBeInTheDocument();
    });
  });

  test('refreshes QR code when refresh button is clicked', async () => {
    render(<QRCodeDisplay />);
    
    await waitFor(() => {
      expect(apiService.getQRCode).toHaveBeenCalledTimes(1);
    });
    
    // Click refresh button
    fireEvent.click(screen.getByText('Refresh QR Code'));
    
    await waitFor(() => {
      expect(apiService.getQRCode).toHaveBeenCalledTimes(2);
    });
  });

  test('calls window.print when print button is clicked', async () => {
    render(<QRCodeDisplay />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading QR code...')).not.toBeInTheDocument();
    });
    
    // Click print button
    fireEvent.click(screen.getByText('Print QR Code'));
    
    expect(mockPrint).toHaveBeenCalledTimes(1);
  });

  test('sets up auto-refresh interval', () => {
    jest.useFakeTimers();
    
    render(<QRCodeDisplay refreshInterval={60000} />);
    
    // Fast-forward time
    jest.advanceTimersByTime(60000);
    
    expect(apiService.getQRCode).toHaveBeenCalledTimes(2);
    
    // Fast-forward time again
    jest.advanceTimersByTime(60000);
    
    expect(apiService.getQRCode).toHaveBeenCalledTimes(3);
    
    jest.useRealTimers();
  });
});