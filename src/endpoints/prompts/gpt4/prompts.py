"""All prompts for GPT-4.1-mini model."""
import json


def get_system_message() -> str:
    """Get system message for GPT-4.1-mini testcase generation."""
    return "You are a helpful assistant for API test case generation."


def get_testcase_prompt(api_spec: dict, review: str = None) -> str:
    """
    Build enhanced prompt for GPT-4.1 that handles any API input structure.
    
    Args:
        api_spec: API specification dictionary (can contain any structure)
        review: Optional review/feedback to consider when generating test cases
        
    Returns:
        Formatted prompt string that works with any API specification
    """
    # Safely extract values with defaults
    method = api_spec.get("method", "GET").upper()
    url = api_spec.get("url", "")
    headers = api_spec.get("headers") or {}
    body = api_spec.get("body")
    query_params = api_spec.get("query_params") or {}
    
    # Detect path parameters in URL (e.g., {id}, {userId}, /api/users/{id}/posts)
    path_params = []
    if url:
        import re
        path_param_pattern = r'\{([^}]+)\}'
        path_params = re.findall(path_param_pattern, url)
    
    # Build dynamic API spec description
    api_spec_section = f"""API Specification:
- HTTP Method: {method}
- Endpoint URL: {url}"""
    
    if path_params:
        api_spec_section += f"\n- Detected Path Parameters: {', '.join(path_params)}"
    
    if headers:
        api_spec_section += f"\n- Headers: {json.dumps(headers, indent=2)}"
    else:
        api_spec_section += "\n- Headers: None (or not specified)"
    
    if body is not None:
        api_spec_section += f"\n- Request Body: {json.dumps(body, indent=2)}"
    else:
        api_spec_section += "\n- Request Body: None (not applicable for this method)"
    
    if query_params:
        api_spec_section += f"\n- Query Parameters: {json.dumps(query_params, indent=2)}"
    else:
        api_spec_section += "\n- Query Parameters: None"
    
    # Determine what to focus on based on HTTP method
    method_guidance = {
        "GET": "Focus on query parameters, path parameters, and headers. No request body expected.",
        "POST": "Focus on request body validation, query parameters, path parameters, and headers.",
        "PUT": "Focus on request body validation (full resource update), path parameters, and headers.",
        "PATCH": "Focus on request body validation (partial resource update), path parameters, and headers.",
        "DELETE": "Focus on path parameters, query parameters, headers, and idempotency testing.",
        "HEAD": "Focus on headers and path parameters. No request body expected.",
        "OPTIONS": "Focus on headers and CORS-related testing."
    }
    method_focus = method_guidance.get(method, "Analyze all components based on the API structure.")
    
    prompt = f"""You are an expert API test case generator. Generate comprehensive test cases for the following API endpoint using advanced testing methodologies.

{api_spec_section}

HTTP Method Guidance: {method_focus}

**INSTRUCTIONS - Analyze the provided API specification and generate test cases based on what is actually present:**

1. **Dynamic Structure Analysis**:
   - Analyze the actual structure of headers, body, query_params, and path parameters
   - Identify data types (string, number, boolean, array, object, null)
   - Detect nested structures and arrays
   - Identify required vs optional fields based on context
   - Detect authentication mechanisms (Bearer tokens, API keys, Basic auth, etc.)
   - Identify content types (JSON, form-data, multipart, etc.)

2. **Path Parameter Testing** (if path parameters are detected in URL):
   - If URL contains path parameters (e.g., {{id}}, {{userId}}, {{resourceId}}):
     * Valid numeric values: 1, 100, 999999
     * Zero value: 0
     * Negative value: -1
     * Non-numeric: "abc", "test123", "invalid"
     * Very large numbers: 2147483647 (32-bit max), 9223372036854775807 (64-bit max)
     * Empty string: ""
     * Special characters: "test@123", "test#id"
     * UUID format (if applicable): "550e8400-e29b-41d4-a716-446655440000"
   - Replace path parameters with actual test values in the URL
   - If no path parameters exist, skip this section

3. **Query Parameter Testing** (if query parameters are present):
   - Analyze each query parameter's expected type and format
   - Missing individual parameters (test each one separately)
   - Missing all parameters
   - Empty string values: ""
   - Valid values based on inferred type
   - Invalid data types (string where number expected, etc.)
   - Very long strings: 1000+ characters
   - Special characters: test both raw and URL-encoded
   - Unicode characters: emojis, non-ASCII characters
   - Boundary values: min, max, min-1, max+1, zero, negative
   - Invalid enum values (if enum-like patterns detected)
   - If no query parameters exist, skip this section

4. **Request Body Testing** (if body is present and method supports body):
   - Analyze the body structure (object, array, primitive, nested)
   - For object bodies:
     * Missing required fields (test each field individually)
     * Invalid data types for each field
     * Empty/null values for required fields
     * Very long strings: 1000+ characters
     * Special characters and Unicode
     * Nested object validation (if nested structures exist)
     * Empty arrays/objects
     * Invalid format validation (email, date, URL patterns if detected)
     * Boundary values for numeric fields
   - For array bodies:
     * Empty array: []
     * Single element array
     * Large array (100+ elements)
     * Invalid element types
     * Nested arrays (if applicable)
   - For primitive bodies:
     * Valid values
     * Invalid types
     * Boundary values
     * Empty/null values
   - If no body is present or method doesn't support body, skip this section

5. **Header Testing**:
   - Analyze authentication headers (Authorization, API-Key, etc.)
   - Missing authentication headers (if auth is detected)
   - Invalid/expired tokens (if Bearer token detected)
   - Missing required headers (Content-Type, Accept, etc.)
   - Invalid header values
   - Case sensitivity testing
   - If no headers specified, test with minimal/default headers

6. **Boundary Value Analysis (BVA)**:
   - Apply to ALL numeric fields (integers, floats) found in body, query params, or path params:
     * Minimum valid value: 1, 0.01, etc.
     * Maximum valid value: 2147483647 (32-bit int), 9223372036854775807 (64-bit int)
     * Just below minimum: min - 1
     * Just above maximum: max + 1
     * Zero: 0
     * Negative: -1 (if applicable)
   - Apply to ALL string fields:
     * Empty string: ""
     * Single character: "a"
     * Very long string: 1000+ characters
     * Boundary lengths: 255, 1024, 2048 characters

7. **Equivalence Partitioning**:
   - For each input field, identify valid and invalid equivalence classes
   - Test at least one value from each valid partition
   - Test at least one value from each invalid partition
   - Test boundary values between partitions

8. **Security Testing** (apply to all string inputs):
   - SQL injection: "'; DROP TABLE users; --", "' OR '1'='1", "1' OR '1'='1"
   - XSS attempts: "<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>"
   - Command injection: "; ls -la", "| cat /etc/passwd", "&& whoami"
   - Path traversal: "../../etc/passwd", "..\\..\\windows\\system32"
   - NoSQL injection: {{"$ne": null}}, {{"$gt": ""}}
   - LDAP injection: "*)(&", "admin)(&(password=*"
   - Missing/Invalid authentication (if auth headers detected)
   - Authorization bypass attempts

9. **Positive Test Cases (Happy Path)**:
   - Valid request with all required fields present
   - Valid request with optional fields included
   - Valid request with boundary values (min, max, zero where applicable)
   - Valid request with typical real-world values

10. **Negative Test Cases (Error Handling)**:
    - Missing required fields (test each individually)
    - Invalid data types for each field
    - Empty/null values for required fields
    - Invalid formats (dates, emails, URLs if detected)
    - Values exceeding limits
    - Invalid enum values (if patterns suggest enums)
    - Malformed JSON (if body is JSON)
    - Invalid HTTP method (if applicable)

**Test Case Structure:**
For each test case, provide:
{{
    "name": "Descriptive test case name indicating what is being tested",
    "code": "UNIQUE_TEST_CODE (e.g., TC_BVA_001, TC_SEC_002, TC_EDGE_003)",
    "description": "Detailed description of what this test validates and why",
    "request": {{
        "method": "{method}",
        "url": "<actual URL with path params replaced if applicable>",
        "headers": {{"<actual headers to use, or omit if not applicable>"}},
        "body": {{"<actual body to use, or omit if not applicable>"}},
        "query_params": {{"<actual query params to use, or omit if not applicable>"}}
    }},
    "expected_status": <appropriate HTTP status code: 200, 201, 400, 401, 403, 404, 422, 500>,
    "steps": [
        "Step 1: Prepare test data and setup",
        "Step 2: Send HTTP {method} request with specified parameters",
        "Step 3: Verify response status code matches expected_status",
        "Step 4: Verify response body structure and content (if applicable)",
        "Step 5: Verify response headers (if applicable)"
    ]
}}

**Critical Requirements:**
- Analyze the ACTUAL structure provided - do not assume fields that don't exist
- Generate as many test cases as possible covering all applicable techniques above
- Use unique test codes with technique prefixes: TC_BVA_ (Boundary), TC_SEC_ (Security), TC_EDGE_ (Edge Cases), TC_POS_ (Positive), TC_NEG_ (Negative), TC_EP_ (Equivalence Partitioning)
- Expected status codes should be realistic: 200/201 (success), 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation error), 500 (server error)
- Ensure test cases are independent and can run in any order
- Replace path parameters in URL with actual test values (e.g., replace {{id}} with 1, 0, -1, "abc", etc.)
- If a component (body, query_params, headers) is not present or not applicable, omit it from test cases
- Adapt test cases to the HTTP method: GET focuses on params, POST/PUT/PATCH on body, DELETE on idempotency
- Handle nested structures recursively if present
- Detect and test authentication/authorization if auth headers are present

**Output Format:**
CRITICAL: Return ONLY a valid JSON array. Do not include any markdown formatting, code blocks, explanatory text, or comments.
- Start with '[' and end with ']'
- Ensure all JSON is properly formatted with no trailing commas
- All strings must be properly escaped
- Return ONLY the JSON array, nothing else"""

    # Add review section if provided
    if review:
        review_section = f"""

**REVIEW AND FEEDBACK TO CONSIDER:**
{review}

Please carefully review the feedback above and adjust your test case generation accordingly. 
Incorporate the suggestions, address any concerns mentioned, and fine-tune the test cases 
based on the review. Ensure the generated test cases align with the feedback provided.
- If the review mentions missing test scenarios, add those test cases
- If the review suggests improvements to existing test cases, incorporate those improvements
- If the review points out issues with test case structure or format, adjust accordingly
- Prioritize the feedback when generating test cases"""
        prompt += review_section

    return prompt

