# Kanban Board Enhancements - POC Implementation

## Overview
Proof-of-concept implementation for Kanban board enhancements adding Priority, Assignment, and Due Date features.

**Related Jira:**
- MLG1-13: Task Priority (High/Medium/Low with color-coding)
- MLG1-14: Task Assignment (name/email)
- MLG1-15: Due Dates (YYYY-MM-DD with past-date validation)

**Confluence FRD:** Page ID 31719425

## Structure

```
kanban-poc/
├── migrations/
│   └── add_task_metadata.sql      # SQLite migration script
├── backend/
│   └── task_validator.py          # Python validation module
├── frontend/
│   └── TaskForm.jsx                # React form component
└── tests/
    └── test_task_validation.py     # Pytest unit tests
```

## Components

### 1. Database Migration (`migrations/add_task_metadata.sql`)
- Adds `priority` column (TEXT, CHECK constraint, default 'Medium')
- Adds `assignee_name` column (TEXT, nullable)
- Adds `assignee_email` column (TEXT, nullable)
- Adds `due_date` column (TEXT, nullable, YYYY-MM-DD format)
- Creates performance indexes

### 2. Backend Validator (`backend/task_validator.py`)
Python module with validation functions:
- `validate_priority()` - Normalizes and validates priority (High/Medium/Low)
- `validate_email()` - Validates email format using regex
- `validate_due_date()` - Validates ISO date format and prevents past dates
- `validate_assignee_name()` - Validates name length
- `validate_task_metadata()` - Complete metadata validation

### 3. Frontend Form (`frontend/TaskForm.jsx`)
React component featuring:
- Priority dropdown with color-coding (Red/Amber/Green)
- Assignee name and email inputs
- Due date picker with min date constraint
- Client-side validation
- Error display

### 4. Unit Tests (`tests/test_task_validation.py`)
Comprehensive pytest test suite:
- Priority validation tests (defaults, normalization, invalid values)
- Email validation tests (valid/invalid formats)
- Due date validation tests (past/future dates, invalid formats)
- Assignee name validation tests (length constraints)
- Integration tests for complete metadata validation

## Running Tests

```bash
# Install dependencies
pip install pytest

# Run tests from kanban-poc directory
cd kanban-poc
python -m pytest tests/test_task_validation.py -v

# Or run directly
python tests/test_task_validation.py
```

## Usage

### Backend Validation Example
```python
from backend.task_validator import validate_task_metadata, ValidationError

try:
    validated = validate_task_metadata(
        priority='high',
        assignee_name='John Doe',
        assignee_email='john@example.com',
        due_date='2026-12-31'
    )
    print(validated)
    # {'priority': 'High', 'assignee_name': 'John Doe', 
    #  'assignee_email': 'john@example.com', 'due_date': '2026-12-31'}
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Frontend Component Example
```jsx
import TaskForm from './frontend/TaskForm';

function App() {
  const handleSubmit = (formData) => {
    console.log('Task data:', formData);
    // Send to API
  };

  const handleCancel = () => {
    console.log('Cancelled');
  };

  return (
    <TaskForm 
      task={{}}
      onSubmit={handleSubmit}
      onCancel={handleCancel}
    />
  );
}
```

## Database Migration

```bash
# Apply migration to SQLite database
sqlite3 your_database.db < migrations/add_task_metadata.sql
```

## Design Decisions

1. **Priority Storage**: TEXT with CHECK constraint for type safety
2. **Email Validation**: Regex pattern on backend, HTML5 type="email" on frontend
3. **Date Format**: ISO 8601 (YYYY-MM-DD) for consistency and SQLite compatibility
4. **Assignment Model**: Separate name/email fields (no user directory integration)
5. **Default Priority**: Medium for all tasks (existing and new)
6. **Past Date Prevention**: Both client-side (HTML min attribute) and server-side validation

## Validation Rules

### Priority (MLG1-13)
- Accepts: "High", "Medium", "Low" (case-insensitive)
- Normalizes to capitalized format
- Defaults to "Medium" if not provided
- Color-coded: High=Red, Medium=Amber, Low=Green

### Email (MLG1-14)
- Pattern: `^[^\s@]+@[^\s@]+\.[^\s@]+$`
- Optional (can be null/empty)
- Trimmed of whitespace

### Due Date (MLG1-15)
- Format: YYYY-MM-DD (ISO 8601)
- Must be today or future date
- Server timezone: UTC
- Optional (can be null/empty)

### Assignee Name (MLG1-14)
- Maximum 100 characters
- Trimmed of whitespace
- Optional (can be null/empty)

## Next Steps for Production

1. Integrate into actual Kanban application
2. Connect to real SQLite database
3. Add API endpoints (POST/PUT /tasks)
4. Implement frontend routing
5. Add filtering by priority/assignee/due date
6. Implement overdue task indicators
7. Add unit tests for API endpoints
8. Add E2E tests
9. Deploy to staging environment

## Approval Gate
This POC demonstrates the core implementation approach. Review and approval required before integration into production codebase.
