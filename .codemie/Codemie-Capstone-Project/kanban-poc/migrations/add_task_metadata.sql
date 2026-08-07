-- Migration: Add task metadata columns (Priority, Assignment, Due Date)
-- Related Jira: MLG1-13, MLG1-14, MLG1-15
-- Date: 2026-08-07

-- Add priority column with CHECK constraint
ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium' 
  CHECK (priority IN ('High', 'Medium', 'Low'));

-- Add assignee columns
ALTER TABLE tasks ADD COLUMN assignee_name TEXT;
ALTER TABLE tasks ADD COLUMN assignee_email TEXT;

-- Add due date column (stored as YYYY-MM-DD string)
ALTER TABLE tasks ADD COLUMN due_date TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee_email ON tasks(assignee_email);

-- Verify migration
-- SELECT * FROM tasks LIMIT 1;
