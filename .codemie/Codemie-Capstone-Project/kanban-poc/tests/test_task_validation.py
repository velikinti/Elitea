"""
Unit Tests for Task Metadata Validator
Related Jira: MLG1-13, MLG1-14, MLG1-15
"""

import pytest
from datetime import date, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.task_validator import (
    validate_priority,
    validate_email,
    validate_due_date,
    validate_assignee_name,
    validate_task_metadata,
    ValidationError
)


class TestPriorityValidation:
    """Tests for MLG1-13: Priority validation"""
    
    def test_default_priority(self):
        """Should default to Medium when None"""
        assert validate_priority(None) == 'Medium'
        assert validate_priority() == 'Medium'
    
    def test_valid_priorities(self):
        """Should accept and normalize valid priorities"""
        assert validate_priority('high') == 'High'
        assert validate_priority('MEDIUM') == 'Medium'
        assert validate_priority('Low') == 'Low'
        assert validate_priority('  High  ') == 'High'
    
    def test_invalid_priority(self):
        """Should reject invalid priority values"""
        with pytest.raises(ValidationError, match="Invalid priority"):
            validate_priority('Urgent')
        
        with pytest.raises(ValidationError, match="Invalid priority"):
            validate_priority('Critical')
    
    def test_case_insensitive(self):
        """Should handle case-insensitive input"""
        assert validate_priority('HIGH') == 'High'
        assert validate_priority('medium') == 'Medium'
        assert validate_priority('LoW') == 'Low'


class TestEmailValidation:
    """Tests for MLG1-14: Email validation"""
    
    def test_valid_emails(self):
        """Should accept valid email formats"""
        assert validate_email('user@example.com') == 'user@example.com'
        assert validate_email('john.doe@company.co.uk') == 'john.doe@company.co.uk'
        assert validate_email('  test@test.com  ') == 'test@test.com'
    
    def test_invalid_emails(self):
        """Should reject invalid email formats"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email('notanemail')
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email('@example.com')
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email('user@')
        
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email('user @example.com')
    
    def test_empty_email(self):
        """Should return None for empty email"""
        assert validate_email(None) is None
        assert validate_email('') is None
        assert validate_email('   ') is None


class TestDueDateValidation:
    """Tests for MLG1-15: Due date validation"""
    
    def test_valid_future_date(self):
        """Should accept future dates"""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        assert validate_due_date(tomorrow) == tomorrow
        
        next_week = (date.today() + timedelta(days=7)).isoformat()
        assert validate_due_date(next_week) == next_week
    
    def test_today_is_valid(self):
        """Should accept today's date"""
        today = date.today().isoformat()
        assert validate_due_date(today) == today
    
    def test_past_date_rejected(self):
        """Should reject past dates"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the past"):
            validate_due_date(yesterday)
        
        last_week = (date.today() - timedelta(days=7)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the past"):
            validate_due_date(last_week)
    
    def test_invalid_date_format(self):
        """Should reject invalid date formats"""
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_due_date('2026-13-01')  # Invalid month
        
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_due_date('2026-02-30')  # Invalid day
        
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_due_date('01/15/2026')  # Wrong format
        
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_due_date('not-a-date')
    
    def test_empty_due_date(self):
        """Should return None for empty due date"""
        assert validate_due_date(None) is None
        assert validate_due_date('') is None
        assert validate_due_date('   ') is None


class TestAssigneeNameValidation:
    """Tests for MLG1-14: Assignee name validation"""
    
    def test_valid_names(self):
        """Should accept valid names"""
        assert validate_assignee_name('John Doe') == 'John Doe'
        assert validate_assignee_name('  Jane Smith  ') == 'Jane Smith'
    
    def test_empty_name(self):
        """Should return None for empty name"""
        assert validate_assignee_name(None) is None
        assert validate_assignee_name('') is None
        assert validate_assignee_name('   ') is None
    
    def test_name_too_long(self):
        """Should reject names longer than 100 characters"""
        long_name = 'A' * 101
        with pytest.raises(ValidationError, match="too long"):
            validate_assignee_name(long_name)
    
    def test_name_max_length(self):
        """Should accept names at exactly 100 characters"""
        max_name = 'A' * 100
        assert validate_assignee_name(max_name) == max_name


class TestTaskMetadataValidation:
    """Integration tests for complete task metadata validation"""
    
    def test_all_valid_fields(self):
        """Should validate all fields correctly"""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        result = validate_task_metadata(
            priority='high',
            assignee_name='John Doe',
            assignee_email='john@example.com',
            due_date=tomorrow
        )
        
        assert result['priority'] == 'High'
        assert result['assignee_name'] == 'John Doe'
        assert result['assignee_email'] == 'john@example.com'
        assert result['due_date'] == tomorrow
    
    def test_minimal_fields(self):
        """Should work with only priority (defaults to Medium)"""
        result = validate_task_metadata()
        
        assert result['priority'] == 'Medium'
        assert result['assignee_name'] is None
        assert result['assignee_email'] is None
        assert result['due_date'] is None
    
    def test_mixed_valid_and_empty(self):
        """Should handle mix of filled and empty fields"""
        result = validate_task_metadata(
            priority='Low',
            assignee_name='Jane Smith',
            assignee_email=None,
            due_date=None
        )
        
        assert result['priority'] == 'Low'
        assert result['assignee_name'] == 'Jane Smith'
        assert result['assignee_email'] is None
        assert result['due_date'] is None
    
    def test_invalid_priority_in_metadata(self):
        """Should raise error for invalid priority"""
        with pytest.raises(ValidationError, match="Invalid priority"):
            validate_task_metadata(priority='Invalid')
    
    def test_invalid_email_in_metadata(self):
        """Should raise error for invalid email"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_task_metadata(assignee_email='not-an-email')
    
    def test_past_date_in_metadata(self):
        """Should raise error for past due date"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError, match="cannot be in the past"):
            validate_task_metadata(due_date=yesterday)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
