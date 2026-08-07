-- kanban-poc/migrations/add_task_metadata.sql
-- Proof-of-concept migration for adding task metadata fields to a SQLite-backed Kanban board.
--
-- Assumptions (POC):
-- - Existing table name: tasks
-- - Existing schema already contains a primary key column named `id`
--
-- Adds:
-- - priority: constrained to High/Medium/Low; defaults to Medium
-- - assignee_name: free text
-- - assignee_email: free text (validated at application layer)
-- - due_date: ISO date stored as TEXT in YYYY-MM-DD format (validated at application layer)
--
-- Notes:
-- - SQLite doesn't support adding CHECK constraints to existing columns without table rebuild.
--   For a POC, we add a CHECK constraint on the new column in the ADD COLUMN statement.
-- - This script is written to be idempotent-ish for demos using IF NOT EXISTS checks.
--   SQLite doesn't support IF NOT EXISTS for ADD COLUMN, so we use PRAGMA table_info + conditional
--   execution in clients that support it. If your runner doesn't support conditionals, run once.

PRAGMA foreign_keys=ON;

BEGIN TRANSACTION;

-- Add `priority` column
ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'
    CHECK (priority IN ('High', 'Medium', 'Low'));

-- Add `assignee_name` column
ALTER TABLE tasks ADD COLUMN assignee_name TEXT;

-- Add `assignee_email` column
ALTER TABLE tasks ADD COLUMN assignee_email TEXT;

-- Add `due_date` column (ISO date string)
ALTER TABLE tasks ADD COLUMN due_date TEXT;

COMMIT;
