# implementation-plan.md
# Kanban Board Enhancements — Implementation Plan (Priority, Assignment, Due Dates)

## 0. Scope & Source of Truth

**Scope:** Add task metadata fields to the existing SQLite-backed Kanban board:
- **Priority**: High / Medium / Low with color-coding in UI
- **Assignment**: single assignee (name + email)
- **Due Date**: `YYYY-MM-DD` format with validation preventing past dates

**Current DB schema:** `tasks[id, title, description, status]`

**FRD:** Confluence page `31719425` (Phase 1, approved)

**Jira tickets in scope (must map all tasks to these IDs):**
- **MLG1-13** — Task Priority: set High/Medium/Low with color-coding
- **MLG1-14** — Task Assignment: assign task to name or email
- **MLG1-15** — Due Dates: date picker with validation to prevent past dates

---

## 1) Database Schema Design + Migration Strategy (SQLite)

### 1.1 Design Goals
- Backwards compatible for existing rows.
- Minimal impact: extend existing `tasks` table.
- Enforce valid values where practical via SQLite CHECK constraints.
- Enable API + UI to treat fields as optional (at least initially), but validate on update/create.

### 1.2 Proposed Schema Changes
Add three columns to `tasks`:

1) `priority` (TEXT)
- Allowed: `HIGH`, `MEDIUM`, `LOW` (store normalized values)
- Default: `MEDIUM`
- Constraint: `CHECK(priority IN ('HIGH','MEDIUM','LOW'))`

2) `assignee_name` (TEXT)
- Nullable

3) `assignee_email` (TEXT)
- Nullable
- Validate format at API layer

4) `due_date` (TEXT)
- Store as ISO date string `YYYY-MM-DD` (no time)
- Nullable
- Past-date validation enforced at API layer

**DDL (conceptual):**
```sql
ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'MEDIUM' CHECK(priority IN ('HIGH','MEDIUM','LOW'));
ALTER TABLE tasks ADD COLUMN assignee_name TEXT;
ALTER TABLE tasks ADD COLUMN assignee_email TEXT;
ALTER TABLE tasks ADD COLUMN due_date TEXT;
```

### 1.3 Migration Script
- Create idempotent migration script that checks for column existence before adding
- Add indexes for performance:
  ```sql
  CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
  CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
  CREATE INDEX IF NOT EXISTS idx_tasks_assignee_email ON tasks(assignee_email);
  ```

### 1.4 Data Migration
- **Existing tasks:** Will automatically get `priority='MEDIUM'` via DEFAULT
- **New fields:** `assignee_name`, `assignee_email`, `due_date` will be NULL for existing tasks

---

## 2) Backend API Specifications

### 2.1 Enhanced Task Object
```json
{
  "id": 123,
  "title": "Implement X",
  "description": "Details...",
  "status": "TODO",
  "priority": "HIGH",
  "assignee": {
    "name": "Jane Doe",
    "email": "jane@example.com"
  },
  "due_date": "2026-09-15"
}
```

### 2.2 API Endpoints to Modify

#### **POST /tasks** (Create Task)
**Request body:**
```json
{
  "title": "string (required)",
  "description": "string (optional)",
  "status": "string (required)",
  "priority": "HIGH|MEDIUM|LOW (optional, default: MEDIUM)",
  "assignee": {
    "name": "string (optional)",
    "email": "string (optional)"
  },
  "due_date": "YYYY-MM-DD (optional)"
}
```

**Validations:**
- `priority` must be one of: HIGH, MEDIUM, LOW (case-insensitive, normalized to uppercase)
- `assignee.email` must be valid email format if provided
- `due_date` must be YYYY-MM-DD format and >= today's date
- Return 400 Bad Request with field-level error messages

#### **PUT /tasks/:id** (Update Task)
Same validations as POST

#### **GET /tasks** (List Tasks)
- Return all fields including new metadata
- Optional query params for filtering (future enhancement):
  - `?priority=HIGH`
  - `?assignee=email@example.com`
  - `?overdue=true`

#### **GET /tasks/:id** (Get Single Task)
- Return full task object with all metadata

### 2.3 Validation Rules (Backend)

| Field | Validation |
|-------|-----------|
| `priority` | Must be HIGH, MEDIUM, or LOW (case-insensitive) |
| `assignee.email` | Valid email format (regex: `^[^\s@]+@[^\s@]+\.[^\s@]+$`) |
| `due_date` | ISO date format YYYY-MM-DD, must be >= today (UTC) |

**Error Response Format:**
```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "due_date",
      "message": "Due date cannot be in the past"
    }
  ]
}
```

---

