import openai
from openai import AzureOpenAI
import json
from endpoints.automation.schemas import TestCaseResponse
from endpoints.prompts.claude4 import get_testcase_prompt, get_system_message

from endpoints.agents.claude4.testcase_judge_agent import TestCaseJudgeAgentClaude4 as TestCaseJudgeAgent

import re
import logging

logger = logging.getLogger(__name__)
 
class TestCaseGeneratorAgentClaude4:

    def __init__(self, api_key: str):

        openai.api_key = api_key
        self.api_key = api_key
 
    def generate(self, api_spec: dict, review: str = None) -> list:

        # Use prompt from prompts folder
        prompt = get_testcase_prompt(api_spec, review)
        client = AzureOpenAI(
            api_key = self.api_key,       # Use the API key provided during initialization
            api_version = "2025-03-01-preview",
            azure_endpoint = "https://ai-proxy.lab.epam.com"
        )                                                   #### Cgheck and renmove it
        
        response = client.chat.completions.create(

            model="claude-sonnet-4-5@20250929",
            #model="gpt-4o",

            messages=[

                {"role": "system", "content": get_system_message()},

                {"role": "user", "content": prompt}

            ],

            max_completion_tokens= 3072,
            response_format={"type": "json_object"},
            temperature=0.3,
            stream=True,
            stream_options={
                "include_usage":True
            }
        )

        # Parse the response content as JSON
        # Accumulate content from stream and capture usage
        content = ""
        usage_data = None
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    content += delta_content
            # Capture usage information from the final chunk
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_data = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens
                }
        
        content = content.strip()

        try:

            parsed = json.loads(content)
            # Handle both array and object with 'test_cases' key
            if isinstance(parsed, list):
                test_cases = parsed
            elif isinstance(parsed, dict) and 'test_cases' in parsed:
                test_cases = parsed['test_cases']
            else:
                # If it's an object but doesn't have test_cases key, try to find it
                test_cases = parsed.get('test_cases', [])
        except json.JSONDecodeError as e:
            # If LLM returns markdown or extra text, extract JSON
            logger.warning(f"Initial JSON parsing failed: {str(e)}")
            logger.debug(f"Raw content: {content[:500]}...")  # Log first 500 chars
            
            # Try to extract JSON from markdown code blocks
            code_block_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", content, re.DOTALL)
            if code_block_match:
                content = code_block_match.group(1)
                logger.info("Extracted JSON from markdown code block")
            else:
                # Try to find JSON array in the content
                match = re.search(r"\[.*\]", content, re.DOTALL)
                if match:
                    content = match.group(0)
                    logger.info("Extracted JSON array from content")

            # Try parsing the cleaned content
            try:
                test_cases = json.loads(content)
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse extracted JSON: {str(e2)}")
                logger.error(f"Problematic content around error: {content[max(0, e2.pos-100):e2.pos+100]}")
                
                # Last resort: try to fix common JSON issues
                try:
                    # Fix trailing commas
                    content = re.sub(r',(\s*[}\]])', r'\1', content)
                    # Fix missing commas between objects
                    content = re.sub(r'}\s*{', r'},{', content)
                    # Fix missing commas between array elements
                    content = re.sub(r']\s*\[', r'],[', content)
                    
                    test_cases = json.loads(content)
                    logger.info("Successfully parsed JSON after fixing common issues")
                except Exception as e3:
                    logger.error(f"All JSON parsing attempts failed: {str(e3)}")
                    # Return empty list as fallback
                    test_cases = []
        if test_cases:
            logger.info(f"Generated {len(test_cases)} test cases successfully")
            max_retries = 3
            temperature = 0.1
            for attempt in range(max_retries):
                judge_agent = TestCaseJudgeAgent(api_key=self.api_key)
                logging.info(f"Reviewing test cases with judge agent, attempt {attempt + 1}...")
                review_results = judge_agent.review_test_cases(test_cases=test_cases, api_spec=api_spec, temperature=temperature)
                
                average_score = review_results.get('overall_summary', {}).get('average_score', 0)
                logger.info(f"Attempt {attempt + 1}: Average test case score from judge agent: {average_score}")
                
                if average_score >= 80:
                    logger.info("Test cases are of good quality based on judge agent evaluation.")
                    return {"test_cases": test_cases, "usage": usage_data}
                logger.warning("Test cases did not meet the quality threshold. Retrying...")
                temperature += 0.1
            logger.warning("Test cases did not meet the quality threshold after retry.")
            return {"test_cases": [], "usage": usage_data}
        else:
            logger.warning("No test cases were generated. Returning empty results.")
            return {"test_cases": [], "usage": usage_data}