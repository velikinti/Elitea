import pytest

from kanban_poc.backend.task_validator import (
    ValidationError,
    validate_assignee_name,
    validate_due_date,
    validate_email,
    validate_priority,
    validate_task_metadata,
)


def test_validate_priority_defaults_to_medium_on_none():
    assert validate_priority(None) == "Medium"


def test_validate_priority_defaults_to_medium_on_blank():
    assert validate_priority("   ") == "Medium"


@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("High", "High"),
        ("high", "High"),
        ("  LOW ", "Low"),
        ("Medium", "Medium"),
    ],
)
def test_validate_priority_normalizes_case(input_value, expected):
    assert validate_priority(input_value) == expected


def test_validate_priority_rejects_invalid():
    with pytest.raises(ValidationError) as exc:
        validate_priority("Urgent")
    assert "Invalid priority" in str(exc.value)


def test_validate_email_allows_none_and_blank():
    assert validate_email(None) is None
    assert validate_email("") is None
    assert validate_email("   ") is None


def test_validate_email_accepts_valid_email():
    assert validate_email("jane.doe+tag@example.co.uk") == "jane.doe+tag@example.co.uk"


@pytest.mark.parametrize("email", ["no-at-symbol", "a@", "@b.com", "a@b", "a b@c.com"])
def test_validate_email_rejects_invalid(email):
    with pytest.raises(ValidationError):
        validate_email(email)


def test_validate_due_date_allows_none_and_blank():
    assert validate_due_date(None) is None
    assert validate_due_date("") is None
    assert validate_due_date("   ") is None


def test_validate_due_date_accepts_iso_date_and_normalizes():
    assert validate_due_date("2026-08-07") == "2026-08-07"


@pytest.mark.parametrize("due", ["2026/08/07", "07-08-2026", "2026-8-7", "not-a-date", "2026-02-30"])
def test_validate_due_date_rejects_invalid(due):
    with pytest.raises(ValidationError):
        validate_due_date(due)


def test_validate_assignee_name_trims_and_allows_blank_to_none():
    assert validate_assignee_name("  Jane Doe  ") == "Jane Doe"
    assert validate_assignee_name("   ") is None


def test_validate_assignee_name_rejects_too_long():
    with pytest.raises(ValidationError):
        validate_assignee_name("a" * 101)


def test_validate_task_metadata_returns_normalized_dict():
    out = validate_task_metadata(
        priority="low",
        assignee_name="  Jane Doe ",
        assignee_email=" jane@example.com ",
        due_date="2026-12-31",
    )
    assert out == {
        "priority": "Low",
        "assignee_name": "Jane Doe",
        "assignee_email": "jane@example.com",
        "due_date": "2026-12-31",
    }