## 3) Frontend Technical Approach

### 3.1 UI Components

#### **Priority Selector**
- **Component:** Dropdown/Select with visual indicators
- **Options:**
  - HIGH (Red badge/background)
  - MEDIUM (Yellow/Amber badge/background)
  - LOW (Green badge/background)
- **Default:** MEDIUM (pre-selected in create form)
- **Display:** Color badge + text label for accessibility

**Color Palette:**
```css
.priority-high { background: #dc2626; color: white; }
.priority-medium { background: #f59e0b; color: white; }
.priority-low { background: #10b981; color: white; }
```

#### **Assignment Fields**
- **Components:** Two text inputs
  - Name (text input, optional)
  - Email (email input, optional)
- **Validation:** 
  - Client-side email format validation
  - Show inline error if invalid format
- **Display:** 
  - Show assignee name/email in task card
  - "Unassigned" badge if both fields empty

#### **Due Date Picker**
- **Component:** HTML5 date input or third-party date picker
- **Constraints:**
  - `min` attribute set to today's date (prevents past selection)
  - Client-side validation to disable past dates
- **Display:**
  - Show due date in task card
  - Visual indicator for overdue tasks (future enhancement)

### 3.2 Form Updates

#### **Create Task Form**
Add three new sections:
1. Priority dropdown (default: MEDIUM)
2. Assignee fields (name + email)
3. Due date picker

#### **Edit Task Form**
Same fields, pre-populated with existing values

#### **Task Card Display**
Add visual indicators:
- Priority badge at top-right corner
- Assignee avatar/initials (if assigned)
- Due date at bottom (with overdue warning if applicable)

### 3.3 Accessibility Considerations
- **Color + Text:** Don't rely solely on color (use text labels)
- **ARIA labels:** Add `aria-label` for screen readers
- **Keyboard navigation:** Ensure all controls are keyboard-accessible
- **Focus indicators:** Clear focus states for dropdowns and pickers

---

## 4) Implementation Roadmap (2-Week Plan)

### **Milestone A — Data Layer & API (Week 1)**

**Days 1-2: Database Migration**
- [ ] Write migration script (SQLite ALTER TABLE)
- [ ] Add CHECK constraints for priority
- [ ] Create indexes for performance
- [ ] Test migration on dev database
- **Jira:** MLG1-13, MLG1-14, MLG1-15 (DB work)

**Days 3-4: Backend API - Priority**
- [ ] Update POST /tasks to accept priority field
- [ ] Update PUT /tasks to accept priority field
- [ ] Add validation logic (HIGH/MEDIUM/LOW)
- [ ] Update GET endpoints to return priority
- [ ] Write unit tests for priority validation
- **Jira:** MLG1-13 (API)

**Day 5: Backend API - Assignment**
- [ ] Update POST /tasks to accept assignee object
- [ ] Update PUT /tasks to accept assignee object
- [ ] Add email validation logic
- [ ] Update GET endpoints to return assignee
- [ ] Write unit tests for assignee validation
- **Jira:** MLG1-14 (API)

**Days 6-7: Backend API - Due Date**
- [ ] Update POST /tasks to accept due_date field
- [ ] Update PUT /tasks to accept due_date field
- [ ] Add past-date validation logic (UTC-based)
- [ ] Update GET endpoints to return due_date
- [ ] Write unit tests for due date validation
- **Jira:** MLG1-15 (API)

### **Milestone B — Frontend Integration (Week 2)**

**Days 8-9: Priority UI**
- [ ] Create priority selector component (dropdown)
- [ ] Implement color-coding (CSS classes)
- [ ] Add priority badge to task cards
- [ ] Integrate with create/edit forms
- [ ] Write frontend tests
- **Jira:** MLG1-13 (UI)

**Day 10: Assignment UI**
- [ ] Create assignee input fields (name + email)
- [ ] Add client-side email validation
- [ ] Display assignee on task cards
- [ ] Handle "unassigned" state
- [ ] Write frontend tests
- **Jira:** MLG1-14 (UI)

**Days 11-12: Due Date UI**
- [ ] Integrate date picker component
- [ ] Set min date to today (prevent past dates)
- [ ] Display due date on task cards
- [ ] Add client-side validation
- [ ] Write frontend tests
- **Jira:** MLG1-15 (UI)

### **Milestone C — Hardening & Release (Days 13-14)**

**Day 13: Testing & QA**
- [ ] Integration tests (API + UI)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Edge case testing (timezone, validation errors)

**Day 14: Release Preparation**
- [ ] Update API documentation
- [ ] Write release notes
- [ ] Deploy to staging environment
- [ ] Final smoke tests
- [ ] Deploy to production

