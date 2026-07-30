"""All prompts for Claude Sonnet 4 model."""
import json
import os
from typing import Dict


# def get_system_message() -> str:
#     """Get system message for Claude Sonnet 4."""
#     # return "You are a helpful assistant for API test case generation."
#     return "You are an expert API test engineer specializing in edge cases and boundary testing. Your role is to generate comprehensive, technically accurate test cases that follow strict JSON formatting rules. You must ensure all data types are correct and the output is valid, parseable JSON. CRITICAL: Never use JavaScript expressions, functions, or methods in JSON. Use only static values (strings, numbers, booleans, null, arrays, objects)."

# def get_testcase_prompt(api_spec: dict, review: str = None) -> str:
#     """
#     Generate testcase prompt for Claude Sonnet 4.
    
#     Args:
#         api_spec: API specification dictionary
#         review: Optional review/feedback to consider when generating test cases
        
#     Returns:
#         Formatted prompt string
#     """
#     prompt = (

#         "You are an expert API tester. Given the following API specification, "
#         "generate a comprehensive list of test cases covering ONLY edge and boundary scenarios.\n\n"

#         "CRITICAL RULES:\n"
#         "- Use ONLY the keys provided: method, url, headers, body, query_params.\n"
#         "- Reuse the exact values from the API specification as the baseline.\n"
#         "- Modify values ONLY to create edge or boundary conditions.\n"
#         "- Do NOT invent URLs, fields, headers, parameters, or sample values.\n\n"

#         "For each test case, provide:\n"
#         "- name\n"
#         "- code (TC001, TC002, ...)\n"
#         "- description\n"
#         "- preconditions (list only what is strictly required, derived from the spec)\n"
#         "- request (method, url, headers, body, query_params)\n"
#         "- expected_status\n"
#         "- steps (detailed, step-by-step manual instructions; "
#         "include request setup, value assignment, execution, and response verification)\n\n"

#         "Steps MUST:\n"
#         "- Reference the exact values used in the request\n"
#         "- Describe one concrete action per step\n"
#         "- Explicitly state header, body, and query parameter configuration\n"
#         "- End with response status-code verification\n\n"

#         "Focus on:\n"
#         "- Empty, null, missing, malformed, and oversized values of existing fields\n"
#         "- Incorrect data types for existing fields\n"
#         "- Missing or invalid existing headers\n"
#         "- Boundary or extreme values for existing query parameters\n\n"

#         "IMPORTANT:\n"
#         "- Return ONLY valid JSON\n"
#         "- Top-level key must be \"test_cases\"\n"
#         "- Do NOT include explanations or markdown\n\n"

#         f"API Specification:\n{json.dumps(api_spec, indent=2)}\n\n"
#     )
    
#     # Add review section if provided
#     if review:
#         review_section = (
#             "\n\n**REVIEW AND FEEDBACK TO CONSIDER:**\n"
#             f"{review}\n\n"
#             "Please carefully review the feedback above and adjust your test case generation accordingly. "
#             "Incorporate the suggestions, address any concerns mentioned, and fine-tune the test cases "
#             "based on the review. Ensure the generated test cases align with the feedback provided.\n\n"
#         )
#         prompt = prompt + review_section

#     return prompt



def get_system_message() -> str:
    """Get system message for Claude Sonnet 4."""
    return """
        You are a senior API test architect focused on specification-driven test design.
        Generate high-quality, technically accurate API test cases strictly from the provided API specification.
        Prioritize meaningful risk coverage (validation, auth, contract, boundary, negative paths) while remaining realistic and executable.
        Never invent endpoints, fields, headers, or payload structures not present in the specification context.
        Output must be strict JSON only, fully parseable, with correct data types and no markdown or prose outside JSON.
        Do not use JavaScript expressions/functions (e.g., .repeat(), Date.now(), Math.*) inside JSON.
        Use static literal values only (string, number, boolean, null, array, object)."""

