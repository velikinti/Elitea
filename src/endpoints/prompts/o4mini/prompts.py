"""All prompts for o4-mini model."""
import json


def get_system_message() -> str:
    """Get system message for o4-mini testcase generation."""
    # return "You are a helpful assistant for API test case generation."
    return "You are an expert API test engineer specializing in edge cases and boundary testing. Your role is to generate comprehensive, technically accurate test cases that follow strict JSON formatting rules. You must ensure all data types are correct and the output is valid, parseable JSON."



def get_testcase_prompt(api_spec: dict, review: str = None) -> str:
    """
    Generate testcase prompt for o4-mini.
    
    Args:
        api_spec: API specification dictionary
        review: Optional review/feedback to consider when generating test cases
        
    Returns:
        Formatted prompt string
    """
    prompt = (

        "You are an expert API tester. Given the following API specification, "
        "generate a comprehensive list of test cases covering ONLY edge and boundary scenarios.\n\n"

        "CRITICAL RULES:\n"
        "- Use ONLY the keys provided: method, url, headers, body, query_params.\n"
        "- Reuse the exact values from the API specification as the baseline.\n"
        "- Modify values ONLY to create edge or boundary conditions.\n"
        "- Do NOT invent URLs, fields, headers, parameters, or sample values.\n\n"

        "For each test case, provide:\n"
        "- name\n"
        "- code (TC001, TC002, ...)\n"
        "- description\n"
        "- preconditions (list only what is strictly required, derived from the spec)\n"
        "- request (method, url, headers, body, query_params)\n"
        "- expected_status\n"
        "- steps (detailed, step-by-step manual instructions; "
        "include request setup, value assignment, execution, and response verification)\n\n"

        "Steps MUST:\n"
        "- Reference the exact values used in the request\n"
        "- Describe one concrete action per step\n"
        "- Explicitly state header, body, and query parameter configuration\n"
        "- End with response status-code verification\n\n"

        "Focus on:\n"
        "- Empty, null, missing, malformed, and oversized values of existing fields\n"
        "- Incorrect data types for existing fields\n"
        "- Missing or invalid existing headers\n"
        "- Boundary or extreme values for existing query parameters\n\n"

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