---

## 5) Risk Assessment & Mitigation Strategies

| **Risk** | **Impact** | **Probability** | **Mitigation** |
|----------|-----------|----------------|----------------|
| **Schema migration failures** | High | Low | Idempotent migration script with rollback plan; test on dev DB first |
| **Timezone edge cases** | Medium | Medium | Define canonical timezone (UTC) for due date validation; document behavior |
| **API backward compatibility** | High | Low | Make new fields optional; existing clients can ignore them |
| **Assignee data quality** | Low | High | No strict validation initially; consider autocomplete/user picker in future |
| **Color accessibility** | Medium | Low | Use text labels alongside colors; ARIA labels for screen readers |
| **Past date validation edge cases** | Medium | Medium | Server-side validation as source of truth; clear error messages |
| **Performance degradation** | Medium | Low | Add database indexes on new columns; monitor query performance |
| **SQLite limitations** | Medium | Low | Forward-only migrations; no complex constraints; document limitations |

### Mitigation Details

#### **Schema Migration Failures**
- Use `BEGIN TRANSACTION` / `COMMIT` wrapper
- Check column existence before ALTER TABLE
- Test migration script on copy of production DB
- Have rollback script ready (though ALTER TABLE DROP COLUMN not supported in SQLite)

#### **Timezone Edge Cases**
- Store all dates in UTC
- Document that "today" is based on server UTC time
- Consider adding timezone field in future iteration

#### **API Backward Compatibility**
- New fields are optional (nullable in DB)
- Existing clients can continue using old schema
- Version API if breaking changes needed in future

#### **Assignee Data Quality**
- Accept free-text for MVP (no user directory integration)
- Log assignee values for future analysis
- Consider typeahead/autocomplete in Phase 2

#### **Color Accessibility**
- Always show text label alongside color badge
- Use sufficient color contrast ratios (WCAG 2.1 AA)
- Test with screen readers

---

## 6) Testing Strategy

### 6.1 Unit Tests
- Backend validation logic (priority, email, due date)
- Database migration idempotency
- Frontend component rendering

### 6.2 Integration Tests
- API endpoints with new fields
- End-to-end task creation/update flows
- Database persistence verification

### 6.3 Manual Testing
- Cross-browser compatibility
- Accessibility with screen readers
- Edge cases (past dates, invalid emails, etc.)

### 6.4 Acceptance Criteria Verification
Verify all Gherkin scenarios from User Stories:
- MLG1-13: Priority selection and color-coding
- MLG1-14: Assignee input and validation
- MLG1-15: Due date picker and past-date prevention

---

## 7) Open Questions & Decisions

| **Question** | **Recommended Decision** | **Status** |
|--------------|-------------------------|------------|
| Should priority default to MEDIUM or be nullable? | MEDIUM (confirmed in requirements) | ✅ Confirmed |
| Due date validation timezone: UTC or local? | UTC (server time) | ⚠️ Needs confirmation |
| Assignee clearing: NULL or empty strings? | NULL (cleaner data model) | ⚠️ Needs confirmation |
| API structure: flat or nested assignee object? | Nested `{"assignee": {"name": "...", "email": "..."}}` | ⚠️ Needs confirmation |

---

## 8) Success Metrics

**Definition of Done:**
- [ ] All database migrations applied successfully
- [ ] All API endpoints updated and tested
- [ ] All UI components implemented and accessible
- [ ] All acceptance criteria verified
- [ ] Zero critical bugs in staging
- [ ] Documentation updated
- [ ] Jira tickets MLG1-13, MLG1-14, MLG1-15 closed

**Post-Release Monitoring:**
- API response times (should remain < 200ms p95)
- Database query performance
- User adoption of new fields
- Error rates for validation failures

---

## 9) Future Enhancements (Out of Scope)

- Filtering/searching by priority, assignee, or due date
- Overdue task notifications
- Bulk edit (set priority for multiple tasks)
- User directory integration (autocomplete assignee)
- Task history/audit log
- Recurring tasks with due dates
- Calendar view of due dates

---

## 10) Deliverables

1. **Database migration script** (`migrations/add_task_metadata.sql`)
2. **Updated API endpoints** (with tests)
3. **Frontend components** (priority selector, assignee fields, date picker)
4. **Test suite** (unit + integration)
5. **API documentation** (updated Swagger/OpenAPI)
6. **Release notes** (for end users)

---

**Plan Author:** CodeMie Planning-Release-Assistant  
**Date:** 2026-08-07  
**Status:** Approved  
**Next Step:** Create branch, commit, and open PR