def get_testcase_prompt(api_spec: dict, review: str = None) -> str:
    """
    Generate testcase prompt for Claude Sonnet 4.
    
    Args:
        api_spec: API specification dictionary
        review: Optional review/feedback to consider when generating test cases
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""You are an expert API tester. Based only on the API specification below, generate high-quality test cases.

GOAL:
- Produce a concise but comprehensive suite emphasizing edge, boundary, and negative validation scenarios.
- Keep every test case directly traceable to the API spec.

STRICT SPEC-DRIVEN RULES:
- Use ONLY keys: method, url, headers, body, query_params.
- Reuse API spec baseline values and mutate only what is needed for the scenario.
- Do NOT invent new endpoints, request fields, headers, query params, or business rules.
- If a section is absent in the spec (e.g., body/query_params), keep it as empty object {{}}.
- Keep request shape consistent with spec; only value-level perturbations unless testing missing required fields.

QUALITY REQUIREMENTS:
- Cover categories where applicable: required-field missing, null/empty, wrong type, format violation, boundary min/max, over-limit length/size, invalid enum/value, invalid auth/header, and malformed payload.
- Include at least one strong positive/nominal control case when feasible for comparison.
- Prefer realistic expected statuses (2xx/4xx/5xx) aligned with HTTP semantics and the scenario.
- Avoid duplicate cases; each case must test a unique risk.

FOR EACH TEST CASE, RETURN:
- name: short and specific
- code: TC001, TC002, ... (sequential, unique)
- description: concrete objective (<= 120 chars)
- preconditions: list of required setup items derived from spec/context only
- request: object with method, url, headers, body, query_params
- expected_status: integer HTTP status code
- steps: actionable execution + verification steps

STEPS MUST:
- Be explicit and reproducible (one concrete action per step)
- Reference exact request values used in that test case
- Include request setup, execution, and response verification
- End with status-code validation

OUTPUT CONTRACT (MANDATORY):
- Return ONLY valid JSON (no markdown, no comments, no extra text)
- Top-level JSON must be: {{"test_cases": [ ... ]}}
- Every test case must include all required keys
- Use only static JSON literals; never use JavaScript or pseudo-code

API Specification:
{json.dumps(api_spec, indent=2)}
"""
    
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



def get_testscript_system_message() -> str:
    """Get system message for testscript generation."""
    return "You are an expert test automation engineer specializing in API testing. Generate complete, executable pytest test functions using ONLY API components from the framework. NEVER use UI components (BasePage, BaseActions, Browser, WebDriver, Selenium) even if they appear in the framework analysis. Only use framework.api.* imports and API-related utilities. Never use generic or placeholder code."


def get_testscript_prompt(test_case_json: str, framework_section: str, components: Dict[str, str], 
                         review_section: str, test_case) -> str:
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


def get_framework_analysis_system_message() -> str:
    """Get system message for framework analysis."""
    return "You are an expert test automation framework analyzer. Extract detailed information including docstrings, method signatures, import paths, and usage patterns. Accurately identify and categorize components as API, UI, or common based on their actual purpose and usage."


