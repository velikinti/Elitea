import openai
from openai import AzureOpenAI
import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CritiqueAgentGPT4oMini:
    """
    GPT-4o based test case critique agent for API testing.
    Evaluates test case quality using comprehensive analysis.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the GPT-4o critique agent.
        
        Args:
            api_key: Azure OpenAI API key
        """
        openai.api_key = api_key
        self.api_key = api_key

    # def judge_test_cases(
    #         self, 
    #         test_cases_file_path: str,
    #         temperature: float = 0.1
    # ) -> Dict[str, Any]:
        
    def review_test_cases_from_file(
            self, 
            test_cases_file_path: str,
            temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Judge test cases from a JSON file and return structured evaluation with score.
        
        Args:
            test_cases_file_path: Path to JSON file containing test case dictionaries
            
        Returns:
            Dictionary containing:
                - test_cases: Original test cases (unmodified)
                - score: Overall quality score (1-5 scale converted to 0-100)
                - evaluation: Detailed evaluation results from LLM
        """
        try:
            # Read test cases from file
            if not os.path.exists(test_cases_file_path):
                raise FileNotFoundError(f"Test cases file not found: {test_cases_file_path}")
            
            with open(test_cases_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both direct array and object with test_cases property
            if isinstance(data, list):
                test_cases = data
            elif isinstance(data, dict) and 'test_cases' in data:
                test_cases = data['test_cases']
            else:
                raise ValueError("Test cases file must contain either a JSON array or an object with 'test_cases' property")
            
            # Ensure test_cases is a list
            if not isinstance(test_cases, list):
                raise ValueError("Test cases must be a JSON array")
            
            logger.info(f"Loaded {len(test_cases)} test cases from {test_cases_file_path}")
            
        except Exception as e:
            logger.error(f"Error reading test cases file: {str(e)}")
            raise Exception(f"Failed to load test cases from file: {str(e)}")

        # Convert test cases to JSON string for prompt
        test_cases_json = json.dumps(test_cases, indent=2)
        
        prompt = f"""You are a senior QA architect tasked with evaluating the quality of API test cases.

You will be given a list of API test case details. Your job is to assess the test cases against common, industry-standard criteria used to judge the effectiveness of API test suites.

Test Cases:
{test_cases_json}

Evaluate the test cases based on the following criteria:

1. Clarity & Readability
   - Are names clear and descriptive?
   - Do descriptions accurately explain what is being tested?

2. Coverage Quality
   - Do test cases meaningfully cover edge, boundary, or negative scenarios?
   - Are scenarios distinct and non-duplicative?

3. Request Accuracy
   - Are method, URL, headers, body, and query parameters clearly and correctly defined?
   - Are request variations appropriate for stated scenarios?

4. Preconditions Validity
   - Are preconditions necessary, minimal, and clearly stated?
   - Are there missing or unnecessary preconditions?

5. Step Quality
   - Are steps detailed, sequential, and executable?
   - Do steps explicitly describe request setup, execution, and validation?
   - Do steps end with response verification?

6. Assertion Strength
   - Are expected status codes appropriate for scenarios?
   - Is validation sufficient or too weak?

7. Maintainability
   - Would these tests be easy to understand, reuse, and maintain over time?
   - Are naming and structure consistent with good test suite practices?

Output Requirements:
Return a JSON object with this exact structure:
{{
    "overall_quality_score": <integer 1-5>,
    "verdict": "<Strong|Adequate|Weak>",
    "criteria_assessment": {{
        "clarity_readability": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "coverage_quality": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "request_accuracy": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "preconditions_validity": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "step_quality": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "assertion_strength": {{"score": <1-5>, "justification": "<brief explanation>"}},
        "maintainability": {{"score": <1-5>, "justification": "<brief explanation>"}}
    }},
    "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>", "..."],
    "summary": "<brief overall summary>"
}}

Constraints:
- Do NOT assume any system behavior beyond what is visible in the test cases
- Do NOT invent missing steps, validations, or requirements
- Do NOT include markdown, explanations, or text outside JSON
- Return ONLY the evaluation JSON object
"""
        
        try:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2025-03-01-preview",
                azure_endpoint="https://ai-proxy.lab.epam.com"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant for API test case quality evaluation."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_completion_tokens=4096,
                response_format={"type": "json_object"},
                temperature=temperature
            )

            # Parse the response content as JSON
            content = response.choices[0].message.content.strip()
            
            logger.info(f"GPT-4o critique response received, length: {len(content)} characters")

            # Try to parse JSON response
            try:
                evaluation = json.loads(content)
                
                # Extract overall quality score (1-5 scale) and convert to 0-100 scale
                quality_score_1_to_5 = evaluation.get("overall_quality_score", 3)
                # Convert 1-5 scale to 0-100 scale: (score - 1) * 25
                score_0_to_100 = int((quality_score_1_to_5 - 1) * 25)
                
                logger.info(f"Test cases evaluated. Quality score: {quality_score_1_to_5}/5 ({score_0_to_100}/100)")
                
                return {
                    "test_cases": test_cases,  # Return original test cases unmodified
                    "score": score_0_to_100,    # Score on 0-100 scale
                    "evaluation": evaluation    # Full evaluation details
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT-4o critique response as JSON: {str(e)}")
                logger.debug(f"Response content: {content}")
                
                # Return default response on JSON parsing error
                return {
                    "test_cases": test_cases,
                    "score": 50,  # Default middle score
                    "evaluation": {
                        "overall_quality_score": 3,
                        "verdict": "Error",
                        "summary": f"Evaluation failed - JSON parsing error: {str(e)}"
                    }
                }

        except Exception as e:
            logger.error(f"Error calling GPT-4o for test case critique: {str(e)}")
            # Return default response on API error
            return {
                "test_cases": test_cases,
                "score": 0,
                "evaluation": {
                    "overall_quality_score": 0,
                    "verdict": "Error",
                    "summary": f"Evaluation failed: {str(e)}"
                }
            }