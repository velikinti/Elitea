import logging
import time
import os
import json
import re
import shutil
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from pathlib import Path

from fastapi import HTTPException, status
# from endpoints.agents.gpt4o import TestCaseGeneratorGPT4o as TestCaseGeneratorAgent
# from endpoints.agents.gpt4 import TestCaseGeneratorGPT4 as TestCaseGeneratorAgent
# from endpoints.agents.o4mini import o4_mini_TestCase_Gen_Agent as TestCaseGeneratorAgent
from endpoints.agents.claude4 import (
    # TestCaseGeneratorAgentClaude4 as TestCaseGeneratorAgent,
    # TestScriptAgent,
    FrameworkAnalyzer
)

from endpoints.agents.gpt5mini import (
    TestCaseGeneratorAgentGPT5Mini as TestCaseGeneratorAgent,
    TestScriptAgent
)

# from endpoints.agents.o4mini.testcase_generator import o4_mini_TestCase_Gen_Agent as TestCaseGeneratorAgent
from endpoints.automation.schemas import (
    TestScript
)
from settings import settings

logger = logging.getLogger(__name__)


def _ensure_within_root(candidate_path: Path, root_path: Path, field_name: str) -> Path:
    """
    Ensure candidate_path is within root_path boundary.

    Uses resolve() then relative_to() to enforce the boundary. Raises ValueError
    with a clear message if candidate escapes the root.
    """
    candidate_resolved = candidate_path.resolve()
    root_resolved = root_path.resolve()

    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError as e:
        raise ValueError(
            f"{field_name} is not permitted: path must be within '{root_resolved}', got '{candidate_resolved}'"
        ) from e

    return candidate_resolved


def _resolve_under_root(root: Path, candidate: str, field_name: str) -> Path:
    """
    Resolve candidate under root with boundary enforcement.

    If candidate is absolute -> use as-is (but still enforce within root).
    If candidate is relative -> interpret as root / candidate.
    """
    root_path = root.resolve()
    candidate_path = Path(candidate)
    combined = candidate_path if candidate_path.is_absolute() else (root_path / candidate_path)
    return _ensure_within_root(combined, root_path, field_name)


class LLMType(str, Enum):
    """Enumeration of supported LLM types for test case generation."""
    GPT4O = "gpt4o"
    GPT4 = "gpt4"
    GPT5MINI = "gpt5mini"
    LLM = "llm"  # GPT-4o mini
    O4MINI = "o4mini"
    CLAUDE_SONNET_4 = "claude_sonnet_4"

def save_test_cases_to_file(test_cases: List[Dict[str, Any]], api_spec: Optional[Dict[str, Any]] = None) -> str:
    """
    Save test cases to outputfolder/testcases/ directory as JSON file.
    
    Args:
        test_cases: List of test case dictionaries
        api_spec: Optional API specification for metadata
        
    Returns:
        Path to the saved JSON file
    """
    # Create outputfolder/testcases directory
    base_output_dir = os.path.join(os.getcwd(), settings.base_output_folder)
    testcases_dir = os.path.join(base_output_dir, "testcases")
    os.makedirs(testcases_dir, exist_ok=True)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create descriptive filename based on API spec if available
    if api_spec:
        method = api_spec.get("method", "api").upper()
        from urllib.parse import urlparse
        parsed = urlparse(api_spec.get("url", ""))
        endpoint_name = parsed.path.strip("/").replace("/", "_")[:30] if parsed.path else "testcases"
        endpoint_name = endpoint_name.replace(":", "_").replace("?", "_").replace("&", "_").replace("=", "_").strip("_")
        if not endpoint_name or len(endpoint_name) < 3:
            endpoint_name = f"{method.lower()}_testcases"
        filename = f"test_cases_{method}_{endpoint_name}_{timestamp}.json"
    else:
        filename = f"test_cases_{timestamp}.json"
    
    # Prepare data to save
    data_to_save = {
        "test_cases": test_cases,
        "timestamp": timestamp,
        "count": len(test_cases)
    }
    if api_spec:
        data_to_save["api_spec"] = api_spec
    
    # Save to file
    file_path = os.path.join(testcases_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, indent=2)
    
    logger.info(f"Saved {len(test_cases)} test cases to {file_path}")
    return file_path


