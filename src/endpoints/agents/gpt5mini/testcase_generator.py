import openai
from openai import AzureOpenAI
import json
import re
import logging
logger = logging.getLogger(__name__)
from endpoints.prompts.gpt5mini import get_testcase_prompt, get_system_message
from endpoints.agents.gpt5mini.testcase_judge_agent_gpt5mini import TestCaseJudgeAgentGPT5Mini as TestCaseJudgeAgent
 
class TestCaseGeneratorAgentGPT5Mini:
 
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.api_key = api_key
 
    def generate(self, api_spec: dict, temperature: float = None, max_completion_tokens: int = None, top_p: float = None, review: str = None) -> list:

        # Use prompt from prompts folder
        prompt = get_testcase_prompt(api_spec, review, temperature, max_completion_tokens, top_p)
        client = AzureOpenAI(
            api_key = self.api_key,  # Use the API key provided during initialization
            api_version = "2024-02-01",
            azure_endpoint = "https://ai-proxy.lab.epam.com"
        )
 
        # Build request parameters
        request_params = {
            "model": "gpt-5-mini-2025-08-07",
            "messages": [
                {"role": "system", "content": get_system_message()},
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add optional parameters if provided
        if max_completion_tokens is not None:
            request_params["max_completion_tokens"] = max_completion_tokens
        else:
            request_params["max_completion_tokens"] = 15000
            
        if temperature is not None:
            request_params["temperature"] = temperature
            
        if top_p is not None:
            request_params["top_p"] = top_p

        response = client.chat.completions.create(**request_params)
 
        # Parse the response content as JSON
 
        content = response.choices[0].message.content.strip()
 
        try:
            test_cases = json.loads(content)
        except Exception:
            # If LLM returns markdown or extra text, extract JSON
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                test_cases = json.loads(match.group(0))
            else:
                test_cases = []

        if test_cases:
            logger.info(f"Generated {len(test_cases)} test cases successfully")
            max_retries = 3
            temperature = 0.1
            for attempt in range(max_retries):
                judge_agent = TestCaseJudgeAgent(api_key=self.api_key)
                logger.info(f"Reviewing test cases with judge agent, attempt {attempt + 1}...")
                review_results = judge_agent.review_test_cases(test_cases=test_cases, api_spec=api_spec, temperature=temperature)
                
                average_score = review_results.get('overall_summary', {}).get('average_score', 0)
                logger.info(f"Attempt {attempt + 1}: Average test case score from judge agent: {average_score}")
                
                if average_score >= 80:
                    logger.info("Test cases are of good quality based on judge agent evaluation.")
                    return test_cases
                logger.warning("Test cases did not meet the quality threshold. Retrying...")
                temperature += 0.1
            logger.warning("Test cases did not meet the quality threshold after retry.")
            return []
        else:
            logger.warning("No test cases were generated. Returning empty list.")
            return []