def get_framework_analysis_prompt(framework_path: str) -> str:
    """
    Get the prompt for framework analysis.
    
    Args:
        framework_path: Path to the framework root directory
        
    Returns:
        Complete framework analysis prompt string
    """
    framework_root_name = os.path.basename(os.path.normpath(framework_path))
    
    # Build prompt in parts to avoid f-string nesting issues
    prompt_start = f"""You are an expert test automation framework analyzer. Analyze the provided framework code and extract comprehensive details.

⚠️ CRITICAL FIRST STEP - CHECK FRAMEWORK STRUCTURE:
Before you start extracting, look at the "# FRAMEWORK STRUCTURE INFORMATION" section at the beginning of the code.
It shows "DETECTED DIRECTORIES: ..." - this tells you which directories (api/, ui/, core/) exist in the framework.
YOU MUST EXTRACT COMPONENTS FROM ALL DIRECTORIES LISTED THERE!

If the structure shows "api, ui, core" - you MUST extract from all three:
- Extract ALL classes and functions from api/ directory → component_type: "api"
- Extract ALL classes and functions from ui/ directory → component_type: "ui"  
- Extract ALL classes and functions from core/ directory → component_type: "common"

If you only extract from api/ and ignore ui/ and core/, your analysis is INCOMPLETE and WRONG!

CRITICAL REQUIREMENTS:
1. FIRST: Check the "# DETECTED DIRECTORIES" line in the framework structure information - extract from ALL listed directories
2. Extract descriptions from docstrings (class/function docstrings, not just comments)
3. Accurately identify and categorize components as API, UI, or common based on their ACTUAL FILE LOCATION in the folder structure
4. Extract method signatures with full parameter details including type hints
5. Include CORRECT import paths for all components - they MUST start with '{framework_root_name}.'
6. Extract usage patterns and examples from actual import statements in the code
7. Look at existing import statements in the code files to understand the correct import paths
8. Extract ALL classes and functions - do not skip any directory or file

FRAMEWORK ROOT AND IMPORT PATHS:
- The framework root directory is: '{framework_root_name}'
- ALL import paths MUST start with '{framework_root_name}.'
- Example: If a file is at {framework_root_name}/api/requests/base_api.py, the import should be: from {framework_root_name}.api.requests.base_api import ClassName
- Look at the actual import statements in the code files to see how they import from each other
- The "# Import Path:" comment in each file shows the correct import path - USE IT

COMPONENT TYPE CATEGORIZATION (BASED ON FILE LOCATION):
- Files in '{framework_root_name}/api/' or any subdirectory under api/ → component_type: "api"
- Files in '{framework_root_name}/ui/' or any subdirectory under ui/ → component_type: "ui"
- Files in '{framework_root_name}/core/' or any subdirectory under core/ → component_type: "common"
- Files in any other location → component_type: "common"
- DO NOT guess based on class names - use the actual file path location

⚠️ MANDATORY DIRECTORY SCANNING PROCESS:
You MUST follow this step-by-step process:

STEP 1: Check the "# DETECTED DIRECTORIES" line in the framework structure information
STEP 2: For EACH directory listed (api/, ui/, core/), do the following:
  a) Find ALL Python files in that directory and its subdirectories
  b) Extract ALL classes from those files
  c) Extract ALL functions from those files
  d) Categorize them based on directory:
     - Files in api/ → component_type: "api"
     - Files in ui/ → component_type: "ui"
     - Files in core/ → component_type: "common"

STEP 3: Verify you extracted from ALL directories:
  - If "api" is in DETECTED DIRECTORIES → You MUST have components with component_type: "api"
  - If "ui" is in DETECTED DIRECTORIES → You MUST have components with component_type: "ui"
  - If "core" is in DETECTED DIRECTORIES → You MUST have components with component_type: "common"

FAILURE TO EXTRACT FROM ALL DIRECTORIES WILL RESULT IN INCOMPLETE ANALYSIS!
If you see files in core/ directory, extract them as "common" type components
If you see files in ui/ directory, extract them as "ui" type components  
If you see files in api/ directory, extract them as "api" type components
DO NOT skip any directory - scan the entire framework structure

1. Framework Components (CRITICAL - Extract ALL of these from ALL directories):

- **Base classes**: MUST extract ALL classes found in the framework (every "class ClassName:" definition). For each class:
  * Extract full docstring description (class-level docstring, triple-quoted strings)
  * Extract ALL methods with full signatures (including parameters, return types, decorators like @staticmethod, @classmethod)
  * Extract CORRECT import path - check the "# Import Path:" comment in the file or construct from file location
  * Import path format: from {framework_root_name}.module.submodule import ClassName
  * Categorize component_type based on file location: "api" if in api/, "ui" if in ui/, "common" if in core/ or elsewhere
  * Examples of what to look for:
    - API classes: APIConfiguration, RestRequest, RestResponse, APIResponse, APIClient, HttpClient
    - UI classes: BasePage, BaseLocator, BaseWait, Browser, WebDriver, PageObject, ElementLocator
    - Common/Core classes: LoggerFactory, PropFileReader, ConfigReader, FileHandler, DataManager, BaseActions, BaseVerifications, Utils, Helpers
  * DO NOT skip any classes - scan every file in EVERY directory (api/, ui/, core/, and others) and list every class definition
  * If a directory exists but has no classes, explicitly note that in your analysis
  
- **Utility functions**: MUST extract ALL functions from helper/utility files. For each function:
  * Extract full docstring description (function-level docstring)
  * Extract complete method signature with all parameters and return types
  * Extract usage patterns from actual import statements and usage in the code
  * Extract CORRECT import path - check existing imports in the code or construct from file location
  * Import path format: from {framework_root_name}.module.submodule import function_name
  * Look in files under: helpers/, utils/, common/, core/ directories AND any other utility directories
  * Examples of what to look for:
    - API utilities: build_url, rest_response_handle, convert_to_json, files_to_upload, validate_params, check_json_response, handle_http_error
    - UI utilities: wait_for_element, click_element, get_text, fill_form, scroll_to_element, take_screenshot
    - Common/Core utilities: read_config, get_logger, parse_json, format_date, validate_data, file_operations, string_utils
  * DO NOT skip any functions - scan every helper/utils/common/core file in ALL directories and list every function definition
  * If utility directories exist but have no functions, explicitly note that in your analysis
  
- **Client classes**: Identify the main client classes used for making requests/interactions:
  * API clients: RestRequest, APIClient, HttpClient (usually in api/requests/ or api/ directory)
  * UI clients: Browser, WebDriver (usually in ui/utils/ or ui/ directory)
  * Categorize based on file location (api/ = "api", ui/ = "ui")
  * Extract all methods with signatures
  * Use CORRECT import path from file location
  
- **Response classes**: Identify response handling classes:
  * API responses: APIResponse, RestResponse (usually in api/response/ directory)
  * UI responses: PageResponse, WebResponse (usually in ui/ directory)
  * Extract all methods and properties with signatures
  * Use CORRECT import path from file location
  
- **Assertion utilities**: MUST identify ALL assertion/validation utilities:
  * Classes with validation methods (e.g., RestResponse with validate_status_code, validate_protocol_version, etc.)
  * Standalone assertion functions (e.g., assert_response, validate_response)
  * Extract ALL validation methods with full signatures
  * Extract usage patterns from test files or actual code
  * Use CORRECT import path from file location
  * Examples: RestResponse class with static validation methods, assert_response function, etc.
  
- **Test markers and decorators**: Extract all pytest markers used (@pytest.mark.*)
- **Fixtures**: Identify pytest fixtures and their purposes

2. Test Organization:
- Test grouping strategies (markers, folders, naming patterns)
- Test method signatures with full details
- Data preparation patterns
- Common setup/teardown approaches
- Test markers used in the framework

3. Testing Patterns:
- Request construction patterns with code examples
- Response validation approaches with method signatures
- Error handling strategies
- Custom validation methods with signatures
- Status code checking patterns
- Content validation patterns
- Error checking patterns

4. Framework Standards:
- Naming conventions (test methods, variables, classes)
- File organization and structure
- Documentation formats (docstring patterns)
- Error message patterns
- Validation step formats

5. Import Information:
- For each component, provide the import statement needed to use it
- Include full import paths (e.g., "from {framework_root_name}.api.requests.base_api import RestRequest")

Provide the analysis in the following JSON structure:
"""
    
    # JSON template as regular string (not f-string) to avoid nesting issues
    json_template = """{
    "base_classes": {
        "ClassName": {
            "file": "relative/path/to/file.py (relative to framework root)",
            "description": "Extract FULL docstring from class definition - detailed description of purpose and usage",
            "import_path": "from {FRAMEWORK_ROOT}.module.submodule import ClassName (MUST start with {FRAMEWORK_ROOT}.)",
            "key_methods": [
                {"name": "method_name", "signature": "def method_name(self, param1: str, param2: int) -> bool", "description": "Extract method docstring if available"},
                {"name": "property_name", "signature": "@property def property_name(self) -> return_type", "description": "For properties, extract property name and return type"}
            ],
            "component_type": "api" or "ui" or "common (based on file location: api/ = api, ui/ = ui, core/ or other = common)"
        }
    },
    "NOTE_BASE_CLASSES": "CRITICAL: You MUST extract ALL classes you find in the code. If you see 'class APIConfiguration:', it MUST be in base_classes. If you see 'class RestRequest:', it MUST be in base_classes. If you see 'class BaseActions:', it MUST be in base_classes. Scan through ALL the code and list EVERY class definition you find. Example: If code contains 'class APIConfiguration:' and 'class RestRequest:', then base_classes must have both entries.",
    "utility_functions": {
        "function_name": {
            "file": "relative/path/to/file.py (relative to framework root)",
            "description": "Extract FULL docstring from function definition - what this function does",
            "import_path": "from {FRAMEWORK_ROOT}.module.submodule import function_name (MUST start with {FRAMEWORK_ROOT}.)",
            "signature": "def function_name(param1: str, param2: int) -> dict (include ALL parameters and return type)",
            "usage_pattern": "Example of how it's used in the actual framework code (look at import statements and usage)"
        }
    },
    "NOTE_UTILITIES": "CRITICAL: You MUST extract ALL functions from helper/utility files. If you see 'def build_url(' in the code, it MUST be in utility_functions. If you see 'def validate_params(' in the code, it MUST be in utility_functions. Scan through ALL helper files and list EVERY function definition you find. Example: If code contains 'def build_url(' and 'def validate_params(', then utility_functions must have both entries.",
    "patterns": {
        "test_setup": ["Pattern descriptions with examples"],
        "assertions": ["Assertion patterns with method signatures"],
        "request_patterns": ["How requests are constructed"],
        "response_handling": ["How responses are handled"],
        "status_checks": ["Status code validation patterns"],
        "content_checks": ["Content validation patterns"],
        "error_checks": ["Error handling patterns"]
    },
    "client_class": {
        "name": "RestRequest",
        "file": "api/requests/base_api.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.requests.base_api import RestRequest (MUST start with {FRAMEWORK_ROOT}.)",
        "key_methods": [
            {"name": "requests_get", "signature": "@staticmethod def requests_get(config: APIConfiguration) -> APIResponse", "description": "Http Get request and returns APIResponse object"},
            {"name": "requests_post", "signature": "@staticmethod def requests_post(config: APIConfiguration, data=None, json_data=None, files=None) -> APIResponse", "description": "Http Post request and returns APIResponse object"},
            {"name": "request_put", "signature": "@staticmethod def request_put(config: APIConfiguration, data=None, json_data=None, *files) -> APIResponse", "description": "Http Put request and returns APIResponse object"},
            {"name": "request_delete", "signature": "@staticmethod def request_delete(config: APIConfiguration, data=None) -> APIResponse", "description": "Http Delete request and returns APIResponse object"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    },
    "response_class": {
        "name": "APIResponse",
        "file": "api/response/response_validator.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.response.response_validator import APIResponse (MUST start with {FRAMEWORK_ROOT}.)",
        "key_properties": [
            {"name": "status_code", "signature": "@property def status_code(self) -> int", "description": "Returns HTTP status code"},
            {"name": "json_response", "signature": "@property def json_response(self) -> dict", "description": "Returns JSON response as dict"},
            {"name": "text", "signature": "@property def text(self) -> str", "description": "Returns response text"},
            {"name": "response", "signature": "@property def response(self) -> requests.Response", "description": "Returns raw response object"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    },
    "assertion_utils": {
        "name": "RestResponse",
        "file": "api/response/response_validator.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.response.response_validator import RestResponse (MUST start with {FRAMEWORK_ROOT}.)",
        "key_methods": [
            {"name": "validate_status_code", "signature": "@staticmethod def validate_status_code(response: requests.Response, expected_status_code: int) -> bool", "description": "Validates HTTP status code"},
            {"name": "validate_protocol_version", "signature": "@staticmethod def validate_protocol_version(response: requests.Response, expected_version: str) -> bool", "description": "Validates HTTP protocol version"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    },
    "config_class": {
        "name": "APIConfiguration",
        "file": "api/requests/base_api.py (relative to framework root)",
        "description": "Extract from docstring",
        "import_path": "from {FRAMEWORK_ROOT}.api.requests.base_api import APIConfiguration (MUST start with {FRAMEWORK_ROOT}.)",
        "key_methods": [
            {"name": "__init__", "signature": "def __init__(self) -> None", "description": "Initialize configuration"},
            {"name": "addHeader", "signature": "def addHeader(self, key: str, value: str) -> None", "description": "Add header"},
            {"name": "addAccept", "signature": "def addAccept(self, value: str) -> None", "description": "Add Accept header"},
            {"name": "addContentType", "signature": "def addContentType(self, value: str) -> None", "description": "Add Content-Type header"}
        ],
        "attributes": [
            {"name": "base_url", "type": "str", "description": "Base URL for API calls"},
            {"name": "end_point", "type": "str", "description": "API endpoint path"},
            {"name": "headers", "type": "dict", "description": "HTTP headers"},
            {"name": "params", "type": "dict", "description": "Query parameters"}
        ],
        "component_type": "api (based on file location in api/ directory)"
    }
}"""
    
    # Continue with rest of prompt (abbreviated for length - full version would include all the detailed requirements)
    prompt_end = f"""

CRITICAL REQUIREMENTS - MUST FOLLOW (READ CAREFULLY):

1. **BASE CLASSES EXTRACTION (MANDATORY)**:
   - Scan ALL Python files in the framework code
   - For EVERY class definition found (class ClassName:), extract it as a base class
   - Look for classes like: APIConfiguration, RestRequest, RestResponse, APIResponse, BaseActions, BaseVerifications, BasePage, BaseLocator, BaseWait, LoggerFactory, PropFileReader, Browser, etc.
   - DO NOT skip any classes - if you see "class Something" in the code, it MUST be in base_classes
   - Extract the class docstring (triple-quoted string right after class definition)
   - Extract ALL methods from each class with their FULL signatures (including decorators, parameters with types, return types)
   - Determine component_type based on FILE LOCATION:
     * "api" if file is in {framework_root_name}/api/ or any subdirectory
     * "ui" if file is in {framework_root_name}/ui/ or any subdirectory  
     * "common" if file is in {framework_root_name}/core/ or any other location
   - Use the "# Import Path:" comment in each file to get the correct import path
   - Import path MUST start with '{framework_root_name}.'

2. **UTILITY FUNCTIONS EXTRACTION (MANDATORY)**:
   - Scan ALL Python files for function definitions (def function_name:)
   - Look for functions in helper/utility files, especially in "helpers", "utils", "common" directories
   - Extract ALL functions like: build_url, check_json_response, validate_params, rest_response_handle, convert_to_json, files_to_upload, handle_http_error, etc.
   - DO NOT skip any utility functions - if you see "def helper_function" in helper/utils files, it MUST be in utility_functions
   - Extract function docstring (triple-quoted string)
   - Extract FULL function signature with ALL parameters (including types) and return type
   - Use the "# Import Path:" comment in each file or construct from file location
   - Import path MUST start with '{framework_root_name}.'
   - Look at actual import statements in the code to see how these functions are imported

3. **ASSERTION UTILITIES EXTRACTION (MANDATORY)**:
   - Look for classes with validation methods (RestResponse, APIResponse, etc.)
   - Look for standalone assertion functions (assert_response, validate_response, etc.)
   - If you find a class like RestResponse with methods like validate_status_code, validate_protocol_version, validate_reason_phrase, etc. - this IS an assertion utility
   - Extract the class/function docstring
   - Extract ALL validation methods with their FULL signatures (including @staticmethod, @classmethod decorators)
   - Extract usage patterns from test files or actual code usage
   - Use CORRECT import path - check "# Import Path:" comment or construct from file location
   - Import path MUST start with '{framework_root_name}.'

4. **IMPORT PATH CONSTRUCTION (CRITICAL)**:
   - ALWAYS check the "# Import Path:" comment at the top of each file - it shows the correct import path
   - If not available, construct from file location: {framework_root_name}.module.submodule
   - Example: File at {framework_root_name}/api/helpers/helper_api.py → import_path: "from {framework_root_name}.api.helpers.helper_api import function_name"
   - Look at existing import statements in the code files to understand the import pattern
   - ALL import paths MUST start with '{framework_root_name}.' - never use relative imports or just module names

5. **COMPONENT TYPE CATEGORIZATION (CRITICAL)**:
   - Use FILE LOCATION, not class names, to determine component_type
   - Check the "# File:" comment at the top of each file to see the location
   - Files in api/ directory → "api"
   - Files in ui/ directory → "ui"
   - Files in core/ directory → "common"
   - Any other location → "common"
   - DO NOT guess based on class names like "API" or "UI" in the name

6. Extract ALL descriptions from docstrings (triple-quoted strings) - Use class-level and function-level docstrings, not comments.
7. Extract method signatures with FULL type hints - Include all parameters with types and return types. This is CRITICAL for code generation.
8. Extract ALL properties from classes - CRITICAL for response classes.
9. Extract COMPLETE configuration class details.
10. Provide COMPLETE usage examples from the actual code - Show end-to-end usage.
11. Be thorough and detailed - This will be used to generate test scripts, so completeness is critical.
12. Identify ALL relevant components regardless of type - The framework may support both API and UI testing.
13. EXPLICITLY CHECK FOR CORE AND UI COMPONENTS.
14. **MODULE ORGANIZATION (CRITICAL FOR TEST GENERATION)**.

REMEMBER: 
- The goal is to extract COMPLETE framework information. Missing base classes, utilities, or assertion methods will result in poor test script generation.
- If you see a class or function in the code, it MUST appear in the JSON response.
- DO NOT return empty base_classes or utility_functions if you see classes/functions in the code.
- ALL import paths MUST start with '{framework_root_name}.' - check the "# Import Path:" comments in files.
- Use FILE LOCATION to determine component_type, not class names.
- SCAN ALL DIRECTORIES: You MUST check api/, ui/, core/, and any other directories. Do not assume a framework only has API components.
- If you find components in core/ directory, they are "common" type. If you find components in ui/ directory, they are "ui" type.
- Be thorough: Extract ALL classes, ALL functions, ALL methods with FULL signatures. This information is critical for generating accurate test scripts.
- Include detailed method signatures with parameter types and return types - this is essential for code generation."""

    return prompt_start + json_template.replace("{FRAMEWORK_ROOT}", framework_root_name) + prompt_end


