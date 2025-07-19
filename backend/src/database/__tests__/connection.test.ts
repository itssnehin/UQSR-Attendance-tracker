import database from '../connection';
import { migrationManager } from '../migrations';

// Mock pg module
jest.mock('pg', () => {
  const mockPool = {
    connect: jest.fn(),
    query: jest.fn(),
    end: jest.fn(),
    on: jest.fn(),
    totalCount: 0,
    idleCount: 0,
    waitingCount: 0,
  };

  return {
    Pool: jest.fn(() => mockPool),
  };
});

describe('Database Connection', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Database Class', () => {
    it('should create a database instance', () => {
      expect(database).toBeDefined();
    });

    it('should handle connection establishment', async () => {
      const mockClient = {
        release: jest.fn(),
      };

      // Mock successful connection
      (database as any).pool.connect.mockResolvedValue(mockClient);

      await database.connect();

      expect((database as any).pool.connect).toHaveBeenCalled();
      expect(mockClient.release).toHaveBeenCalled();
    });

    it('should handle connection errors', async () => {
      const error = new Error('Connection failed');
      (database as any).pool.connect.mockRejectedValue(error);

      await expect(database.connect()).rejects.toThrow('Connection failed');
    });

    it('should execute queries successfully', async () => {
      const mockResult = {
        rows: [{ id: 1, name: 'test' }],
        rowCount: 1,
      };

      (database as any).pool.query.mockResolvedValue(mockResult);
      (database as any).isConnected = true;

      const result = await database.query('SELECT * FROM test');

      expect(result).toEqual(mockResult);
      expect((database as any).pool.query).toHaveBeenCalledWith('SELECT * FROM test', undefined);
    });

    it('should handle query errors', async () => {
      const error = new Error('Query failed');
      (database as any).pool.query.mockRejectedValue(error);
      (database as any).isConnected = true;

      await expect(database.query('INVALID SQL')).rejects.toThrow('Query failed');
    });

    it('should throw error when not connected', async () => {
      (database as any).isConnected = false;

      await expect(database.query('SELECT 1')).rejects.toThrow('Database not connected');
    });

    it('should handle transactions successfully', async () => {
      const mockClient = {
        query: jest.fn(),
        release: jest.fn(),
      };

      (database as any).pool.connect.mockResolvedValue(mockClient);
      mockClient.query.mockResolvedValue({ rows: [], rowCount: 0 });

      const callback = jest.fn().mockResolvedValue('success');

      const result = await database.transaction(callback);

      expect(result).toBe('success');
      expect(mockClient.query).toHaveBeenCalledWith('BEGIN');
      expect(mockClient.query).toHaveBeenCalledWith('COMMIT');
      expect(callback).toHaveBeenCalledWith(mockClient);
      expect(mockClient.release).toHaveBeenCalled();
    });

    it('should rollback transaction on error', async () => {
      const mockClient = {
        query: jest.fn(),
        release: jest.fn(),
      };

      (database as any).pool.connect.mockResolvedValue(mockClient);
      mockClient.query.mockResolvedValue({ rows: [], rowCount: 0 });

      const error = new Error('Transaction failed');
      const callback = jest.fn().mockRejectedValue(error);

      await expect(database.transaction(callback)).rejects.toThrow('Transaction failed');

      expect(mockClient.query).toHaveBeenCalledWith('BEGIN');
      expect(mockClient.query).toHaveBeenCalledWith('ROLLBACK');
      expect(mockClient.release).toHaveBeenCalled();
    });

    it('should return pool information', () => {
      const poolInfo = database.getPoolInfo();

      expect(poolInfo).toHaveProperty('totalCount');
      expect(poolInfo).toHaveProperty('idleCount');
      expect(poolInfo).toHaveProperty('waitingCount');
    });

    it('should check health status', () => {
      (database as any).isConnected = true;
      expect(database.isHealthy()).toBe(true);

      (database as any).isConnected = false;
      expect(database.isHealthy()).toBe(false);
    });
  });

  describe('Migration Manager', () => {
    it('should check database health', async () => {
      (database as any).pool.query.mockResolvedValue({ rows: [{ '?column?': 1 }] });

      const isHealthy = await migrationManager.checkDatabaseHealth();

      expect(isHealthy).toBe(true);
      expect((database as any).pool.query).toHaveBeenCalledWith('SELECT 1');
    });

    it('should handle health check failures', async () => {
      (database as any).pool.query.mockRejectedValue(new Error('Health check failed'));

      const isHealthy = await migrationManager.checkDatabaseHealth();

      expect(isHealthy).toBe(false);
    });
  });
});