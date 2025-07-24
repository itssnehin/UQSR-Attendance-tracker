import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import AttendanceHistory from './AttendanceHistory';
import apiService from '../../services/apiService';

// Mock the API service
jest.mock('../../services/apiService', () => ({
  getAttendanceHistory: jest.fn(),
}));

describe('AttendanceHistory', () => {
  const mockHistoryData = [
    {
      id: 1,
      runDate: '2025-07-22',
      runnerName: 'John Doe',
      registeredAt: '2025-07-22T10:00:00Z',
      sessionId: 'session1'
    },
    {
      id: 2,
      runDate: '2025-07-22',
      runnerName: 'Jane Smith',
      registeredAt: '2025-07-22T10:05:00Z',
      sessionId: 'session1'
    },
    {
      id: 3,
      runDate: '2025-07-23',
      runnerName: 'Bob Johnson',
      registeredAt: '2025-07-23T10:00:00Z',
      sessionId: 'session2'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (apiService.getAttendanceHistory as jest.Mock).mockResolvedValue(mockHistoryData);
  });

  test('renders loading state initially', () => {
    render(<AttendanceHistory />);
    expect(screen.getByText('Loading attendance history...')).toBeInTheDocument();
  });

  test('renders attendance history data after loading', async () => {
    render(<AttendanceHistory />);
    
    await waitFor(() => {
      expect(screen.queryByText('Loading attendance history...')).not.toBeInTheDocument();
    });
    
    // Check for dates
    expect(screen.getByText(/7\/23\/2025/)).toBeInTheDocument(); // Format may vary by locale
    expect(screen.getByText(/7\/22\/2025/)).toBeInTheDocument();
    
    // Check for counts
    expect(screen.getByText('1 runners')).toBeInTheDocument();
    expect(screen.getByText('2 runners')).toBeInTheDocument();
    
    // Check for names
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    expect(screen.getByText('John Doe, Jane Smith')).toBeInTheDocument();
  });

  test('shows error message when API call fails', async () => {
    (apiService.getAttendanceHistory as jest.Mock).mockRejectedValue(new Error('API error'));
    
    render(<AttendanceHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load attendance history')).toBeInTheDocument();
    });
  });

  test('shows no data message when API returns empty array', async () => {
    (apiService.getAttendanceHistory as jest.Mock).mockResolvedValue([]);
    
    render(<AttendanceHistory />);
    
    await waitFor(() => {
      expect(screen.getByText('No attendance data available for the selected period')).toBeInTheDocument();
    });
  });

  test('changes date range when buttons are clicked', async () => {
    render(<AttendanceHistory />);
    
    await waitFor(() => {
      expect(apiService.getAttendanceHistory).toHaveBeenCalledTimes(1);
    });
    
    // Click 14 days button
    fireEvent.click(screen.getByText('14 Days'));
    
    await waitFor(() => {
      expect(apiService.getAttendanceHistory).toHaveBeenCalledTimes(2);
    });
    
    // Click 30 days button
    fireEvent.click(screen.getByText('30 Days'));
    
    await waitFor(() => {
      expect(apiService.getAttendanceHistory).toHaveBeenCalledTimes(3);
    });
  });

  test('refreshes data when refresh button is clicked', async () => {
    render(<AttendanceHistory />);
    
    await waitFor(() => {
      expect(apiService.getAttendanceHistory).toHaveBeenCalledTimes(1);
    });
    
    // Click refresh button
    fireEvent.click(screen.getByText('Refresh Data'));
    
    await waitFor(() => {
      expect(apiService.getAttendanceHistory).toHaveBeenCalledTimes(2);
    });
  });
});