# def _get_agent_for_llm_type(llm_type: LLMType, api_key: str):
#     """
#     Internal utility to get the appropriate agent instance based on LLM type.
    
#     Args:
#         llm_type: The LLM type to use
#         api_key: API key for the agent
        
#     Returns:
#         Agent instance
#     """
#     if llm_type == LLMType.GPT4O:
#         return TestCaseGeneratorGPT4o(api_key=api_key)
#     elif llm_type == LLMType.GPT4:
#         return TestCaseGeneratorGPT4(api_key=api_key)
#     elif llm_type == LLMType.GPT5MINI:
#         return TestCaseGeneratorAgentGPT5Mini(api_key=api_key)
#     elif llm_type == LLMType.LLM:
#         return TestCaseGeneratorAgentllm(api_key=api_key)
#     elif llm_type == LLMType.O4MINI:
#         return o4_mini_TestCase_Gen_Agent(api_key=api_key)
#     elif llm_type == LLMType.CLAUDE_SONNET_4:
#         return Claude_Sonnet_4_TestCase_Gen_Agent(api_key=api_key)
#     else:
#         raise ValueError(f"Unsupported LLM type: {llm_type}")


def generate_test_cases(
    api_spec: Dict[str, Any],
    llm_type: LLMType = LLMType.LLM,
    review: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Optional[float]]:
    """
    Unified utility function to generate test cases using any supported LLM.
    This is the main entry point for all test case generation - all endpoints should call this.
    
    Args:
        api_spec: API specification dictionary containing method, url, headers, body, query_params
        llm_type: Type of LLM to use (default: LLM which is GPT-4o mini)
        review: Optional review/feedback to consider when generating test cases
        api_key: Optional API key (defaults to settings.openapi_key)
        
    Returns:
        Tuple of (test_cases list, optional response_time_seconds)
        
    Raises:
        Exception: If test case generation fails
    """
    try:
        start_time = time.time()
        api_key = api_key or settings.openapi_key
        
        logger.info(f"Generating test cases with {llm_type.value} for endpoint: {api_spec.get('method')} {api_spec.get('url')}")
        
        # Get the appropriate agent
        # agent = _get_agent_for_llm_type(llm_type, api_key)
        agent = TestCaseGeneratorAgent(api_key=api_key)
        
        # Generate test cases
        result = agent.generate(api_spec, review=review)
        
        # Extract test_cases from result (some agents return dict, some return list)
        if isinstance(result, dict) and "test_cases" in result:
            test_cases = result["test_cases"]
        else:
            test_cases = result
        
        response_time = time.time() - start_time
        
        logger.info(f"Successfully generated {len(test_cases)} test cases using {llm_type.value} in {response_time:.2f}s")
        
        return test_cases, response_time
        
    except Exception as e:
        logger.error(f"Error generating test cases with {llm_type.value}: {str(e)}")
        raise


