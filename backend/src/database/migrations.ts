import database from './connection';

export interface MigrationResult {
  success: boolean;
  error?: string;
  migrationsRun: string[];
}

export class MigrationManager {
  async runMigrations(): Promise<MigrationResult> {
    try {
      await database.runMigrations();
      return {
        success: true,
        migrationsRun: ['001_create_tables.sql']
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown migration error',
        migrationsRun: []
      };
    }
  }

  async checkDatabaseHealth(): Promise<boolean> {
    try {
      await database.query('SELECT 1');
      return true;
    } catch (error) {
      console.error('Database health check failed:', error);
      return false;
    }
  }

  async createDatabase(): Promise<void> {
    // This would typically be run outside the application
    // For development, ensure the database exists before running migrations
    const dbName = process.env.DB_NAME || 'runner_attendance';
    console.log(`Ensure database '${dbName}' exists before running migrations`);
  }
}

export const migrationManager = new MigrationManager();