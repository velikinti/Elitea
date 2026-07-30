import os
from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging
import json
import re
import ast
import time
from functools import lru_cache


from endpoints.prompts.gpt5mini.prompts import (
    get_testscript_prompt, 
    get_testscript_system_message as get_system_message, 
    get_testscript_review_section as get_review_section
)
from endpoints.agents.gpt5mini.testscript_judge_agent_gpt5mini import TestScriptJudgeAgentGPT5Mini as TestScriptJudgeAgent

logger = logging.getLogger(__name__)

class TestScriptAgent:

    def __init__(self, framework_markdown_path: str, api_key: str = None):
        """Initialize the TestScriptAgent with framework markdown file path.
        
        Args:
            framework_markdown_path: Path to framework analysis markdown file (.md) - required
            api_key: OpenAI API key for LLM calls (if not provided, uses QA_OPENAPI_KEY env var)
        """
        if not framework_markdown_path:
            raise ValueError("framework_markdown_path is required. Cannot generate scripts without framework information.")
        
        self.framework_markdown = None
        
        # Get API key from parameter, environment variable, or raise error
        self.api_key = api_key
        if not self.api_key:
            raise ValueError(
                "API key must be provided via parameter or QA_OPENAPI_KEY environment variable. "
                "Cannot initialize LLM client without API key."
            )
        
        # Initialize LLM client
        self.llm_client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint="https://ai-proxy.lab.epam.com"
        )
        
        # Rate limiting
        self._last_call_time = 0
        self._min_interval = 0.5  # Minimum seconds between LLM calls
        
        # Load framework markdown file
        logger.info(f"Loading framework analysis from markdown file: {framework_markdown_path}")
        self._load_framework_markdown(framework_markdown_path)
        logger.info("Framework markdown loaded - will use markdown for code generation")
    
    def _load_framework_markdown(self, markdown_path: str):
        """Load framework analysis from markdown file."""
        if not os.path.exists(markdown_path):
            raise ValueError(f"Framework markdown file not found: {markdown_path}")
        
        if not markdown_path.lower().endswith('.md'):
            raise ValueError(f"Framework markdown file must be a .md file. Provided: {markdown_path}")
        
        try:
            with open(markdown_path, "r", encoding="utf-8") as f:
                self.framework_markdown = f.read()
            
            if not self.framework_markdown or len(self.framework_markdown) < 100:
                raise ValueError(f"Framework markdown file appears to be empty or invalid: {markdown_path}")
            
            logger.info(f"Successfully loaded framework markdown ({len(self.framework_markdown)} characters)")
        except Exception as e:
            logger.error(f"Error loading framework markdown: {str(e)}")
            raise ValueError(f"Failed to load framework markdown from {markdown_path}: {str(e)}")
        
    
    def _extract_framework_components(self) -> Dict[str, str]:
        """Extract framework components (client, response, assertion, config) from markdown.
        
        Returns:
            Dictionary with component names and imports
        """
        defaults = {
            "client_class": "RestRequest",
            "client_import": "from framework.api.requests.base_api import RestRequest",
            "response_class": "APIResponse",
            "response_import": "from framework.api.response.response_validator import APIResponse",
            "assertion_utils": "RestResponse",
            "assertion_import": "from framework.api.response.response_validator import RestResponse",
            "config_class": "APIConfiguration",
            "config_import": "from framework.api.requests.base_api import APIConfiguration"
        }
        
        components = defaults.copy()
        
        # Extract from markdown using regex
        patterns = {
            "client": (r'## Client Class.*?- \*\*Name\*\*: (\w+).*?- \*\*Import\*\*: `([^`]+)`', "client_class", "client_import"),
            "response": (r'## Response Class.*?- \*\*Name\*\*: (\w+).*?- \*\*Import\*\*: `([^`]+)`', "response_class", "response_import"),
            "assertion": (r'## Assertion Utilities.*?- \*\*Name\*\*: (\w+).*?- \*\*Import\*\*: `([^`]+)`', "assertion_utils", "assertion_import"),
            "config": (r'#### APIConfiguration.*?- \*\*Import\*\*: `([^`]+)`', None, "config_import")
        }
        
        for key, (pattern, name_key, import_key) in patterns.items():
            match = re.search(pattern, self.framework_markdown, re.DOTALL)
            if match:
                if name_key:
                    components[name_key] = match.group(1)
                components[import_key] = match.group(2) if len(match.groups()) > 1 else match.group(1)
        
        logger.info(f"Extracted components from markdown: {components['client_class']}, {components['response_class']}, {components['assertion_utils']}")
        return components
    
    @lru_cache(maxsize=1)
    def _build_framework_sections(self) -> str:
        """Build framework sections for LLM prompt from markdown (filtered for API components only).
        
        Returns:
            Filtered markdown content with UI components removed
        """
        framework_sections = []
        
        # Extract relevant sections from markdown
        sections_patterns = [
            (r'## Client Class.*?(?=## Response Class|## Assertion Utilities|## Utility Functions|## Test Patterns|\Z)', 1500),
            (r'## Response Class.*?(?=## Assertion Utilities|## Utility Functions|## Test Patterns|\Z)', 1500),
            (r'## Test Patterns.*?(?=## Test Organization|## Framework Conventions|\Z)', 2000),
            (r'### API Components.*?(?=### UI Components|### Core Components|## Client Class|\Z)', 2000),
            (r'### API Utilities.*?(?=### UI Utilities|### Core Utilities|## Test Patterns|\Z)', 1500)
        ]
        
        for pattern, max_length in sections_patterns:
            match = re.search(pattern, self.framework_markdown, re.DOTALL)
            if match:
                section_text = match.group(0)
                # Filter UI patterns for Test Patterns section
                if "Test Patterns" in pattern:
                    section_text = re.sub(r'###.*UI.*?\n.*?(?=###|\Z)', '', section_text, flags=re.DOTALL | re.IGNORECASE)
                    section_text = re.sub(r'.*Browser\.get_driver.*?\n', '', section_text, flags=re.IGNORECASE)
                    section_text = re.sub(r'.*driver.*?\n', '', section_text, flags=re.IGNORECASE)
                framework_sections.append(section_text[:max_length])
        
        result = "\n\n".join(framework_sections) if framework_sections else self.framework_markdown[:8000]
        logger.debug(f"Built framework sections ({len(result)} characters)")
        return result
    
    def _build_review_section(self, review: Optional[str], original_script: Optional[str]) -> str:
        """Build review section for prompt (SRP: Single responsibility for review section)."""
        return get_review_section(review, original_script)
    
    def _build_llm_prompt(self, test_case_json: str, framework_section: str, components: Dict[str, str], 
                          review_section: str, test_case) -> str:
        """Build LLM prompt (SRP: Single responsibility for prompt building).
        
        The LLM will extract method signatures and properties directly from the framework_section markdown.
        """
        return get_testscript_prompt(test_case_json, framework_section, components, review_section, test_case)

    def _validate_script_syntax(self, script: str) -> tuple:
        """Validate Python syntax of generated script.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(script)
            return True, None
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            logger.error(f"Script syntax validation failed: {error_msg}")
            return False, error_msg
    
    def _validate_script_imports(self, script: str, components: Dict[str, str]) -> tuple:
        """Validate that required imports are present in script.
        
        Returns:
            Tuple of (is_valid, missing_imports)
        """
        missing = []
        required_imports = [
            components.get("client_import", "").split("import")[-1].strip(),
            components.get("response_import", "").split("import")[-1].strip(),
        ]
        
        for imp in required_imports:
            if imp and imp not in script:
                missing.append(imp)
        
        return len(missing) == 0, missing
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM API with retry logic and rate limiting.
        
        Args:
            prompt: The prompt to send to LLM
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated script content
        """
        system_message = get_system_message()
        
        for attempt in range(1, max_retries + 1):
            try:
                # Rate limiting
                current_time = time.time()
                time_since_last_call = current_time - self._last_call_time
                if time_since_last_call < self._min_interval:
                    sleep_time = self._min_interval - time_since_last_call
                    logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                
                # Log prompt (truncated for large prompts)
                if logger.isEnabledFor(logging.DEBUG):
                    prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
                    logger.debug(f"LLM Prompt (attempt {attempt}/{max_retries}, first 500 chars): {prompt_preview}")
                
                self._last_call_time = time.time()
                


                completion = self.llm_client.chat.completions.create(
                    model="gpt-5-mini-2025-08-07",
                    messages=[
                        {
                            "role": "system", 
                            "content": system_message
                         },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=8000
                    # max_tokens=18432,
                    # temperature=0.3
                )
                script = completion.choices[0].message.content.strip()
                
                # Log response metadata
                if hasattr(completion, 'usage') and completion.usage:
                    logger.info(
                        f"LLM Response: tokens_used={completion.usage.total_tokens}, "
                        f"prompt_tokens={completion.usage.prompt_tokens}, "
                        f"completion_tokens={completion.usage.completion_tokens}, "
                        f"model={completion.model}"
                    )
                
                return script
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"LLM call attempt {attempt}/{max_retries} failed: {error_msg}")
                
                if attempt < max_retries:
                    # Exponential backoff: wait 2^attempt seconds
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} LLM call attempts failed")
                    raise ValueError(f"Failed to generate test script after {max_retries} attempts: {error_msg}")
        
        # Should never reach here, but just in case
        raise ValueError("Failed to generate test script: unexpected error in retry logic")
    
    def _generate_script_with_llm(self, test_case, review: Optional[str] = None, original_script: Optional[str] = None) -> str:
        """Generate test script using LLM from markdown framework analysis.
        
        Args:
            test_case: Test case object
            review: Optional review/feedback to incorporate
            original_script: Optional original script to modify (when review is provided)
        """
        test_case_json = json.dumps({
            "name": test_case.name,
            "code": test_case.code,
            "description": test_case.description,
            "request": test_case.request,
            "expected_status": test_case.expected_status,
            "steps": test_case.steps
        }, indent=2)
        
        components = self._extract_framework_components()
        framework_section = self._build_framework_sections()
        review_section = self._build_review_section(review, original_script)
        prompt = self._build_llm_prompt(test_case_json, framework_section, components, review_section, test_case)
        
        try:
            # Call LLM with retry logic
            script = self._call_llm_with_retry(prompt, max_retries=3)
            
            if not script or len(script) < 50:
                raise ValueError(
                    f"LLM returned empty or too short response (length: {len(script) if script else 0}). "
                    f"Test case: {test_case.code}"
                )
            
            # Clean script output - remove markdown code blocks
            if script.startswith("```python"):
                script = script[9:]
            elif script.startswith("```"):
                script = script[3:]
            if script.endswith("```"):
                script = script[:-3]
            script = script.strip()
            
            # Enhanced validation
            script_lower = script.lower()
            is_incomplete = "TODO" in script or ("pass" in script_lower and len(script) < 300)
            missing_framework = components["client_class"] not in script
            
            # Try to extract code from nested markdown blocks if validation fails
            if is_incomplete or missing_framework:
                if "```" in script:
                    code_match = re.search(r'```(?:python)?\s*\n(.*?)\n```', script, re.DOTALL)
                    if code_match:
                        cleaned_script = code_match.group(1).strip()
                        if "TODO" not in cleaned_script and components["client_class"] in cleaned_script:
                            script = cleaned_script
                            is_incomplete = False
                            missing_framework = False
            
            # Validate syntax
            is_valid_syntax, syntax_error = self._validate_script_syntax(script)
            if not is_valid_syntax:
                raise ValueError(
                    f"Generated script has syntax errors: {syntax_error}. "
                    f"Test case: {test_case.code}, Script length: {len(script)}"
                )
            
            # Validate imports
            has_imports, missing_imports = self._validate_script_imports(script, components)
            if not has_imports:
                logger.warning(
                    f"Script missing some imports: {missing_imports}. "
                    f"Test case: {test_case.code}"
                )
            
            # Final completeness check
            if is_incomplete or missing_framework:
                raise ValueError(
                    f"Generated script is incomplete: TODO={is_incomplete}, "
                    f"missing_framework={missing_framework}, "
                    f"script_length={len(script)}, "
                    f"test_case_code={test_case.code}, "
                    f"test_case_name={test_case.name}"
                )
            
            logger.info(f"Successfully generated script for test case {test_case.code} ({len(script)} characters)")
            # Implement llm as judge for generated script here
            judge_agent = TestScriptJudgeAgent(api_key=self.api_key)
            review_result = judge_agent.review_test_scripts(test_case = test_case, test_script=script, temperature=0.1)
            
            average_score = review_result.get('overall_summary', {}).get('overall_score', 0)
            logger.info(f"average_score : {average_score}")
            if average_score < 80:
                logger.warning(f"Generated script for test case {test_case.code} received low score from judge agent: {average_score}")
                raise ValueError(
                    f"Generated script did not meet quality threshold. "
                    f"Average score from judge agent: {average_score}. "
                    f"Test case: {test_case.code}, Script length: {len(script)}"
                )
            return script
            
        except ValueError:
            # Re-raise ValueError as-is (these are our validation errors)
            raise
        except Exception as e:
            logger.error(f"LLM script generation failed for test case {test_case.code}: {str(e)}", exc_info=True)
            raise ValueError(
                f"Failed to generate test script using LLM: {str(e)}. "
                f"Test case: {test_case.code}. "
                f"Ensure framework markdown file is correct and LLM service is available."
            )
    
    
    def _extract_test_function_from_file(self, file_path: str, test_case_code: str) -> Optional[str]:
        """
        Extract a specific test function from an existing test file.
        
        Args:
            file_path: Path to the existing test file
            test_case_code: Test case code to find (e.g., "TC001")
        
        Returns:
            The test function code as string, or None if not found
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Pattern to find test function: def test_*TC001*...
            # Match from def test_ to next def test_ or end of file
            pattern = rf'def test_[^{{]*{re.escape(test_case_code)}[^{{]*\([^)]*\):.*?(?=\n\ndef test_|\n\n@pytest\.|\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                return match.group(0).strip()
            
            # Fallback: search line by line
            lines = content.split('\n')
            in_target_function = False
            function_lines = []
            indent_level = None
            
            for line in lines:
                # Check if this is the start of our target function
                if f'def test_' in line and test_case_code in line:
                    in_target_function = True
                    function_lines = [line]
                    indent_level = len(line) - len(line.lstrip())
                    continue
                
                if in_target_function:
                    # Check if we've reached the next function
                    if line.strip().startswith('def test_') and len(line) - len(line.lstrip()) <= indent_level:
                        break
                    function_lines.append(line)
            
            if function_lines:
                return '\n'.join(function_lines).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting test function from file: {str(e)}")
            return None

    def generate_scripts(self, test_cases: List, review: Optional[str] = None, file_path: Optional[str] = None) -> List[Dict]:
        """Generate test scripts for the given test cases using framework markdown analysis.
        
        Args:
            test_cases: List of test case objects
            review: Optional review/feedback to incorporate (requires file_path)
            file_path: Required if review is provided: Specific file path to modify
        
        Returns:
            List of dictionaries with test_case_code, script, file_path, has_review
        """
        if not self.framework_markdown:
            raise ValueError("Framework markdown is required for script generation. Ensure framework_markdown_path is provided during initialization.")
        
        scripts = []
        for tc in test_cases:
            original_script = None
            used_file_path = None
            
            # If review is provided, extract original script from file_path
            if review:
                if not file_path:
                    raise ValueError("file_path is required when review is provided")
                
                # Use user-provided file path
                if not os.path.isabs(file_path):
                    file_path = os.path.join(os.getcwd(), file_path)
                
                if not os.path.exists(file_path):
                    raise ValueError(f"File not found: {file_path}")
                
                original_script = self._extract_test_function_from_file(file_path, tc.code)
                used_file_path = file_path
                
                if original_script:
                    logger.info(f"Extracted original script for {tc.code} from {file_path}")
                else:
                    logger.warning(f"Could not extract test function for {tc.code} from {file_path}")
            
            # Generate script using LLM
            script_code = self._generate_script_with_llm(tc, review=review, original_script=original_script)
            scripts.append({
                "test_case_code": tc.code,
                "script": script_code,
                "file_path": used_file_path,
                "has_review": review is not None
            })
        return scripts
