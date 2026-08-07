"""
Task Metadata Validator
Validates priority, assignment, and due date fields for Kanban tasks
Related Jira: MLG1-13, MLG1-14, MLG1-15
"""

import re
from datetime import date, datetime
from typing import Dict, Any, Optional


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_priority(priority: Optional[str] = None) -> str:
    """
    Validate and normalize task priority
    
    Args:
        priority: Priority value (case-insensitive)
    
    Returns:
        Normalized priority (High, Medium, or Low)
    
    Raises:
        ValidationError: If priority is invalid
    """
    if priority is None:
        return 'Medium'
    
    normalized = priority.strip().capitalize()
    
    if normalized not in ['High', 'Medium', 'Low']:
        raise ValidationError(
            f"Invalid priority '{priority}'. Must be High, Medium, or Low."
        )
    
    return normalized


def validate_email(email: Optional[str]) -> Optional[str]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        Validated email or None
    
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        return None
    
    email = email.strip()
    
    # Basic email regex pattern
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    
    if not re.match(pattern, email):
        raise ValidationError(
            f"Invalid email format: '{email}'"
        )
    
    return email


def validate_due_date(due_date: Optional[str]) -> Optional[str]:
    """
    Validate due date format and ensure it's not in the past
    
    Args:
        due_date: Date string in YYYY-MM-DD format
    
    Returns:
        Validated date string or None
    
    Raises:
        ValidationError: If date format is invalid or date is in the past
    """
    if not due_date:
        return None
    
    due_date = due_date.strip()
    
    try:
        parsed_date = date.fromisoformat(due_date)
    except ValueError as e:
        raise ValidationError(
            f"Invalid date format '{due_date}'. Must be YYYY-MM-DD."
        ) from e
    
    today = date.today()
    if parsed_date < today:
        raise ValidationError(
            f"Due date '{due_date}' cannot be in the past. Today is {today}."
        )
    
    return due_date


def validate_assignee_name(name: Optional[str]) -> Optional[str]:
    """
    Validate assignee name
    
    Args:
        name: Assignee name
    
    Returns:
        Trimmed name or None
    
    Raises:
        ValidationError: If name is too long
    """
    if not name:
        return None
    
    name = name.strip()
    
    if len(name) > 100:
        raise ValidationError(
            f"Assignee name too long ({len(name)} chars). Maximum 100 characters."
        )
    
    return name


def validate_task_metadata(
    priority: Optional[str] = None,
    assignee_name: Optional[str] = None,
    assignee_email: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate all task metadata fields
    
    Args:
        priority: Task priority
        assignee_name: Assignee name
        assignee_email: Assignee email
        due_date: Due date (YYYY-MM-DD)
    
    Returns:
        Dictionary of validated and normalized fields
    
    Raises:
        ValidationError: If any field is invalid
    """
    return {
        'priority': validate_priority(priority),
        'assignee_name': validate_assignee_name(assignee_name),
        'assignee_email': validate_email(assignee_email),
        'due_date': validate_due_date(due_date)
    }
