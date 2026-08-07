// kanban-poc/frontend/TaskForm.jsx
// Proof-of-concept React component for editing Kanban task metadata.
//
// Notes:
// - This is a UI mockup meant to demonstrate form fields and basic client-side validation.
// - Uses no external libraries beyond React.

import React, { useMemo, useState } from 'react';

const PRIORITIES = ['High', 'Medium', 'Low'];

function isIsoDate(value) {
  // Strict YYYY-MM-DD (not validating day/month ranges here; leave that to backend).
  return /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function isEmail(value) {
  // Pragmatic email check; backend is source of truth.
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

export default function TaskForm({
  initialValue,
  onSubmit,
  submitLabel = 'Save',
}) {
  const initial = useMemo(
    () => ({
      title: initialValue?.title ?? '',
      description: initialValue?.description ?? '',
      priority: initialValue?.priority ?? 'Medium',
      assigneeName: initialValue?.assigneeName ?? '',
      assigneeEmail: initialValue?.assigneeEmail ?? '',
      dueDate: initialValue?.dueDate ?? '',
    }),
    [initialValue]
  );

  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState({});

  const setField = (key) => (e) => {
    const value = e.target.value;
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const validate = () => {
    const nextErrors = {};

    if (!form.title.trim()) nextErrors.title = 'Title is required.';

    if (!PRIORITIES.includes(form.priority)) {
      nextErrors.priority = 'Priority must be High, Medium, or Low.';
    }

    if (form.assigneeEmail.trim() && !isEmail(form.assigneeEmail.trim())) {
      nextErrors.assigneeEmail = 'Invalid email.';
    }

    if (form.dueDate.trim() && !isIsoDate(form.dueDate.trim())) {
      nextErrors.dueDate = 'Due date must be YYYY-MM-DD.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      priority: form.priority,
      assignee_name: form.assigneeName.trim() || null,
      assignee_email: form.assigneeEmail.trim() || null,
      due_date: form.dueDate.trim() || null,
    };

    await onSubmit?.(payload);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12, maxWidth: 520 }}>
      <div>
        <label>
          Title
          <input
            type="text"
            value={form.title}
            onChange={setField('title')}
            style={{ width: '100%' }}
            aria-invalid={Boolean(errors.title)}
          />
        </label>
        {errors.title ? <div style={{ color: 'crimson' }}>{errors.title}</div> : null}
      </div>

      <div>
        <label>
          Description
          <textarea
            value={form.description}
            onChange={setField('description')}
            style={{ width: '100%', minHeight: 80 }}
          />
        </label>
      </div>

      <div>
        <label>
          Priority
          <select
            value={form.priority}
            onChange={setField('priority')}
            aria-invalid={Boolean(errors.priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        {errors.priority ? <div style={{ color: 'crimson' }}>{errors.priority}</div> : null}
      </div>

      <fieldset style={{ border: '1px solid #ddd', padding: 12 }}>
        <legend>Assignment</legend>

        <div style={{ display: 'grid', gap: 10 }}>
          <label>
            Name
            <input
              type="text"
              value={form.assigneeName}
              onChange={setField('assigneeName')}
              style={{ width: '100%' }}
              placeholder="Jane Doe"
            />
          </label>

          <label>
            Email
            <input
              type="email"
              value={form.assigneeEmail}
              onChange={setField('assigneeEmail')}
              style={{ width: '100%' }}
              placeholder="jane@example.com"
              aria-invalid={Boolean(errors.assigneeEmail)}
            />
          </label>
          {errors.assigneeEmail ? (
            <div style={{ color: 'crimson' }}>{errors.assigneeEmail}</div>
          ) : null}
        </div>
      </fieldset>

      <div>
        <label>
          Due date (YYYY-MM-DD)
          <input
            type="text"
            value={form.dueDate}
            onChange={setField('dueDate')}
            style={{ width: '100%' }}
            placeholder="2026-12-31"
            aria-invalid={Boolean(errors.dueDate)}
          />
        </label>
        {errors.dueDate ? <div style={{ color: 'crimson' }}>{errors.dueDate}</div> : null}
      </div>

      <button type="submit">{submitLabel}</button>
    </form>
  );
}
