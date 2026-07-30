import openai
from openai import AzureOpenAI
import json
from endpoints.prompts.o4mini import get_testcase_prompt, get_system_message

import re
import logging
logger = logging.getLogger(__name__)
 
class o4_mini_TestCase_Gen_Agent:

    def __init__(self, api_key: str):

        openai.api_key = api_key
        self.api_key = api_key
 
    def generate(self, api_spec: dict, review: str = None) -> list:

        # Use prompt from prompts folder
        prompt = get_testcase_prompt(api_spec, review)
        client = AzureOpenAI(
        api_key = self.api_key,  # Use the API key provided during initialization
        api_version = "2025-03-01-preview",
        azure_endpoint = "https://ai-proxy.lab.epam.com"
        )

        response = client.chat.completions.create(

            model="o4-mini-2025-04-16",
            #model="gpt-4o",

            messages=[

                {"role": "system", "content": get_system_message()},

                {"role": "user", "content": prompt}

            ],

            max_completion_tokens= 5120,
            response_format={"type": "json_object"},
            # temperature=0.1
            
        )

        # Capture usage information
        usage_data = None
        if hasattr(response, 'usage') and response.usage:
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        # Parse the response content as JSON

        content = response.choices[0].message.content.strip()
        logger.info(f"Raw response content received from GPT-4o mini: {content}")  # Log first 500 characters of response

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

        return {"test_cases": test_cases, "usage": usage_data}