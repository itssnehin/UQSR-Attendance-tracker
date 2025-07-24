import React from 'react';
import { render, screen, act } from '@testing-library/react';
import AttendanceCounter from './AttendanceCounter';
import { useAppContext } from '../../context';
import socketService from '../../services/socketService';

// Mock the context hook
jest.mock('../../context', () => ({
  useAppContext: jest.fn(),
}));

// Mock the socket service
jest.mock('../../services/socketService', () => ({
  on: jest.fn(),
  off: jest.fn(),
}));

describe('AttendanceCounter', () => {
  const mockUseAppContext = useAppContext as jest.Mock;
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation
    mockUseAppContext.mockReturnValue({
      state: {
        currentAttendance: 10,
        isConnected: true,
      },
    });
  });

  test('renders attendance count from context', () => {
    render(<AttendanceCounter />);
    
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('Today\'s Attendance')).toBeInTheDocument();
  });

  test('shows connected status when socket is connected', () => {
    render(<AttendanceCounter />);
    
    expect(screen.getByText('Live Updates Active')).toBeInTheDocument();
  });

  test('shows disconnected status when socket is not connected', () => {
    mockUseAppContext.mockReturnValue({
      state: {
        currentAttendance: 10,
        isConnected: false,
      },
    });
    
    render(<AttendanceCounter />);
    
    expect(screen.getByText('Reconnecting...')).toBeInTheDocument();
  });

  test('registers socket event listeners on mount', () => {
    render(<AttendanceCounter />);
    
    expect(socketService.on).toHaveBeenCalledWith(
      'registration_success',
      expect.any(Function)
    );
  });

  test('removes socket event listeners on unmount', () => {
    const { unmount } = render(<AttendanceCounter />);
    unmount();
    
    expect(socketService.off).toHaveBeenCalledWith('registration_success');
  });

  test('updates recent attendees list when receiving registration event', () => {
    // Setup
    let registrationCallback: Function;
    (socketService.on as jest.Mock).mockImplementation((event, callback) => {
      if (event === 'registration_success') {
        registrationCallback = callback;
      }
    });
    
    render(<AttendanceCounter />);
    
    // Simulate receiving a registration event
    act(() => {
      registrationCallback({ count: 11, runner_name: 'John Doe' });
    });
    
    // Check that the attendee was added to the list
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  test('limits recent attendees list to 5 entries', () => {
    // Setup
    let registrationCallback: Function;
    (socketService.on as jest.Mock).mockImplementation((event, callback) => {
      if (event === 'registration_success') {
        registrationCallback = callback;
      }
    });
    
    render(<AttendanceCounter />);
    
    // Simulate receiving 6 registration events
    act(() => {
      registrationCallback({ count: 11, runner_name: 'Runner 1' });
      registrationCallback({ count: 12, runner_name: 'Runner 2' });
      registrationCallback({ count: 13, runner_name: 'Runner 3' });
      registrationCallback({ count: 14, runner_name: 'Runner 4' });
      registrationCallback({ count: 15, runner_name: 'Runner 5' });
      registrationCallback({ count: 16, runner_name: 'Runner 6' });
    });
    
    // Check that only the 5 most recent attendees are shown
    expect(screen.getByText('Runner 6')).toBeInTheDocument();
    expect(screen.getByText('Runner 5')).toBeInTheDocument();
    expect(screen.getByText('Runner 4')).toBeInTheDocument();
    expect(screen.getByText('Runner 3')).toBeInTheDocument();
    expect(screen.getByText('Runner 2')).toBeInTheDocument();
    expect(screen.queryByText('Runner 1')).not.toBeInTheDocument(); // This one should be removed
  });
});