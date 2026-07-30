import os
from typing import Dict, List, Optional
from openai import AzureOpenAI
import logging
import json

from endpoints.prompts.gpt5mini.prompts import get_testscript_judge_system_message, get_testscript_judge_prompt

logger = logging.getLogger(__name__)


class TestScriptJudgeAgentGPT5Mini:
    """
    LLM-based judge agent that reviews and evaluates test scripts using GPT-5-mini.
    Evaluates test scripts based on accuracy, consistency, factualness, completeness, and other quality metrics.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the TestScriptJudgeAgentGPT5Mini.
        
        Args:
            api_key: Azure OpenAI API key for LLM calls
        """
        self.api_key = api_key
        
        # Initialize LLM client for GPT-5-mini
        self.llm_client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint="https://ai-proxy.lab.epam.com"
        )
    
    def review_test_scripts(
        self, 
        test_case: Dict, 
        test_script: str,
        temperature: float = 0.3
    ) -> Dict:
        """
        Review and evaluate test scripts using LLM as a judge.
        
        Args:
            test_case: Test case dictionary to review
            test_script: Test script content as a string
            
        Returns:
            Dictionary containing review results with scores and feedback for each test script
        """
        try:
            # Create review prompt using new prompt functions
            prompt = get_testscript_judge_prompt(test_case, test_script)

            # Call GPT-5-mini for review
            # Note: GPT-5-mini only supports default temperature (1), so we don't set it
            completion = self.llm_client.chat.completions.create(
                model="gpt-5-mini-2025-08-07",
                messages=[
                    {
                        "role": "system",
                        "content": get_testscript_judge_system_message()
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=8000
            )
            
            # Parse LLM response
            review_text = completion.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if review_text.startswith("```json"):
                review_text = review_text[7:]
            elif review_text.startswith("```"):
                review_text = review_text[3:]
            if review_text.endswith("```"):
                review_text = review_text[:-3]
            review_text = review_text.strip()
            
            try:
                review_result = json.loads(review_text)
                return review_result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                logger.error(f"Response text: {review_text[:500]}")
                # Return error structure
                return {
                    "error": "Failed to parse LLM response as JSON",
                    "raw_response": review_text[:1000],
                    "test_cases": test_case.code if 'code' in test_case else 'N/A'
                }
                
        except Exception as e:
            logger.error(f"Error reviewing test cases: {str(e)}")
            raise
    
    def review_single_test_case(
        self, 
        test_case: Dict, 
        api_spec: Optional[Dict] = None
    ) -> Dict:
        """
        Review a single test case.
        
        Args:
            test_case: Test case dictionary to review
            api_spec: Optional API specification for context
            
        Returns:
            Review result for the single test case
        """
        return self.review_test_cases([test_case], api_spec, temperature=0.1)
    
    def review_test_cases_from_file(
        self, 
        file_path: str,
        temperature: float = 0.1
    ) -> Dict:
        """
        Review test cases from a test_results JSON file.
        
        Args:
            file_path: Path to the test_results JSON file
            
        Returns:
            Dictionary containing review results with scores and feedback for each test case
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
            Exception: If file reading or parsing fails
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Test results file not found: {file_path}")
            
            # If relative path, make it absolute relative to current working directory
            if not os.path.isabs(file_path):
                file_path = os.path.join(os.getcwd(), file_path)
            
            # Read and parse JSON file
            logger.info(f"Reading test results from file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            
            # Extract test cases and API spec from the file structure
            if not isinstance(file_data, dict):
                raise ValueError(f"Invalid file format: Expected JSON object, got {type(file_data)}")
            
            # Extract test cases
            if "test_cases" not in file_data:
                raise ValueError("Invalid file format: 'test_cases' key not found in JSON file")
            
            test_cases = file_data["test_cases"]
            if not isinstance(test_cases, list):
                raise ValueError(f"Invalid file format: 'test_cases' should be a list, got {type(test_cases)}")
            
            # Extract API spec from metadata if available
            api_spec = None
            if "metadata" in file_data and isinstance(file_data["metadata"], dict):
                api_spec = file_data["metadata"].get("api_spec")
            
            logger.info(f"Found {len(test_cases)} test cases in file. API spec available: {api_spec is not None}")
            
            # Review the test cases using existing method
            review_result = self.review_test_cases(test_cases, api_spec, temperature=temperature)
            
            # Add file metadata to review result
            if isinstance(review_result, dict):
                review_result["source_file"] = file_path
                if "metadata" in file_data:
                    review_result["file_metadata"] = file_data["metadata"]
            
            return review_result
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file: {str(e)}")
            raise ValueError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading or reviewing test cases from file: {str(e)}")
            raise

