import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Calendar from './Calendar';
import AppProvider from '../../context/AppProvider';
import apiService from '../../services/apiService';
import { CalendarDay } from '../../types';

// Mock the API service
jest.mock('../../services/apiService');
const mockedApiService = apiService as jest.Mocked<typeof apiService>;

// Mock date utilities to have consistent test results
jest.mock('../../utils/dateUtils', () => ({
  ...jest.requireActual('../../utils/dateUtils'),
  isToday: (date: Date | string) => {
    const d = typeof date === 'string' ? new Date(date) : date;
    // Mock today as 2024-01-15 for consistent testing
    return d.getDate() === 15 && d.getMonth() === 0 && d.getFullYear() === 2024;
  },
  isSameDay: (date1: Date | string, date2: Date | string) => {
    const d1 = typeof date1 === 'string' ? new Date(date1) : date1;
    const d2 = typeof date2 === 'string' ? new Date(date2) : date2;
    return (
      d1.getDate() === d2.getDate() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getFullYear() === d2.getFullYear()
    );
  }
}));

const mockCalendarData: CalendarDay[] = [
  {
    date: '2024-01-01',
    hasRun: true,
    attendanceCount: 5
  },
  {
    date: '2024-01-03',
    hasRun: true,
    attendanceCount: 8
  },
  {
    date: '2024-01-15',
    hasRun: false,
    attendanceCount: 0
  }
];

const renderCalendarWithProvider = (props = {}) => {
  return render(
    <AppProvider>
      <Calendar {...props} />
    </AppProvider>
  );
};

