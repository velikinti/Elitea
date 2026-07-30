"""All prompts for GPT-5-mini model."""
import json
from typing import Dict


def get_system_message() -> str:
    """Get system message for GPT-5-mini testcase generation."""
    return "You are an expert API test engineer specializing in edge cases and boundary testing. Your role is to generate comprehensive, technically accurate test cases that follow strict JSON formatting rules. You must ensure all data types are correct and the output is valid, parseable JSON."


def get_testcase_prompt(api_spec: dict, review: str = None, temperature: float = None, max_completion_tokens: int = None, top_p: float = None) -> str:
    """
    Generate testcase prompt for GPT-5-mini.
    
    Args:
        api_spec: API specification dictionary
        review: Optional review/feedback to consider when generating test cases
        temperature: Optional temperature parameter (not used in prompt but kept for compatibility)
        max_completion_tokens: Optional max tokens (not used in prompt but kept for compatibility)
        top_p: Optional top_p parameter (not used in prompt but kept for compatibility)
        
    Returns:
        Formatted prompt string
    """
    prompt = (
        "You are an expert API test engineer. Generate 12-18 test cases covering edge cases, boundaries, "
        "HTTP protocol aspects, and API-specific validation.\n\n"

        "Coverage areas:\n"
        "- Edge cases: trailing slashes, extra headers, type mismatches, encoding\n"
        "- Boundaries: min/max values, empty/null, very large numbers\n"
        "- HTTP: methods, headers, status codes, content negotiation, conditional requests\n"
        "- API-specific: data validation, relationships, query parameters\n"
        "- Errors: invalid inputs, missing fields, type mismatches\n\n"

        "Each test case MUST have these fields with EXACT types:\n"
        "- name: string\n"
        "- code: string (e.g., \"TC001\")\n"
        "- description: string\n"
        "- request: object with method (string), url (string), headers (object), body (object|null), query_params (object)\n"
        "- expected_status: integer (200, 404, 500, etc.) - MUST be integer, NEVER string\n"
        "- steps: array of strings\n\n"

        "Example:\n"
        '{"name": "TC001 - Boundary: Max ID", "code": "TC001", "description": "Test max ID boundary", '
        '"request": {"method": "GET", "url": "https://api.example.com/resource/2147483647", "headers": {}, '
        '"body": null, "query_params": {}}, "expected_status": 200, '
        '"steps": ["Send GET request", "Verify status 200"]}\n\n'

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
    
    prompt += (
        "CRITICAL: expected_status MUST be integer (200, 404, 500), not string. "
        "Return ONLY valid JSON array starting with [ and ending with ]. "
        "No markdown, no explanations. Validate: all commas correct, all brackets closed, all strings quoted."
    )

    return prompt


def get_testscript_system_message() -> str:
    """Get system message for testscript generation."""
    return "You are an expert test automation engineer specializing in API testing. Generate complete, executable pytest test functions using ONLY API components from the framework. NEVER use UI components (BasePage, BaseActions, Browser, WebDriver, Selenium) even if they appear in the framework analysis. Only use framework.api.* imports and API-related utilities. Never use generic or placeholder code."


def get_testscript_review_section(review: str = None, original_script: str = None) -> str:
    """
    Build review section for prompt.
    
    Args:
        review: Optional review/feedback text
        original_script: Optional original script for comparison
        
    Returns:
        Review section string
    """
    if not review:
        return ""
    
    review_section = f"""
## Review/Feedback

{review}
"""
    
    if original_script:
        review_section += f"""
## Original Script (for reference)

```python
{original_script}
```

**IMPORTANT:** Please incorporate the above review/feedback into the generated test script.
- Address any specific concerns mentioned
- Add any missing validations or assertions
- Fix any code style or structure issues
- Ensure the review requirements are met while maintaining framework compliance
"""
    else:
        review_section += """
**IMPORTANT:** Please incorporate the above review/feedback into the generated test script.
- Address any specific concerns mentioned
- Add any missing validations or assertions
- Fix any code style or structure issues
- Ensure the review requirements are met while maintaining framework compliance
"""
    
    return review_section



def get_testscript_prompt(test_case_json: str, framework_section: str, components: Dict[str, str], review_section: str, test_case) -> str:
    """
    Build LLM prompt for test script generation.
    
    Args:
        test_case_json: JSON string of the test case
        framework_section: Framework analysis markdown section
        components: Dictionary with component information (config_class, client_class, etc.)
        review_section: Review/feedback section
        test_case: Test case object
        
    Returns:
        Formatted prompt string
    """
    return f"""You are a test automation expert. Generate a complete pytest test function based on the framework analysis and test case provided.

## Framework Analysis (Key Components - API ONLY)

{framework_section}

**IMPORTANT:** Extract method signatures, properties, and usage patterns directly from the framework analysis above. 
The framework analysis contains all the information you need about:
- Available methods in {components['client_class']} (e.g., requests_get, requests_post, request_put, request_delete, requests_patch)
- Available properties in {components['response_class']} (e.g., status_code, json_response, text, response, http_error_msg)
- Method signatures and return types
- Usage examples and patterns

## Test Case

{test_case_json}
{review_section}

## ⚠️ CRITICAL WARNING - READ CAREFULLY ⚠️

**THIS IS AN API TEST - USE ONLY API COMPONENTS!**

The framework analysis may contain BOTH API and UI components. For this API test case, you MUST:
- ✅ USE ONLY components from "API Components" section
- ✅ USE ONLY utilities from "API Utilities" section  
- ✅ USE ONLY API-related test patterns
- ❌ DO NOT use any UI components (BasePage, BaseActions, Browser, Locator, Wait, etc.)
- ❌ DO NOT use any UI utilities
- ❌ DO NOT import any UI-related classes
- ❌ DO NOT use WebDriver, Selenium, or browser-related code

**ONLY use these API components:**
- {components['config_class']}, {components['client_class']}, {components['response_class']}, {components['assertion_utils']}
- API exception classes (ParamsMissing, InvalidURLException, etc.)
- API validation utilities (JSONValidator, CSVValidator, XMLValidator)
- API helper functions (build_url, handle_http_error, etc.)

## CRITICAL INSTRUCTIONS - FOLLOW EXACTLY

Generate a COMPLETE, EXECUTABLE pytest test function that:

1. **IMPORTS** - Use these EXACT imports from the framework analysis:
```python
import pytest
{components['config_import']}
{components['client_import']}
{components['response_import']}
{components['assertion_import']}
```

2. **REQUEST CONSTRUCTION** - Extract and use EXACT method signatures from the framework analysis:
```python
# Create API configuration (use EXACT class name: {components['config_class']})
config = {components['config_class']}()
config.base_url = "{{base_url}}"  # Extract from test case URL
config.end_point = "{{endpoint}}"  # Extract from test case URL

# Add headers using addHeader method (if headers exist in test case)
if headers:
    for key, value in headers.items():
        config.addHeader(key, value)

# Add query params (if query_params exist in test case)
if query_params:
    config.params = query_params

# Send request using {components['client_class']} - Extract EXACT method signatures from framework analysis:
# Look for methods like: requests_get, requests_post, request_put, request_delete, requests_patch
# Use the EXACT method name and signature as shown in the framework analysis
# Method signature format: {components['client_class']}.<method_name>(config, ...) -> {components['response_class']}
response = {components['client_class']}.requests_get(config)  # Use correct method based on HTTP method from test case
```

3. **RESPONSE VALIDATION** - Extract and use EXACT properties and methods from the framework analysis:
```python
# Validate status code using {components['assertion_utils']} - Extract EXACT method signature from framework analysis
{components['assertion_utils']}.validate_status_code(response.response, {test_case.expected_status})

# Access response data using EXACT property names from {components['response_class']}:
# Extract available properties from the framework analysis (e.g., status_code, json_response, text, response, http_error_msg)
# Use the EXACT property names as documented in the framework analysis
assert response.status_code == {test_case.expected_status}

# If JSON response exists, validate content
if response.json_response:
    assert response.json_response is not None
    
    # Use JSONValidator for JSON validation if needed (check framework analysis for exact method signatures):
    # from framework.api.response.response_parser import JSONValidator
    # JSONValidator.validate_node_in_response_body(response.json_response, 'key', 'expected_value')
```

4. **ERROR HANDLING** - Follow framework patterns from the analysis:
```python
# Check for HTTP errors (use exact property names from framework analysis)
if response.http_error_msg:
    raise Exception(f"HTTP Error: {{response.http_error_msg}}")

# Validate response structure
if response.status_code >= 400:
    # Handle error responses according to test case expectations
    pass
```

5. **TEST STRUCTURE**:
   - Function name: test_{{test_case.code}}__{{sanitized_name}}
   - Use @pytest.mark.api decorator
   - Include docstring with test case description and code
   - Implement ALL steps from the test case
   - Follow test setup patterns from framework (ONLY API setup: PropFileReader, LoggerFactory - NO Browser or driver setup)
   - DO NOT include any UI/WebDriver initialization or browser-related code

6. **CODE QUALITY**:
   - NO TODO comments
   - NO placeholders
   - Complete, executable code
   - Extract and use EXACT method names and signatures from framework analysis
   - Extract and use EXACT property names from response class
   - Proper error handling following framework patterns

7. **VALIDATION** - Use framework validation utilities when appropriate (API utilities ONLY):
   - Extract validation method signatures from the framework analysis
   - JSONValidator.validate_node_in_response_body() for JSON validation
   - JSONValidator.validate_node_with_jsonpath_response() for JSONPath validation
   - RestResponse.validate_protocol_version() for protocol validation
   - RestResponse.validate_reason_phrase() for reason phrase validation
   - DO NOT use any UI validation utilities (BaseVerifications, is_text, is_displayed, etc.)

8. **COMPONENT RESTRICTION** - IMPORTANT:
   - This is an API test - generate ONLY API test code
   - If you see UI components (BasePage, BaseActions, Browser, Locator, Wait) in the framework analysis, IGNORE them completely
   - If you see UI utilities in the framework analysis, IGNORE them completely
   - Only use components clearly marked as "API Components" or "API Utilities"
   - Only use classes/functions from framework.api.* imports
   - NEVER use framework.ui.* imports
   - NEVER use Selenium, WebDriver, or browser automation code

9. **EXTRACTION REQUIREMENT**:
   - You MUST extract method signatures, property names, and usage patterns directly from the framework analysis provided above
   - Do NOT guess or use generic method names - use EXACT names from the framework analysis
   - If a method or property is documented in the framework analysis, use it exactly as shown
   - If a method or property is NOT in the framework analysis, do NOT use it

Return ONLY the Python code for the complete test function. Do not include explanations, markdown formatting, code blocks (```python or ```), or any text outside the code. Start directly with the imports."""



def get_testscript_judge_system_message():
    """Get system message for test script judge agent."""
    return "You are an expert test script reviewer. Evaluate the provided test script based on technical accuracy, completeness, and adherence to best practices. Provide specific feedback and improvement recommendations. Output ONLY valid JSON - no explanations, no markdown formatting."


def get_testscript_judge_prompt(test_script: str, test_case: dict) -> str:
    """
    Generate judge prompt for test script evaluation.
    
    Args:
        test_script: Test script code to review
        test_case: Test case dictionary with expected behavior
        
    Returns:
        Formatted judge prompt string for test script review
    """
    prompt = f"""You are an expert test automation reviewer. Evaluate the provided test script against the test case requirements and technical standards.

## Test Script to Review:
```python
{test_script}
```

## Test Case Context:
{json.dumps(test_case, indent=2)}

## Evaluation Criteria (Score 0-100 each):
1. **Accuracy**: Correct implementation of test case requirements (method, URL, headers, body, query params)
2. **Completeness**: All test case steps implemented, proper assertions for expected status
3. **Code Quality**: Clean code, proper error handling, no TODO/placeholder comments
4. **Framework Compliance**: Correct use of framework components, proper import statements
5. **API Focus**: Uses only API components (no UI/browser code), follows API testing patterns
6. **Assertions**: Proper validation of status codes, response content, error conditions
7. **Maintainability**: Well-structured, readable, follows naming conventions

## Specific Review Points:
- Does the script implement ALL steps from the test case?
- Are the HTTP method, URL, headers, body, and query parameters correctly set?
- Is the expected status code properly validated?
- Are imports correct and using only API components?
- Is error handling implemented appropriately?
- Are assertions comprehensive and meaningful?
- Does the code follow pytest conventions?
- Is the test function name descriptive and follows naming patterns?

## CRITICAL OUTPUT RULES:
- Return ONLY valid JSON starting with opening curly brace
- NO explanations, NO markdown formatting
- Use exact structure shown below

## EXACT JSON FORMAT REQUIRED:
{{
    "overall_summary": {{
        "overall_score": <0-100>,
        "implementation_status": "complete|partial|incomplete",
        "strengths": ["<strength1>", "<strength2>"],
        "critical_issues": ["<issue1>", "<issue2>"],
        "recommendations": ["<recommendation1>", "<recommendation2>"]
    }},
    "detailed_review": {{
        "accuracy": {{
            "score": <0-100>,
            "feedback": "<specific feedback on test case implementation accuracy>",
            "issues": ["<issue1>", "<issue2>"]
        }},
        "completeness": {{
            "score": <0-100>,
            "feedback": "<feedback on implementation completeness>",
            "missing_elements": ["<element1>", "<element2>"]
        }},
        "code_quality": {{
            "score": <0-100>,
            "feedback": "<feedback on code quality and structure>",
            "improvements": ["<improvement1>", "<improvement2>"]
        }},
        "framework_compliance": {{
            "score": <0-100>,
            "feedback": "<feedback on framework usage>",
            "violations": ["<violation1>", "<violation2>"]
        }},
        "api_focus": {{
            "score": <0-100>,
            "feedback": "<feedback on API-only implementation>",
            "ui_violations": ["<violation1>", "<violation2>"]
        }},
        "assertions": {{
            "score": <0-100>,
            "feedback": "<feedback on test assertions>",
            "missing_validations": ["<validation1>", "<validation2>"]
        }},
        "maintainability": {{
            "score": <0-100>,
            "feedback": "<feedback on code maintainability>",
            "style_issues": ["<issue1>", "<issue2>"]
        }}
    }},
    "implementation_check": {{
        "test_steps_implemented": <true|false>,
        "request_setup_correct": <true|false>,
        "expected_status_validated": <true|false>,
        "imports_correct": <true|false>,
        "api_only_components": <true|false>,
        "error_handling_present": <true|false>,
        "assertions_comprehensive": <true|false>
    }},
    "specific_feedback": {{
        "request_construction": "<feedback on how request is built>",
        "response_validation": "<feedback on response handling>",
        "test_structure": "<feedback on overall test structure>",
        "improvement_suggestions": ["<suggestion1>", "<suggestion2>"]
    }}
}}

IMPORTANT: Start response immediately with opening curly brace. No additional text before or after JSON."""
    
    return prompt