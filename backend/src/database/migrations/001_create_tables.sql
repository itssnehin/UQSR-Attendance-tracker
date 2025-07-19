-- Migration: Create initial tables for Runner Attendance Tracker
-- Version: 001
-- Description: Creates runs, attendances, and calendar_config tables

-- Create runs table
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create attendances table
CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    runner_name VARCHAR(255) NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(run_id, runner_name)
);

-- Create calendar_config table
CREATE TABLE IF NOT EXISTS calendar_config (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    has_run BOOLEAN NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_runs_date ON runs(date);
CREATE INDEX IF NOT EXISTS idx_runs_session_id ON runs(session_id);
CREATE INDEX IF NOT EXISTS idx_attendances_run_id ON attendances(run_id);
CREATE INDEX IF NOT EXISTS idx_attendances_runner_name ON attendances(runner_name);
CREATE INDEX IF NOT EXISTS idx_calendar_config_date ON calendar_config(date);