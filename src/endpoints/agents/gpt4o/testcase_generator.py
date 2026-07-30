import openai
from openai import AzureOpenAI
import json
import logging
import re
import time
from endpoints.prompts.gpt4o import get_testcase_prompt, get_system_message

logger = logging.getLogger(__name__)


class TestCaseGeneratorGPT4o:
    """
    GPT-4o-based test case generator agent.
    For now this behaves like the GPT-4o-mini agent: simple JSON parsing,
    no additional JSON repair logic.
    """

    def __init__(self, api_key: str):
        """
        Initialize GPT-4o agent.

        Args:
            api_key: Azure OpenAI API key
        """
        self.api_key = api_key
        openai.api_key = api_key

    def generate(self, api_spec: dict, review: str = None) -> list:
        """
        Generate test cases using the LLM (configured here to behave like the
        GPT-4o-mini LLM, without extra JSON repair logic).

        Args:
            api_spec: API specification dictionary
            review: Optional review/feedback to consider when generating test cases

        Returns:
            List of test case dictionaries
        """
        # Use prompt from prompts folder
        prompt = get_testcase_prompt(api_spec, review)

        client = AzureOpenAI(
            api_key=self.api_key,  # Use the API key provided during initialization
            api_version="2024-02-01",
            azure_endpoint="https://ai-proxy.lab.epam.com"
        )

        start_time = time.perf_counter()

        response = client.chat.completions.create(
            # Use GPT-4o model and ask the API to enforce JSON output
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": get_system_message()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10000,
            temperature=0.1  # Low temperature for more deterministic JSON structure
        )

        elapsed = time.perf_counter() - start_time
        logger.info(f"GPT-4o completion time: {elapsed:.2f} seconds")

        # With response_format=json_object, the content is guaranteed to be a JSON object string
        content = response.choices[0].message.content.strip()
        logger.debug(f"GPT-4o JSON content length: {len(content)}")
        logger.debug(f"GPT-4o JSON content preview (first 500 chars): {content[:500]}")

        data = json.loads(content)
        test_cases = data.get("test_cases", [])

        # Filter out malformed entries to avoid response validation errors
        cleaned = []
        for tc in test_cases:
            if not isinstance(tc, dict):
                continue
            if "expected_status" not in tc or "steps" not in tc:
                continue
            cleaned.append(tc)

        if len(cleaned) != len(test_cases):
            logger.warning(
                f"Filtered out {len(test_cases) - len(cleaned)} malformed test cases "
                f"(missing expected_status or steps)"
            )

        return cleaned

