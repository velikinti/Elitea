"""All prompts for GPT-4o model."""
import json


def get_system_message() -> str:
    """Get system message for GPT-4o testcase generation."""
    return "You are a helpful assistant for API test case generation."


def get_testcase_prompt(api_spec: dict, review: str = None) -> str:
    """
    Generate testcase prompt for GPT-4o.
    
    Args:
        api_spec: API specification dictionary
        review: Optional review/feedback to consider when generating test cases
        
    Returns:
        Formatted prompt string
    """
    prompt = (
        "You are an expert API tester. Given the following API specification, "
        "generate a comprehensive list of test cases covering ONLY edge and boundary scenarios.\n\n"

        "Focus on:\n"
        "Positive and Negative test cases: Invalid inputs, missing required fields, and data type mismatches\n\n"
        "Missing or invalid existing headers\n"
        "Boundary values including minimums, maximums, empty values, nulls, and very large numbers\n"
        "Edge and boundary values for defined query parameters\n\n"
        "Edge cases involving trailing slashes, special characters\n"

        "Each test case MUST have these fields with EXACT types:\n"
        "- name\n"
        "- code (TC001, TC002, TC003...)\n"
        "- description\n"
        "- request (method, url, headers, body, query params)\n"
        "- expected_status\n"
        "- steps: array of strings\n\n"

        "- Test cases MUST be strictly derived from the provided API specification.\n"
        "- Do NOT invent endpoints, fields, or request bodies that are not present in the spec.\n"
        "- Use the exact HTTP method, URL, path params, query params, headers, and request body structure defined in the spec.\n"
        "- Every test case MUST differ meaningfully from others (no duplicates or reworded positives).\n\n"

       "Example:\n"
        '{"name": "Create user with name exceeding maximum length", '
        '"code": "TC001", '
        '"description": "Verify that the API returns an error when the name field exceeds the maximum allowed length.", '
        '"request": {"method": "POST", "url": "https://api.example.com/users", '
        '"headers": {"Content-Type": "application/json"}, '
        '"body": {"name": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "age": 30}, '
        '"query_params": {}}, '
        '"expected_status": 400, '
        '"steps": ["Prepare request with name exceeding max length", '
        '"Send POST request to create user endpoint", '
        '"Verify response status code is 400", '
        '"Verify validation error for name length"]}\n\n'

        "IMPORTANT:\n"
        "- Return ONLY valid JSON\n"
        "- Top-level key must be \"test_cases\"\n"
        "- Do NOT include explanations or markdown\n\n"

        f"API Specification:\n{json.dumps(api_spec, indent=2)}\n\n"
    )
    
    # Add review section if provided
    if review:
        review_section = (
            "\n\n**REVIEW AND FEEDBACK TO CONSIDER:**\n"
            f"{review}\n\n"
            "Please carefully review the feedback above and adjust your test case generation accordingly. "
            "Incorporate the suggestions, address any concerns mentioned, and fine-tune the test cases "
            "based on the review. Ensure the generated test cases align with the feedback provided.\n\n"
        )
        prompt = prompt + review_section

    return prompt

