import openai
from openai import AzureOpenAI
import json
import logging
from endpoints.prompts.gpt4 import get_testcase_prompt, get_system_message

logger = logging.getLogger(__name__)

class TestCaseGeneratorGPT4:
    """
    GPT-4.1 based test case generator for API testing.
    Uses advanced prompt engineering for comprehensive test case generation.
    """

    def __init__(self, api_key: str):
        """
        Initialize the GPT-4.1 test case generator.
        
        Args:
            api_key: Azure OpenAI API key
        """
        openai.api_key = api_key
        self.api_key = api_key

    def generate(self, api_spec: dict, review: str = None) -> list:
        """
        Generate comprehensive test cases using GPT-4.1 model.
        
        Args:
            api_spec: API specification dictionary containing method, url, headers, body, query_params
            review: Optional review/feedback to consider when generating test cases
            
        Returns:
            List of test case dictionaries with name, code, description, request, expected_status, steps
        """
        # Use prompt from prompts folder
        prompt = get_testcase_prompt(api_spec, review)
        
        try:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-02-01",
                azure_endpoint="https://ai-proxy.lab.epam.com",
                timeout=120.0  # 2 minute timeout for GPT-4.1
            )

            response = client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",   # Match your Azure deployment name exactly
                messages=[
                    {
                        "role": "system", 
                        "content": get_system_message()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=8192,  # Default token limit
                temperature=0.3,  # Default temperature for consistent output
            )

            # Parse the response content as JSON
            content = response.choices[0].message.content.strip()
            
            logger.info(f"GPT-4.1 response received, length: {len(content)} characters")

            import re
            
            # Step 1: Remove markdown code blocks if present
            content_clean = content
            if '```json' in content_clean:
                match = re.search(r'```json\s*(.*?)\s*```', content_clean, re.DOTALL)
                if match:
                    content_clean = match.group(1).strip()
                    logger.info("Extracted JSON from markdown code block")
            elif '```' in content_clean:
                match = re.search(r'```\s*(.*?)\s*```', content_clean, re.DOTALL)
                if match:
                    content_clean = match.group(1).strip()
                    logger.info("Extracted JSON from code block")

            # Step 2: Try direct parsing
            try:
                test_cases = json.loads(content_clean)
                logger.info(f"Successfully parsed {len(test_cases)} test cases from GPT-4.1")
                return test_cases
            except json.JSONDecodeError as e:
                error_pos = getattr(e, 'pos', None)
                logger.warning(f"Direct JSON parsing failed: {str(e)}. Attempting to fix JSON...")
                if error_pos:
                    logger.debug(f"Error at position {error_pos}: {content_clean[max(0, error_pos-100):min(len(content_clean), error_pos+100)]}")
                
                # Step 3: Fix improperly escaped quotes in string values
                def fix_escaped_quotes(text):
                    """Fix improperly escaped quotes in JSON string values"""
                    original_text = text
                    
                    # Fix patterns like: "key": \"value\" -> "key": "value"
                    # This handles cases where quotes are escaped at string boundaries
                    text = re.sub(r':\s*\\"([^"]*)\\"', r': "\1"', text)
                    
                    # Fix nested JSON objects in strings (NoSQL injection patterns)
                    # Pattern: "key": \"{\"$ne\": null}\" -> "key": "{\"$ne\": null}"
                    def fix_nested_json_string(match):
                        key = match.group(1)
                        value = match.group(2)
                        # Remove outer escaped quotes
                        if value.startswith('\\"') and value.endswith('\\"'):
                            value = value[2:-2]  # Remove outer \"
                            # Properly escape inner quotes for JSON
                            value = value.replace('\\"', '"').replace('"', '\\"')
                        return f'"{key}": "{value}"'
                    
                    # Match patterns like: "key": \"{\"$ne\": null}\"
                    text = re.sub(r'"([^"]+)":\s*\\"({[^}]+})\\"', fix_nested_json_string, text)
                    
                    # Fix patterns like: "key": \"{\\\"$ne\\\": null}\"
                    def fix_double_escaped(match):
                        key = match.group(1)
                        value = match.group(2)
                        # Remove outer escaped quotes and fix double escaping
                        if value.startswith('\\"') and value.endswith('\\"'):
                            value = value[2:-2]
                            # Fix double-escaped quotes: \\\" -> \"
                            value = value.replace('\\\\"', '\\"')
                            # Then properly escape for JSON
                            value = value.replace('"', '\\"')
                        return f'"{key}": "{value}"'
                    
                    text = re.sub(r'"([^"]+)":\s*\\"({[^}]+})\\"', fix_double_escaped, text)
                    
                    # More aggressive fix: Find any pattern where a string value has escaped quotes
                    # Pattern: "key": \"anything\" -> "key": "anything" (with proper escaping)
                    def fix_any_escaped_string(match):
                        key = match.group(1)
                        value = match.group(2)
                        # If value starts and ends with \", remove them and properly escape
                        if value.startswith('\\"') and value.endswith('\\"'):
                            # Remove outer escaped quotes
                            inner = value[2:-2]
                            # Unescape any inner escaped quotes first
                            inner = inner.replace('\\"', '"')
                            # Then properly escape for JSON
                            inner = inner.replace('"', '\\"')
                            return f'"{key}": "{inner}"'
                        return match.group(0)  # Return unchanged if pattern doesn't match
                    
                    # Match: "key": \"...\" where ... can contain anything
                    text = re.sub(r'"([^"]+)":\s*\\"((?:[^"\\]|\\.)*)\\"', fix_any_escaped_string, text)
                    
                    if text != original_text:
                        logger.debug("Fixed escaped quotes in JSON")
                    
                    return text
                
                # Step 4: Fix JavaScript expressions (like "a".repeat(256))
                def fix_javascript_expressions(text):
                    """Replace JavaScript expressions with actual values"""
                    # Fix .repeat() expressions
                    def replace_repeat(match):
                        char = match.group(1)
                        count = int(match.group(2))
                        return '"' + (char * count) + '"'
                    text = re.sub(r'"([^"]+)"\.repeat\((\d+)\)', replace_repeat, text)
                    return text
                
                # Apply fixes in order
                content_fixed = fix_escaped_quotes(content_clean)
                content_fixed = fix_javascript_expressions(content_fixed)
                
                # Step 5: Fix common JSON issues (trailing commas)
                content_fixed = re.sub(r',\s*}', '}', content_fixed)
                content_fixed = re.sub(r',\s*]', ']', content_fixed)
                content_fixed = re.sub(r',(\s*[}\]])', r'\1', content_fixed)
                
                try:
                    test_cases = json.loads(content_fixed)
                    logger.info(f"Successfully parsed {len(test_cases)} test cases after fixing JSON")
                    return test_cases
                except json.JSONDecodeError as e2:
                    error_pos = getattr(e2, 'pos', None)
                    logger.warning(f"JSON fixing failed: {str(e2)}. Attempting extraction...")
                    if error_pos:
                        logger.debug(f"Error at position {error_pos} after fixes: {content_fixed[max(0, error_pos-200):min(len(content_fixed), error_pos+200)]}")
                
                # Step 6: Extract individual test case objects using balanced brace counting
                # This is more robust than regex for malformed JSON
                test_cases = []
                array_start = content_fixed.find('[')
                if array_start != -1:
                    brace_count = 0
                    obj_start = -1
                    in_string = False
                    escape_next = False
                    
                    for i in range(array_start + 1, min(len(content_fixed), array_start + 500000)):
                        char = content_fixed[i]
                        
                        if escape_next:
                            escape_next = False
                            continue
                        if char == '\\':
                            escape_next = True
                            continue
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        if not in_string:
                            if char == '{':
                                if brace_count == 0:
                                    obj_start = i
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0 and obj_start >= 0:
                                    obj_str = content_fixed[obj_start:i+1]
                                    try:
                                        test_case = json.loads(obj_str)
                                        if isinstance(test_case, dict) and 'name' in test_case and 'code' in test_case:
                                            # Avoid duplicates
                                            if not any(tc.get('code') == test_case.get('code') for tc in test_cases):
                                                test_cases.append(test_case)
                                    except json.JSONDecodeError:
                                        # Try fixing this individual object
                                        try:
                                            obj_fixed = fix_escaped_quotes(obj_str)
                                            obj_fixed = re.sub(r',(\s*[}\]])', r'\1', obj_fixed)
                                            test_case = json.loads(obj_fixed)
                                            if isinstance(test_case, dict) and 'name' in test_case and 'code' in test_case:
                                                if not any(tc.get('code') == test_case.get('code') for tc in test_cases):
                                                    test_cases.append(test_case)
                                        except json.JSONDecodeError:
                                            pass
                                    obj_start = -1
                            elif char == ']' and brace_count == 0:
                                break
                    
                    if test_cases:
                        logger.info(f"Recovered {len(test_cases)} test cases using balanced brace extraction")
                        return test_cases
                
                # Step 7: Extract JSON array (fallback approach)
                match = re.search(r'\[.*\]', content_fixed, re.DOTALL)
                
                if match:
                    extracted = match.group(0)
                    # Fix JavaScript expressions in extracted JSON
                    extracted_fixed = fix_javascript_expressions(extracted)
                    # Try to fix extracted JSON
                    extracted_fixed = re.sub(r',\s*}', '}', extracted_fixed)
                    extracted_fixed = re.sub(r',\s*]', ']', extracted_fixed)
                    extracted_fixed = re.sub(r',(\s*[}\]])', r'\1', extracted_fixed)
                    
                    try:
                        test_cases = json.loads(extracted_fixed)
                        logger.info(f"Successfully extracted and parsed {len(test_cases)} test cases")
                        return test_cases
                    except json.JSONDecodeError as parse_error:
                        logger.error(f"Failed to parse extracted JSON: {str(parse_error)}")
                        # Log problematic section for debugging
                        error_pos = getattr(parse_error, 'pos', None)
                        if error_pos:
                            start = max(0, error_pos - 200)
                            end = min(len(extracted_fixed), error_pos + 200)
                            logger.debug(f"Problematic JSON section: {extracted_fixed[start:end]}")
                
                # Step 8: Try to find JSON object with test_cases key
                match = re.search(r'\{.*"test_cases".*\}', content_fixed, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                        if "test_cases" in parsed and isinstance(parsed["test_cases"], list):
                            logger.info(f"Found test_cases key, extracted {len(parsed['test_cases'])} test cases")
                            return parsed["test_cases"]
                    except json.JSONDecodeError:
                        pass
                
                # Step 9: Last resort - try to extract individual test cases by finding "name" and "code" patterns
                if not test_cases:
                    # Look for objects that have both "name" and "code" keys
                    test_case_pattern = r'\{\s*"name"\s*:\s*"[^"]*"\s*,\s*"code"\s*:\s*"[^"]*".*?\}'
                    potential_objects = re.findall(test_case_pattern, content_fixed, re.DOTALL)
                    
                    for obj_str in potential_objects:
                        try:
                            # Try to make it valid JSON
                            if not obj_str.strip().startswith('{'):
                                continue
                            # Try to close the object if needed
                            if obj_str.count('{') > obj_str.count('}'):
                                obj_str += '}' * (obj_str.count('{') - obj_str.count('}'))
                            
                            # Fix escaped quotes
                            obj_fixed = fix_escaped_quotes(obj_str)
                            obj_fixed = re.sub(r',(\s*[}\]])', r'\1', obj_fixed)
                            
                            test_case = json.loads(obj_fixed)
                            if isinstance(test_case, dict) and 'name' in test_case and 'code' in test_case:
                                if not any(tc.get('code') == test_case.get('code') for tc in test_cases):
                                    test_cases.append(test_case)
                        except json.JSONDecodeError:
                            pass
                    
                    if test_cases:
                        logger.info(f"Recovered {len(test_cases)} test cases using pattern matching")
                        return test_cases
                
                logger.error("Could not extract valid JSON from GPT-4.1 response")
                logger.error(f"Response length: {len(content)} characters")
                logger.debug(f"Response content (first 2000 chars): {content[:2000]}")
                logger.debug(f"Response content (last 500 chars): {content[-500:]}")
                
                # Try one more time with a more aggressive approach: extract all valid JSON objects
                # This is a last resort to salvage any valid test cases
                try:
                    # Find all potential JSON objects that look like test cases (use content_fixed which has fixes applied)
                    potential_objects = re.findall(r'\{\s*"name"\s*:.*?"code"\s*:.*?\}', content_fixed, re.DOTALL)
                    recovered_cases = []
                    for obj_str in potential_objects:
                        try:
                            # Try to close the object if needed
                            if obj_str.count('{') > obj_str.count('}'):
                                obj_str += '}' * (obj_str.count('{') - obj_str.count('}'))
                            # Apply all fixes
                            obj_fixed = fix_escaped_quotes(obj_str)
                            obj_fixed = re.sub(r',(\s*[}\]])', r'\1', obj_fixed)
                            test_case = json.loads(obj_fixed)
                            if isinstance(test_case, dict) and 'name' in test_case and 'code' in test_case:
                                if not any(tc.get('code') == test_case.get('code') for tc in recovered_cases):
                                    recovered_cases.append(test_case)
                        except:
                            pass
                    
                    if recovered_cases:
                        logger.info(f"Last resort recovery: extracted {len(recovered_cases)} test cases")
                        return recovered_cases
                except Exception as final_error:
                    logger.debug(f"Final recovery attempt failed: {str(final_error)}")
                
                return []

        except Exception as e:
            logger.error(f"Error generating test cases with GPT-4.1: {str(e)}")
            raise


