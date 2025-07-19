import { migrationManager, MigrationManager } from '../migrations';
import database from '../connection';

// Mock the database connection
jest.mock('../connection', () => ({
  runMigrations: jest.fn(),
  query: jest.fn(),
}));

describe('Migration Manager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('runMigrations', () => {
    it('should run migrations successfully', async () => {
      (database.runMigrations as jest.Mock).mockResolvedValue(undefined);

      const result = await migrationManager.runMigrations();

      expect(result.success).toBe(true);
      expect(result.migrationsRun).toEqual(['001_create_tables.sql']);
      expect(result.error).toBeUndefined();
      expect(database.runMigrations).toHaveBeenCalled();
    });

    it('should handle migration failures', async () => {
      const error = new Error('Migration failed');
      (database.runMigrations as jest.Mock).mockRejectedValue(error);

      const result = await migrationManager.runMigrations();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Migration failed');
      expect(result.migrationsRun).toEqual([]);
    });

    it('should handle unknown errors', async () => {
      (database.runMigrations as jest.Mock).mockRejectedValue('Unknown error');

      const result = await migrationManager.runMigrations();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Unknown migration error');
      expect(result.migrationsRun).toEqual([]);
    });
  });

  describe('checkDatabaseHealth', () => {
    it('should return true for healthy database', async () => {
      (database.query as jest.Mock).mockResolvedValue({ rows: [{ '?column?': 1 }] });

      const isHealthy = await migrationManager.checkDatabaseHealth();

      expect(isHealthy).toBe(true);
      expect(database.query).toHaveBeenCalledWith('SELECT 1');
    });

    it('should return false for unhealthy database', async () => {
      (database.query as jest.Mock).mockRejectedValue(new Error('Connection failed'));

      const isHealthy = await migrationManager.checkDatabaseHealth();

      expect(isHealthy).toBe(false);
    });
  });

  describe('createDatabase', () => {
    it('should log database creation message', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      await migrationManager.createDatabase();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Ensure database 'runner_attendance' exists")
      );

      consoleSpy.mockRestore();
    });

    it('should use custom database name from environment', async () => {
      const originalEnv = process.env.DB_NAME;
      process.env.DB_NAME = 'custom_db';

      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      await migrationManager.createDatabase();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Ensure database 'custom_db' exists")
      );

      consoleSpy.mockRestore();
      process.env.DB_NAME = originalEnv;
    });
  });

  describe('MigrationManager class', () => {
    it('should create a new instance', () => {
      const manager = new MigrationManager();
      expect(manager).toBeInstanceOf(MigrationManager);
    });

    it('should export a singleton instance', () => {
      expect(migrationManager).toBeInstanceOf(MigrationManager);
    });
  });
});