def generate_test_scripts(
    test_cases: List[Dict[str, Any]],
    framework_markdown_path: str,
    review: Optional[str] = None,
    file_path: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Unified utility function to generate test scripts from test cases.
    This is the main entry point for all test script generation - all endpoints should call this.
    
    Args:
        test_cases: List of test case dictionaries
        framework_markdown_path: Path to framework analysis markdown file (.md)
        review: Optional review/feedback to consider when generating scripts
        file_path: Optional file path to modify (required if review is provided)
        api_key: Optional API key (defaults to settings.openapi_key)
        
    Returns:
        Tuple of (scripts list, output_directory_path)
        
    Raises:
        Exception: If test script generation fails
    """
    try:
        api_key = api_key or settings.openapi_key
        
        # Validate framework markdown path
        if not os.path.isabs(framework_markdown_path):
            framework_markdown_path = os.path.join(os.getcwd(), framework_markdown_path)
        
        if not os.path.exists(framework_markdown_path):
            raise ValueError(f"Framework markdown file not found: {framework_markdown_path}")
        
        if not framework_markdown_path.lower().endswith('.md'):
            raise ValueError(f"Framework markdown file must be a .md file. Provided: {framework_markdown_path}")
        
        logger.info(f"Generating test scripts using framework: {framework_markdown_path}")
        
        # Create agent
        agent = TestScriptAgent(framework_markdown_path=framework_markdown_path, api_key=api_key)
        
        # Generate scripts
        scripts_raw = agent.generate_scripts(test_cases, review=review, file_path=file_path)
        logger.info(f"Generated raw scripts for {len(scripts_raw)} test cases")
        
        # Save scripts to outputfolder/testscript directory
        base_output_dir = os.path.join(os.getcwd(), settings.base_output_folder)
        output_dir = os.path.join(base_output_dir, "testscript")
        os.makedirs(output_dir, exist_ok=True)

        generated_tests_dir = (Path.cwd() / settings.base_output_folder / "testscript").resolve()
        
        # Handle review case - update existing files
        if review and file_path:
            files_to_update = {}
            for script_data in scripts_raw:
                used_file_path = script_data.get('file_path')
                if used_file_path:
                    if used_file_path not in files_to_update:
                        files_to_update[used_file_path] = []
                    files_to_update[used_file_path].append({
                        'test_case_code': script_data['test_case_code'],
                        'script': script_data['script']
                    })
            
            # Update existing files
            for file_path_to_update, script_updates in files_to_update.items():
                try:
                    permitted_path = _resolve_under_root(
                        generated_tests_dir,
                        file_path_to_update,
                        field_name="file_path"
                    )

                    with open(permitted_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()
                    
                    for update in script_updates:
                        test_case_code = update['test_case_code']
                        new_script = update['script']
                        
                        pattern = rf'def test_[^{{]*{re.escape(test_case_code)}[^{{]*\([^)]*\):.*?(?=\n\ndef test_|\n\n@pytest\.|\Z)'
                        new_content = re.sub(pattern, new_script, existing_content, flags=re.DOTALL)
                        
                        if new_content != existing_content:
                            existing_content = new_content
                            logger.info(f"Updated test function for {test_case_code} in {permitted_path.name}")
                    
                    with open(permitted_path, "w", encoding="utf-8") as f:
                        f.write(existing_content)
                    
                    logger.info(f"Updated existing file: {permitted_path.name}")
                except ValueError as ve:
                    detail = str(ve)
                    if "is not permitted" in detail:
                        raise ValueError(f"file path is not permitted: {detail}") from ve
                    raise
                except Exception as e:
                    logger.error(f"Error updating file {file_path_to_update}: {str(e)}")
                    raise
        
        # Generate new test file if needed
        if not review or any(not s.get('file_path') for s in scripts_raw):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if test_cases:
                first_test = test_cases[0]
                from urllib.parse import urlparse


                # Support both dict and Pydantic/model objects
                if isinstance(first_test, dict):
                    req = first_test.get("request", {}) or {}
                    url = req.get("url", "")
                else:
                    req = getattr(first_test, "request", None)
                    if isinstance(req, dict):
                        url = req.get("url", "")
                    else:
                        url = getattr(req, "url", "") if req is not None else ""

                        
                parsed = urlparse(url)
                base_name = parsed.path.strip("/").replace("/", "_")[:50] if parsed.path else "api_tests"
                base_name = base_name.replace(":", "_").replace("?", "_").replace("&", "_").replace("=", "_").strip("_")
                if not base_name or len(base_name) < 3:
                    base_name = f"test_cases_{len(test_cases)}"
            else:
                base_name = "test_cases"
            
            test_filename = f"test_{base_name}_{timestamp}.py"
            
            test_file_content = f'''#!/usr/bin/env python3
"""
Generated test cases.
Auto-generated by TestScriptAgent
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total test cases: {len(test_cases)}

Note: This test file is generated for review.
To use in framework, upload via POST /upload-test-to-framework endpoint.
The uploaded version will be placed in framework/tests/ and can be run directly.
"""

'''
            
            import_lines = set()
            test_scripts_clean = []
            
            scripts_to_process = [s for s in scripts_raw if not s.get('file_path')]
            if not scripts_to_process:
                scripts_to_process = scripts_raw
            
            for script_data in scripts_to_process:
                script = script_data.get('script', '')
                script_lines = script.split('\n')
                clean_script_lines = []
                in_import_section = True
                
                for line in script_lines:
                    stripped = line.strip()
                    if stripped.startswith(('import ', 'from ')):
                        import_lines.add(stripped)
                        in_import_section = True
                    elif in_import_section and stripped == '':
                        continue
                    else:
                        in_import_section = False
                        clean_script_lines.append(line)
                
                clean_script = '\n'.join(clean_script_lines).strip()
                if clean_script:
                    test_scripts_clean.append(clean_script)
            
            if import_lines:
                test_file_content += "\n".join(sorted(import_lines)) + "\n\n"
            
            for clean_script in test_scripts_clean:
                test_file_content += "\n" + clean_script + "\n"
            
            test_file_path = os.path.join(output_dir, test_filename)
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_file_content)
            
            os.chmod(test_file_path, 0o755)
            logger.info(f"Generated executable test file with {len(scripts_to_process)} test cases: {test_file_path}")
        
        # Create package __init__.py if it doesn't exist
        init_path = os.path.join(output_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write('''"""Test scripts generated by TestScriptAgent."""
import os
import sys
import pytest

def run_tests(pattern="test_*.py", args=None):
    """Run all tests in this package matching the pattern."""
    if args is None:
        args = []
    test_dir = os.path.dirname(os.path.abspath(__file__))
    return pytest.main([test_dir, "-k", pattern] + args)

if __name__ == "__main__":
    sys.exit(run_tests())
''')
            os.chmod(init_path, 0o755)
        
        logger.info(f"Successfully generated {len(scripts_raw)} test scripts")
        return scripts_raw, output_dir
        
    except Exception as e:
        logger.error(f"Error generating test scripts: {str(e)}")
        raise


def analyze_framework(
    framework_path: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[Any, str]:
    """
    Unified utility function to analyze test framework.
    This is the main entry point for framework analysis - all endpoints should call this.
    
    Args:
        framework_path: Optional framework path (defaults to settings.test_framework_path)
        api_key: Optional API key (defaults to settings.openapi_key)
        
    Returns:
        Tuple of (FrameworkAnalysis object, results_file_path)
        
    Raises:
        Exception: If framework analysis fails
    """
    try:
        framework_path = framework_path or settings.test_framework_path
        api_key = api_key or settings.openapi_key
        
        if not framework_path:
            raise ValueError("Framework path not configured. Please set QA_TEST_FRAMEWORK_PATH in your .env file")
        
        if not os.path.exists(framework_path):
            raise ValueError(f"Framework path does not exist: {framework_path}")
        
        logger.info(f"Starting framework analysis for path: {framework_path}")
        
        # Analyze framework
        analyzer = FrameworkAnalyzer(framework_path=framework_path, api_key=api_key)
        framework_analysis = analyzer.analyze()
        
        if not framework_analysis:
            raise ValueError("Framework analysis returned empty results")
        
        # Save to outputfolder/framework directory
        base_output_dir = os.path.join(os.getcwd(), settings.base_output_folder)
        framework_results_dir = os.path.join(base_output_dir, "framework")
        os.makedirs(framework_results_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        framework_results_path = os.path.join(framework_results_dir, f"framework_analysis_{timestamp}.md")
        
        # Save as Markdown file
        markdown_content = framework_analysis.to_markdown()
        with open(framework_results_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logger.info(f"Framework analysis saved to {framework_results_path}")
        
        return framework_analysis, framework_results_path
        
    except Exception as e:
        logger.error(f"Error analyzing framework: {str(e)}")
        raise


def integrate_script_to_framework(
    test_file_name: str,
    framework_test_dir: str
) -> Dict[str, Any]:
    """
    Integrate test script to framework and run it without using LLM.
    This function copies the test file and executes it using pytest.
    
    Args:
        test_file_name: Name of test file (can be just filename or full path)
        framework_test_dir: Framework test directory path (can be relative or absolute path)
        
    Returns:
        Dictionary with integration and test execution results
        
    Raises:
        Exception: If integration or test execution fails
    """
    import subprocess
    
    try:
        generated_tests_dir = (Path.cwd() / settings.base_output_folder / "testscript").resolve()
        os.makedirs(generated_tests_dir, exist_ok=True)

        # Resolve and enforce source file is within generated_tests_dir (even if absolute provided)
        source_file = _resolve_under_root(
            generated_tests_dir,
            test_file_name,
            field_name="test_file_name"
        )

        if not source_file.exists():
            raise ValueError(f"Test file not found: {source_file}")

        test_file_basename = source_file.name

        # Require configured framework root and do not infer from provided framework_test_dir
        if not settings.test_framework_path:
            raise ValueError("Framework path not configured. Please set QA_TEST_FRAMEWORK_PATH in your .env file")
        framework_root = Path(settings.test_framework_path).resolve()
        if not framework_root.exists():
            raise ValueError(f"Framework path does not exist: {framework_root}")

        # Resolve target test directory within framework_root (absolute allowed but must be within root)
        target_test_dir = _resolve_under_root(
            framework_root,
            framework_test_dir,
            field_name="framework_test_dir"
        )

        target_test_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Framework test directory: {target_test_dir}")

        # Copy test file to framework (use basename to avoid path issues)
        dest_file = target_test_dir / test_file_basename
        shutil.copy2(source_file, dest_file)
        logger.info(f"Test file copied to framework: {dest_file}")
        
        # Run the test using pytest
        logger.info(f"Running test: {dest_file}")
        logger.info(f"Framework root for pytest: {framework_root}")
        
        # Detect and use framework's Python/pytest executable
        python_executable = None
        pytest_cmd = None
        
        # Check for virtual environment in framework root
        venv_paths = [
            framework_root / "venv",
            framework_root / ".venv",
            framework_root / "env",
        ]
        
        for venv_path in venv_paths:
            if venv_path.exists():
                # Windows: venv/Scripts/python.exe, Linux: venv/bin/python
                python_win = venv_path / "Scripts" / "python.exe"
                python_unix = venv_path / "bin" / "python"
                if python_win.exists():
                    python_executable = str(python_win)
                    logger.info(f"Found Python in venv: {python_executable}")
                    break
                elif python_unix.exists():
                    python_executable = str(python_unix)
                    logger.info(f"Found Python in venv: {python_executable}")
                    break
        
        # If no venv found, check for poetry environment
        if not python_executable:
            pyproject_toml = framework_root / "pyproject.toml"
            if pyproject_toml.exists():
                # Use poetry run pytest
                pytest_cmd = ["poetry", "run", "pytest", str(dest_file), "-v", "--tb=short"]
                logger.info("Using poetry to run pytest")
            else:
                # Fallback: use system python -m pytest
                python_executable = "python"
                logger.info("Using system python (ensure framework's Python is in PATH)")
        
        # Build pytest command if not already built (for poetry case)
        if not pytest_cmd:
            if python_executable:
                # Use framework's Python to run pytest as module
                pytest_cmd = [python_executable, "-m", "pytest", str(dest_file), "-v", "--tb=short"]
            else:
                # Last resort: use system pytest
                pytest_cmd = ["pytest", str(dest_file), "-v", "--tb=short"]
                logger.warning("Using system pytest - may use wrong environment!")
        
        logger.info(f"Executing: {' '.join(pytest_cmd)}")
        logger.info(f"Working directory: {framework_root}")
        
        try:
            # Change to framework root directory to run pytest
            result = subprocess.run(
                pytest_cmd,
                cwd=str(framework_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            test_passed = result.returncode == 0
            test_output = (result.stdout or "") + (result.stderr or "")
            
            if test_passed:
                logger.info(f"Test execution passed: {test_file_basename}")
                return {
                    "success": True,
                    "message": f"Test file integrated successfully and test execution passed",
                    "source_file": str(source_file),
                    "destination_file": str(dest_file),
                    "test_execution_success": True,
                    "test_execution_output": test_output
                }
            else:
                logger.warning(f"Test execution failed: {test_file_basename}")
                return {
                    "success": True,  # Integration succeeded, but test failed
                    "message": f"Test file integrated successfully but test execution failed",
                    "source_file": str(source_file),
                    "destination_file": str(dest_file),
                    "test_execution_success": False,
                    "test_execution_output": test_output
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"Test execution timed out after 5 minutes"
            logger.error(error_msg)
            return {
                "success": True,  # Integration succeeded, but test timed out
                "message": f"Test file integrated successfully but test execution timed out",
                "source_file": str(source_file),
                "destination_file": str(dest_file),
                "test_execution_success": False,
                "test_execution_output": error_msg
            }
        except Exception as test_error:
            error_msg = f"Error running test: {str(test_error)}"
            logger.error(error_msg)
            return {
                "success": True,  # Integration succeeded, but test execution had error
                "message": f"Test file integrated successfully but test execution encountered an error",
                "source_file": str(source_file),
                "destination_file": str(dest_file),
                "test_execution_success": False,
                "test_execution_output": error_msg
            }
        
    except ValueError as e:
        logger.error(f"Error integrating test to framework: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error integrating test to framework: {str(e)}")
        raise