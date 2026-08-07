/**
 * TaskForm Component
 * Form for creating/editing Kanban tasks with metadata
 * Related Jira: MLG1-13, MLG1-14, MLG1-15
 */

import React, { useState } from 'react';

const TaskForm = ({ task = {}, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: task.title || '',
    description: task.description || '',
    status: task.status || 'TODO',
    priority: task.priority || 'Medium',
    assignee_name: task.assignee_name || '',
    assignee_email: task.assignee_email || '',
    due_date: task.due_date || ''
  });

  const [errors, setErrors] = useState({});

  const priorityColors = {
    High: '#dc2626',
    Medium: '#f59e0b',
    Low: '#10b981'
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate title (required)
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    // Validate email format if provided
    if (formData.assignee_email && 
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.assignee_email)) {
      newErrors.assignee_email = 'Invalid email format';
    }

    // Validate due date is not in the past
    if (formData.due_date) {
      const selectedDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate < today) {
        newErrors.due_date = 'Due date cannot be in the past';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const getTodayDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <h2>{task.id ? 'Edit Task' : 'Create Task'}</h2>

      {/* Title */}
      <div className="form-group">
        <label htmlFor="title">Title *</label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          required
          className={errors.title ? 'error' : ''}
        />
        {errors.title && <span className="error-message">{errors.title}</span>}
      </div>

      {/* Description */}
      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="4"
        />
      </div>

      {/* Status */}
      <div className="form-group">
        <label htmlFor="status">Status</label>
        <select
          id="status"
          name="status"
          value={formData.status}
          onChange={handleChange}
        >
          <option value="TODO">To Do</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="DONE">Done</option>
        </select>
      </div>

      {/* Priority - MLG1-13 */}
      <div className="form-group">
        <label htmlFor="priority">Priority</label>
        <select
          id="priority"
          name="priority"
          value={formData.priority}
          onChange={handleChange}
          style={{ 
            backgroundColor: priorityColors[formData.priority],
            color: 'white',
            fontWeight: 'bold'
          }}
        >
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <div className="priority-indicator" style={{ marginTop: '5px' }}>
          <span 
            className="priority-badge"
            style={{
              backgroundColor: priorityColors[formData.priority],
              color: 'white',
              padding: '4px 12px',
              borderRadius: '4px',
              fontSize: '12px'
            }}
          >
            {formData.priority}
          </span>
        </div>
      </div>

      {/* Assignment - MLG1-14 */}
      <div className="form-group">
        <label>Assignment</label>
        <input
          type="text"
          id="assignee_name"
          name="assignee_name"
          placeholder="Assignee Name"
          value={formData.assignee_name}
          onChange={handleChange}
        />
        <input
          type="email"
          id="assignee_email"
          name="assignee_email"
          placeholder="assignee@example.com"
          value={formData.assignee_email}
          onChange={handleChange}
          className={errors.assignee_email ? 'error' : ''}
          style={{ marginTop: '8px' }}
        />
        {errors.assignee_email && 
          <span className="error-message">{errors.assignee_email}</span>
        }
      </div>

      {/* Due Date - MLG1-15 */}
      <div className="form-group">
        <label htmlFor="due_date">Due Date</label>
        <input
          type="date"
          id="due_date"
          name="due_date"
          value={formData.due_date}
          onChange={handleChange}
          min={getTodayDate()}
          className={errors.due_date ? 'error' : ''}
        />
        {errors.due_date && 
          <span className="error-message">{errors.due_date}</span>
        }
      </div>

      {/* Actions */}
      <div className="form-actions">
        <button type="submit" className="btn-primary">
          {task.id ? 'Update Task' : 'Create Task'}
        </button>
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
};

export default TaskForm;