def get_judge_system_message() -> str:
    """Get system message for test case judge agent."""
    return "You are a senior API test quality reviewer and judge. Evaluate test cases objectively based on technical accuracy, completeness, and professional standards. Provide constructive feedback and specific improvement recommendations. Output ONLY valid JSON - no explanations, no markdown formatting."


def get_judge_prompt(test_cases_json: str, api_spec_dict: dict) -> str:
    """
    Generate judge prompt for test case evaluation.
    
    Args:
        test_cases_json: JSON string of test cases to review
        api_spec_dict: API specification dictionary
        
    Returns:
        Formatted judge prompt string
    """
    api_spec_context = f"## API Specification:\n{json.dumps(api_spec_dict, indent=2)}\n\n" if api_spec_dict else ""
    
    prompt = f"""You are an expert test case reviewer. Evaluate test cases based on quality dimensions and provide structured feedback.

{api_spec_context}## Test Cases to Review:
{test_cases_json}

## Evaluation Criteria (Score 0-100 each):
1. **Accuracy**: Technical correctness (HTTP methods, endpoints, headers, body structures)
2. **Consistency**: Uniform naming, structure, format patterns
3. **Factualness**: Correct descriptions, status codes, assertions per API spec
4. **Completeness**: Coverage of positive, negative, edge cases, boundary values
5. **Clarity**: Clear names, descriptions, understandable steps
6. **Relevance**: Meaningful scenarios for the API being tested
7. **Maintainability**: Well-structured, easy to maintain

## CRITICAL OUTPUT RULES:
- Return ONLY valid JSON starting with opening curly brace
- NO explanations, NO markdown formatting
- Use exact structure shown below

## EXACT JSON FORMAT REQUIRED:
{{
    "overall_summary": {{
        "total_test_cases": <number>,
        "average_score": <number>,
        "strengths": ["<strength1>", "<strength2>"],
        "common_issues": ["<issue1>", "<issue2>"],
        "recommendations": ["<recommendation1>", "<recommendation2>"]
    }},
    "test_case_reviews": [
        {{
            "test_case_code": "<code>",
            "test_case_name": "<name>",
            "overall_score": <0-100>,
            "dimension_scores": {{
                "accuracy": <0-100>,
                "consistency": <0-100>,
                "factualness": <0-100>,
                "completeness": <0-100>,
                "clarity": <0-100>,
                "relevance": <0-100>,
                "maintainability": <0-100>
            }},
            "feedback": "<specific feedback>",
            "issues": ["<issue1>", "<issue2>"],
            "strengths": ["<strength1>", "<strength2>"]
        }}
    ]
}}

IMPORTANT: Start response immediately with opening curly brace. No additional text before or after JSON."""
    
    return prompt


def get_testscript_judge_system_message():
    """Get system message for test script judge agent."""
    return "You are an expert test script reviewer. Evaluate the provided test script based on technical accuracy, completeness, and adherence to best practices. Provide specific feedback and improvement recommendations. Output ONLY valid JSON - no explanations, no markdown formatting."

# ...existing code...

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