describe('Calendar Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedApiService.getCalendar.mockResolvedValue(mockCalendarData);
    mockedApiService.configureCalendar.mockResolvedValue();
  });

  describe('Rendering', () => {
    it('renders calendar with correct month and year', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
    });

    it('renders day headers correctly', async () => {
      renderCalendarWithProvider();
      
      const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      dayHeaders.forEach(day => {
        expect(screen.getByText(day)).toBeInTheDocument();
      });
    });

    it('renders navigation buttons', async () => {
      renderCalendarWithProvider();
      
      expect(screen.getByText('←')).toBeInTheDocument();
      expect(screen.getByText('→')).toBeInTheDocument();
    });

    it('renders legend correctly', async () => {
      renderCalendarWithProvider();
      
      expect(screen.getByText('Run Day')).toBeInTheDocument();
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Selected')).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    it('loads calendar data on mount', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(mockedApiService.getCalendar).toHaveBeenCalledTimes(1);
      });
    });

    it('displays loading state while fetching data', async () => {
      mockedApiService.getCalendar.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockCalendarData), 100))
      );
      
      renderCalendarWithProvider();
      
      expect(screen.getByText('Loading...')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      });
    });

    it('handles API errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      mockedApiService.getCalendar.mockRejectedValue(new Error('API Error'));
      
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Error loading calendar:', expect.any(Error));
      });
      
      consoleError.mockRestore();
    });
  });

  describe('Calendar Navigation', () => {
    it('navigates to previous month when left arrow is clicked', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('←'));
      
      await waitFor(() => {
        expect(mockedApiService.getCalendar).toHaveBeenCalledTimes(2);
      });
    });

    it('navigates to next month when right arrow is clicked', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('→'));
      
      await waitFor(() => {
        expect(mockedApiService.getCalendar).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Day Selection and Toggling', () => {
    it('toggles run day status when clicking on a date', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on day 10 (which should not be a run day initially)
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Should show save/reset buttons
      await waitFor(() => {
        expect(screen.getByText('Save Changes')).toBeInTheDocument();
        expect(screen.getByText('Reset')).toBeInTheDocument();
      });
    });

    it('shows visual indicators for run days', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        // Day 1 should have run indicator (🏃)
        const day1 = screen.getByText('1').closest('.calendar-day');
        expect(day1).toHaveClass('run-day');
      });
    });

    it('shows attendance count for days with attendance', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        // Day 1 should show attendance count of 5
        expect(screen.getByText('5')).toBeInTheDocument();
        // Day 3 should show attendance count of 8
        expect(screen.getByText('8')).toBeInTheDocument();
      });
    });

    it('highlights today with special styling', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        // Day 15 should be highlighted as today
        const day15 = screen.getByText('15').closest('.calendar-day');
        expect(day15).toHaveClass('today');
      });
    });
    
    it('shows selected date info when a date is clicked', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on day 1 (which is a run day)
      const day1 = screen.getByText('1');
      fireEvent.click(day1);
      
      // Should show selected date info
      await waitFor(() => {
        expect(screen.getByText('Selected Date: Jan 1, 2024')).toBeInTheDocument();
        expect(screen.getByText(/Status: Run Day/)).toBeInTheDocument();
      });
    });
    
    it('applies selected class to the clicked date', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on day 10
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Day 10 should have selected class
      expect(day10.closest('.calendar-day')).toHaveClass('selected');
    });
    
    it('handles keyboard navigation for accessibility', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Find day 10 and trigger Enter key
      const day10 = screen.getByText('10').closest('.calendar-day');
      if (day10) {
        fireEvent.keyDown(day10, { key: 'Enter' });
      }
      
      // Should show save/reset buttons
      await waitFor(() => {
        expect(screen.getByText('Save Changes')).toBeInTheDocument();
        expect(screen.getByText('Reset')).toBeInTheDocument();
      });
    });
  });

  describe('Save and Reset Functionality', () => {
    it('saves changes when save button is clicked', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on a day to make changes
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Click save button
      const saveButton = await screen.findByText('Save Changes');
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(mockedApiService.configureCalendar).toHaveBeenCalledTimes(1);
      });
    });

    it('resets changes when reset button is clicked', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on a day to make changes
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Click reset button
      const resetButton = await screen.findByText('Reset');
      fireEvent.click(resetButton);
      
      // Save/Reset buttons should disappear
      await waitFor(() => {
        expect(screen.queryByText('Save Changes')).not.toBeInTheDocument();
        expect(screen.queryByText('Reset')).not.toBeInTheDocument();
      });
    });

    it('shows saving state during save operation', async () => {
      mockedApiService.configureCalendar.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 100))
      );
      
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on a day to make changes
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Click save button
      const saveButton = await screen.findByText('Save Changes');
      fireEvent.click(saveButton);
      
      // Should show saving state
      expect(screen.getByText('Saving...')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
      });
    });

    it('handles save errors gracefully', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      mockedApiService.configureCalendar.mockRejectedValue(new Error('Save failed'));
      
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on a day to make changes
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Click save button
      const saveButton = await screen.findByText('Save Changes');
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Error saving calendar:', expect.any(Error));
      });
      
      consoleError.mockRestore();
    });
  });

  describe('Callback Functions', () => {
    it('calls onSave callback when save is successful', async () => {
      const onSaveMock = jest.fn();
      renderCalendarWithProvider({ onSave: onSaveMock });
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      // Click on a day to make changes
      const day10 = screen.getByText('10');
      fireEvent.click(day10);
      
      // Click save button
      const saveButton = await screen.findByText('Save Changes');
      fireEvent.click(saveButton);
      
      await waitFor(() => {
        expect(onSaveMock).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper titles for calendar days', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        const day1 = screen.getByText('1').closest('.calendar-day');
        expect(day1).toHaveAttribute('title', expect.stringContaining('Jan 1, 2024'));
      });
    });

    it('disables navigation buttons during loading', async () => {
      mockedApiService.getCalendar.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve(mockCalendarData), 100))
      );
      
      renderCalendarWithProvider();
      
      const prevButton = screen.getByLabelText('Previous month');
      const nextButton = screen.getByLabelText('Next month');
      
      expect(prevButton).toBeDisabled();
      expect(nextButton).toBeDisabled();
      
      await waitFor(() => {
        expect(prevButton).not.toBeDisabled();
        expect(nextButton).not.toBeDisabled();
      });
    });
    
    it('has proper ARIA attributes for calendar days', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      const day1 = screen.getByText('1').closest('.calendar-day');
      expect(day1).toHaveAttribute('aria-label', expect.stringContaining('Jan 1, 2024 - Run Day'));
      expect(day1).toHaveAttribute('role', 'gridcell');
      
      const day15 = screen.getByText('15').closest('.calendar-day');
      expect(day15).toHaveAttribute('aria-label', expect.stringContaining('(Today)'));
    });
    
    it('supports keyboard navigation', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      const day10 = screen.getByText('10').closest('.calendar-day');
      expect(day10).toHaveAttribute('tabIndex', '0');
      
      // Simulate keyboard interaction
      if (day10) {
        fireEvent.keyDown(day10, { key: 'Enter' });
      }
      
      await waitFor(() => {
        expect(screen.getByText('Save Changes')).toBeInTheDocument();
      });
    });
    
    it('provides accessible navigation buttons', async () => {
      renderCalendarWithProvider();
      
      await waitFor(() => {
        expect(screen.getByText('January 2024')).toBeInTheDocument();
      });
      
      const prevButton = screen.getByLabelText('Previous month');
      const nextButton = screen.getByLabelText('Next month');
      
      expect(prevButton).toBeInTheDocument();
      expect(nextButton).toBeInTheDocument();
    });
  });
});