import { 
  CalendarConfigValidator, 
  CreateCalendarConfigRequest, 
  UpdateCalendarConfigRequest 
} from '../CalendarConfig';

describe('CalendarConfig Model', () => {
  describe('CalendarConfigValidator', () => {
    describe('validateCreateRequest', () => {
      it('should validate valid create request', () => {
        const validRequest: CreateCalendarConfigRequest = {
          date: new Date('2024-01-15'),
          hasRun: true,
        };

        expect(CalendarConfigValidator.validateCreateRequest(validRequest)).toBe(true);
      });

      it('should validate create request with hasRun false', () => {
        const validRequest: CreateCalendarConfigRequest = {
          date: new Date('2024-01-15'),
          hasRun: false,
        };

        expect(CalendarConfigValidator.validateCreateRequest(validRequest)).toBe(true);
      });

      it('should reject request with invalid date', () => {
        const invalidRequest = {
          date: 'invalid-date',
          hasRun: true,
        };

        expect(CalendarConfigValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with NaN date', () => {
        const invalidRequest = {
          date: new Date('invalid'),
          hasRun: true,
        };

        expect(CalendarConfigValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with non-boolean hasRun', () => {
        const invalidRequest = {
          date: new Date('2024-01-15'),
          hasRun: 'true',
        };

        expect(CalendarConfigValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with missing hasRun', () => {
        const invalidRequest = {
          date: new Date('2024-01-15'),
        };

        expect(CalendarConfigValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject null or undefined request', () => {
        expect(CalendarConfigValidator.validateCreateRequest(null)).toBe(false);
        expect(CalendarConfigValidator.validateCreateRequest(undefined)).toBe(false);
      });
    });

    describe('validateUpdateRequest', () => {
      it('should validate valid update request', () => {
        const validRequest: UpdateCalendarConfigRequest = {
          hasRun: true,
        };

        expect(CalendarConfigValidator.validateUpdateRequest(validRequest)).toBe(true);
      });

      it('should validate update request with hasRun false', () => {
        const validRequest: UpdateCalendarConfigRequest = {
          hasRun: false,
        };

        expect(CalendarConfigValidator.validateUpdateRequest(validRequest)).toBe(true);
      });

      it('should reject request with non-boolean hasRun', () => {
        const invalidRequest = {
          hasRun: 'false',
        };

        expect(CalendarConfigValidator.validateUpdateRequest(invalidRequest)).toBe(false);
      });

      it('should reject null or undefined request', () => {
        expect(CalendarConfigValidator.validateUpdateRequest(null)).toBe(false);
        expect(CalendarConfigValidator.validateUpdateRequest(undefined)).toBe(false);
      });
    });

    describe('validateDate', () => {
      it('should validate valid dates', () => {
        expect(CalendarConfigValidator.validateDate(new Date())).toBe(true);
        expect(CalendarConfigValidator.validateDate(new Date('2024-01-15'))).toBe(true);
        expect(CalendarConfigValidator.validateDate(new Date('2023-12-31'))).toBe(true);
      });

      it('should reject invalid dates', () => {
        expect(CalendarConfigValidator.validateDate(new Date('invalid'))).toBe(false);
        expect(CalendarConfigValidator.validateDate(new Date('2024-13-01'))).toBe(false);
      });

      it('should reject non-date values', () => {
        expect(CalendarConfigValidator.validateDate('2024-01-15' as any)).toBe(false);
        expect(CalendarConfigValidator.validateDate(null as any)).toBe(false);
        expect(CalendarConfigValidator.validateDate(undefined as any)).toBe(false);
      });
    });

    describe('validateDateString', () => {
      it('should validate valid date strings', () => {
        expect(CalendarConfigValidator.validateDateString('2024-01-15')).toBe(true);
        expect(CalendarConfigValidator.validateDateString('2023-12-31')).toBe(true);
        expect(CalendarConfigValidator.validateDateString('2024-02-29')).toBe(true); // Leap year
      });

      it('should reject invalid date strings', () => {
        expect(CalendarConfigValidator.validateDateString('invalid-date')).toBe(false);
        expect(CalendarConfigValidator.validateDateString('2024-13-01')).toBe(false);
        expect(CalendarConfigValidator.validateDateString('2024-02-30')).toBe(false);
        expect(CalendarConfigValidator.validateDateString('2023-02-29')).toBe(false); // Not leap year
      });

      it('should reject malformed date strings', () => {
        expect(CalendarConfigValidator.validateDateString('24-01-15')).toBe(false);
        expect(CalendarConfigValidator.validateDateString('2024/01/15')).toBe(false);
        expect(CalendarConfigValidator.validateDateString('15-01-2024')).toBe(false);
      });
    });

    describe('parseDateString', () => {
      it('should parse valid date strings', () => {
        const result = CalendarConfigValidator.parseDateString('2024-01-15');
        expect(result).toBeInstanceOf(Date);
        expect(result?.getFullYear()).toBe(2024);
        expect(result?.getMonth()).toBe(0); // January is 0
        expect(result?.getDate()).toBe(15);
      });

      it('should return null for invalid date strings', () => {
        expect(CalendarConfigValidator.parseDateString('invalid-date')).toBeNull();
        expect(CalendarConfigValidator.parseDateString('2024-13-01')).toBeNull();
        expect(CalendarConfigValidator.parseDateString('2024-02-30')).toBeNull();
      });

      it('should handle edge cases', () => {
        expect(CalendarConfigValidator.parseDateString('')).toBeNull();
        expect(CalendarConfigValidator.parseDateString('2024-02-29')).toBeInstanceOf(Date); // Leap year
        expect(CalendarConfigValidator.parseDateString('2023-02-29')).toBeNull(); // Not leap year
      });
    });

    describe('formatDateForDatabase', () => {
      it('should format dates correctly for database', () => {
        const date = new Date('2024-01-15T10:30:00.000Z');
        expect(CalendarConfigValidator.formatDateForDatabase(date)).toBe('2024-01-15');
      });

      it('should handle different timezones consistently', () => {
        const date = new Date('2024-01-15T23:59:59.999Z');
        expect(CalendarConfigValidator.formatDateForDatabase(date)).toBe('2024-01-15');
      });

      it('should handle edge dates', () => {
        const newYear = new Date('2024-01-01T00:00:00.000Z');
        expect(CalendarConfigValidator.formatDateForDatabase(newYear)).toBe('2024-01-01');

        const newYearEve = new Date('2023-12-31T23:59:59.999Z');
        expect(CalendarConfigValidator.formatDateForDatabase(newYearEve)).toBe('2023-12-31');
      });
    });

    describe('formatDateForFrontend', () => {
      it('should format dates correctly for frontend', () => {
        const date = new Date('2024-01-15T10:30:00.000Z');
        expect(CalendarConfigValidator.formatDateForFrontend(date)).toBe('2024-01-15');
      });

      it('should be consistent with database format', () => {
        const date = new Date('2024-01-15T10:30:00.000Z');
        const dbFormat = CalendarConfigValidator.formatDateForDatabase(date);
        const frontendFormat = CalendarConfigValidator.formatDateForFrontend(date);
        expect(dbFormat).toBe(frontendFormat);
      });
    });
  });
});