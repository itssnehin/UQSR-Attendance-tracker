import { RunValidator, CreateRunRequest, UpdateRunRequest } from '../Run';

describe('Run Model', () => {
  describe('RunValidator', () => {
    describe('validateCreateRequest', () => {
      it('should validate valid create request', () => {
        const validRequest: CreateRunRequest = {
          date: new Date('2024-01-15'),
          sessionId: 'session-123',
          isActive: true,
        };

        expect(RunValidator.validateCreateRequest(validRequest)).toBe(true);
      });

      it('should validate create request without isActive', () => {
        const validRequest = {
          date: new Date('2024-01-15'),
          sessionId: 'session-123',
        };

        expect(RunValidator.validateCreateRequest(validRequest)).toBe(true);
      });

      it('should reject request with invalid date', () => {
        const invalidRequest = {
          date: 'invalid-date',
          sessionId: 'session-123',
        };

        expect(RunValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with empty sessionId', () => {
        const invalidRequest = {
          date: new Date('2024-01-15'),
          sessionId: '',
        };

        expect(RunValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject request with missing sessionId', () => {
        const invalidRequest = {
          date: new Date('2024-01-15'),
        };

        expect(RunValidator.validateCreateRequest(invalidRequest)).toBe(false);
      });

      it('should reject null or undefined request', () => {
        expect(RunValidator.validateCreateRequest(null)).toBe(false);
        expect(RunValidator.validateCreateRequest(undefined)).toBe(false);
      });

      it('should reject non-object request', () => {
        expect(RunValidator.validateCreateRequest('string')).toBe(false);
        expect(RunValidator.validateCreateRequest(123)).toBe(false);
      });
    });

    describe('validateUpdateRequest', () => {
      it('should validate valid update request', () => {
        const validRequest: UpdateRunRequest = {
          isActive: false,
        };

        expect(RunValidator.validateUpdateRequest(validRequest)).toBe(true);
      });

      it('should validate empty update request', () => {
        const validRequest = {};

        expect(RunValidator.validateUpdateRequest(validRequest)).toBe(true);
      });

      it('should reject request with invalid isActive type', () => {
        const invalidRequest = {
          isActive: 'true',
        };

        expect(RunValidator.validateUpdateRequest(invalidRequest)).toBe(false);
      });

      it('should reject null or undefined request', () => {
        expect(RunValidator.validateUpdateRequest(null)).toBe(false);
        expect(RunValidator.validateUpdateRequest(undefined)).toBe(false);
      });
    });

    describe('validateSessionId', () => {
      it('should validate valid session ID', () => {
        expect(RunValidator.validateSessionId('session-123')).toBe(true);
        expect(RunValidator.validateSessionId('a')).toBe(true);
      });

      it('should reject empty session ID', () => {
        expect(RunValidator.validateSessionId('')).toBe(false);
      });

      it('should reject non-string session ID', () => {
        expect(RunValidator.validateSessionId(123 as any)).toBe(false);
        expect(RunValidator.validateSessionId(null as any)).toBe(false);
      });

      it('should reject session ID that is too long', () => {
        const longSessionId = 'a'.repeat(256);
        expect(RunValidator.validateSessionId(longSessionId)).toBe(false);
      });

      it('should accept session ID at max length', () => {
        const maxLengthSessionId = 'a'.repeat(255);
        expect(RunValidator.validateSessionId(maxLengthSessionId)).toBe(true);
      });
    });

    describe('validateDate', () => {
      it('should validate valid date', () => {
        expect(RunValidator.validateDate(new Date())).toBe(true);
        expect(RunValidator.validateDate(new Date('2024-01-15'))).toBe(true);
      });

      it('should reject invalid date', () => {
        expect(RunValidator.validateDate(new Date('invalid'))).toBe(false);
      });

      it('should reject non-date values', () => {
        expect(RunValidator.validateDate('2024-01-15' as any)).toBe(false);
        expect(RunValidator.validateDate(null as any)).toBe(false);
        expect(RunValidator.validateDate(undefined as any)).toBe(false);
      });
    });
  });
});