import { AttendanceValidator, CreateAttendanceRequest } from '../Attendance';

describe('Attendance Model', () => {
  describe('AttendanceValidator', () => {
    describe('validateCreateRequest', () => {
      it('should validate valid create request', () => {
        const validRequest: CreateAttendanceRequest = {
          runId: 1,
          runnerName: 'John Doe',
        };

        expect(AttendanceValidator.validateCreateRequest(validRequest)).toBe(true);
      });

      it('should reject request with invalid runId', () => {
        const invalidRequest = {
          runId: 0,
          runnerName: 'John Doe',
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with negative runId', () => {
        const invalidRequest = {
          runId: -1,
          runnerName: 'John Doe',
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with non-number runId', () => {
        const invalidRequest = {
          runId: '1',
          runnerName: 'John Doe',
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with empty runnerName', () => {
        const invalidRequest = {
          runId: 1,
          runnerName: '',
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with whitespace-only runnerName', () => {
        const invalidRequest = {
          runId: 1,
          runnerName: '   ',
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with runnerName too long', () => {
        const invalidRequest = {
          runId: 1,
          runnerName: 'a'.repeat(256),
        };

        expect(AttendanceValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject null or undefined request', () => {
        expect(AttendanceValidator.validateCreateRequest(null)).toBe(false);
        expect(AttendanceValidator.validateCreateRequest(undefined)).toBe(false);
      });
    });

    describe('validateRunnerName', () => {
      it('should validate valid runner names', () => {
        expect(AttendanceValidator.validateRunnerName('John Doe')).toBe(true);
        expect(AttendanceValidator.validateRunnerName('Mary-Jane Smith')).toBe(true);
        expect(AttendanceValidator.validateRunnerName("O'Connor")).toBe(true);
        expect(AttendanceValidator.validateRunnerName('Dr. Smith')).toBe(true);
        expect(AttendanceValidator.validateRunnerName('Jean-Luc')).toBe(true);
      });

      it('should reject names with invalid characters', () => {
        expect(AttendanceValidator.validateRunnerName('John123')).toBe(false);
        expect(AttendanceValidator.validateRunnerName('John@Doe')).toBe(false);
        expect(AttendanceValidator.validateRunnerName('John#Doe')).toBe(false);
        expect(AttendanceValidator.validateRunnerName('John$Doe')).toBe(false);
      });

      it('should reject empty or whitespace-only names', () => {
        expect(AttendanceValidator.validateRunnerName('')).toBe(false);
        expect(AttendanceValidator.validateRunnerName('   ')).toBe(false);
        expect(AttendanceValidator.validateRunnerName('\t\n')).toBe(false);
      });

      it('should reject names that are too long', () => {
        const longName = 'a'.repeat(256);
        expect(AttendanceValidator.validateRunnerName(longName)).toBe(false);
      });

      it('should accept names at max length', () => {
        const maxLengthName = 'a'.repeat(255);
        expect(AttendanceValidator.validateRunnerName(maxLengthName)).toBe(true);
      });

      it('should reject non-string values', () => {
        expect(AttendanceValidator.validateRunnerName(123 as any)).toBe(false);
        expect(AttendanceValidator.validateRunnerName(null as any)).toBe(false);
        expect(AttendanceValidator.validateRunnerName(undefined as any)).toBe(false);
      });
    });

    describe('sanitizeRunnerName', () => {
      it('should trim whitespace', () => {
        expect(AttendanceValidator.sanitizeRunnerName('  John Doe  ')).toBe('John Doe');
      });

      it('should normalize multiple spaces', () => {
        expect(AttendanceValidator.sanitizeRunnerName('John    Doe')).toBe('John Doe');
        expect(AttendanceValidator.sanitizeRunnerName('John\t\nDoe')).toBe('John Doe');
      });

      it('should handle mixed whitespace', () => {
        expect(AttendanceValidator.sanitizeRunnerName('  John   \t  Doe  \n ')).toBe('John Doe');
      });

      it('should return empty string for whitespace-only input', () => {
        expect(AttendanceValidator.sanitizeRunnerName('   ')).toBe('');
      });
    });

    describe('validateRunId', () => {
      it('should validate positive integers', () => {
        expect(AttendanceValidator.validateRunId(1)).toBe(true);
        expect(AttendanceValidator.validateRunId(100)).toBe(true);
        expect(AttendanceValidator.validateRunId(999999)).toBe(true);
      });

      it('should reject zero and negative numbers', () => {
        expect(AttendanceValidator.validateRunId(0)).toBe(false);
        expect(AttendanceValidator.validateRunId(-1)).toBe(false);
        expect(AttendanceValidator.validateRunId(-100)).toBe(false);
      });

      it('should reject non-integers', () => {
        expect(AttendanceValidator.validateRunId(1.5)).toBe(false);
        expect(AttendanceValidator.validateRunId(3.14)).toBe(false);
      });

      it('should reject non-numbers', () => {
        expect(AttendanceValidator.validateRunId('1' as any)).toBe(false);
        expect(AttendanceValidator.validateRunId(null as any)).toBe(false);
        expect(AttendanceValidator.validateRunId(undefined as any)).toBe(false);
      });

      it('should reject Infinity and NaN', () => {
        expect(AttendanceValidator.validateRunId(Infinity)).toBe(false);
        expect(AttendanceValidator.validateRunId(-Infinity)).toBe(false);
        expect(AttendanceValidator.validateRunId(NaN)).toBe(false);
      });
    });
  });
});