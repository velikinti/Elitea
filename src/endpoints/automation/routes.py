import logging
from typing import List, Optional, Union, Dict, Any

from fastapi import APIRouter, Body, Depends, status, HTTPException

from endpoints.auth import require_api_key

from .schemas import (
    GenerateScriptRequest,
    GenerateScriptResponse,
    TestScript,
    FrameworkAnalysisResponse,
    FrameworkAnalysisRequest,
    IntegrateScriptToFrameworkRequest,
    IntegrateScriptToFrameworkResponse,
)

from settings import settings
from .schemas import (
    APISpecRequest,
    APISpecResponse,
    TestCaseRequest,
    TestCaseResponse,
    SwaggerSpecRequest,
    CurlSpecRequest,
)

from .utility import (
    generate_test_cases,
    generate_test_scripts,
    analyze_framework,
    integrate_script_to_framework,
    save_test_cases_to_file,
    LLMType,
)

from endpoints.automation.utility import generate_test_scripts as generate_test_scripts_util
from endpoints.agents.apispec_parser import APISpecParser


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/parse-swagger",
    response_model=APISpecResponse,
    summary="Convert Swagger/OpenAPI to API Specification",
)
async def parse_swagger_to_spec(request: SwaggerSpecRequest = Body(...)) -> APISpecResponse:
    """
    Convert Swagger/OpenAPI JSON or YAML to OpenAPI specification
    """
    try:
        parser = APISpecParser()
        api_specs = parser.parse("swagger", request.content)
        return APISpecResponse(specs=api_specs)
    except Exception as e:
        logger.error(f"Error parsing Swagger spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse Swagger input: {str(e)}",
        )


@router.post(
    "/parse-curl",
    response_model=APISpecResponse,
    summary="Convert curl command to API Specification",
)
async def parse_curl_to_spec(request: CurlSpecRequest = Body(...)) -> APISpecResponse:
    """
    Convert curl command to OpenAPI specification
    """
    try:
        parser = APISpecParser()
        api_spec = parser.parse("curl", request.content)
        # For curl, wrap the single spec in a list to match swagger format
        return APISpecResponse(specs=[api_spec])
    except Exception as e:
        logger.error(f"Error parsing curl command: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse curl input: {str(e)}",
        )


# Keep the legacy endpoint for backward compatibility
@router.post(
    "/parse-spec",
    response_model=APISpecResponse,
    summary="[DEPRECATED] Convert Swagger/Curl to API Specification",
)
async def parse_to_spec(request: APISpecRequest = Body(...)) -> APISpecResponse:
    """
    [DEPRECATED] Use /parse-swagger or /parse-curl instead.
    Convert Swagger JSON or curl command to OpenAPI specification
    """
    try:
        parser = APISpecParser()
        api_spec = parser.parse(request.input_type, request.content)
        # Handle both Swagger (list) and curl (single) cases
        specs = api_spec if isinstance(api_spec, list) else [api_spec]
        return APISpecResponse(specs=specs)
    except Exception as e:
        logger.error(f"Error parsing API spec: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse input: {str(e)}",
        )


@router.post(
    "/generate-tests",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from API specification.
    Uses LLM-based generation by default, with deterministic approach as fallback.
    """
    try:
        try:
            # Try LLM first by default using unified utility
            api_spec_dict = request.api_spec.dict() if hasattr(request.api_spec, "dict") else request.api_spec.model_dump()
            test_cases, _ = generate_test_cases(
                api_spec=api_spec_dict,
                llm_type=LLMType.LLM,
                review=request.review,
            )
            logger.info("Successfully generated test cases using LLM")

            # Save test cases to file
            test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
            return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)
        except Exception as llm_error:
            logger.warning(f"LLM generation failed, falling back to deterministic approach: {str(llm_error)}")

        # Fallback to deterministic approach
        generator = TestCaseGenerator()
        api_spec_dict = request.api_spec.dict() if hasattr(request.api_spec, "dict") else request.api_spec.model_dump()
        test_cases = generator.generate(api_spec_dict)
        logger.info("Successfully generated test cases using deterministic approach")

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)
    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-framework-analysis",
    response_model=FrameworkAnalysisResponse,
    summary="Generate and save framework analysis to outputfolder/framework",
    dependencies=[Depends(require_api_key)],
)
async def generate_framework_analysis(request: FrameworkAnalysisRequest) -> FrameworkAnalysisResponse:  # Add framework path in input
    """
    Analyze the test framework and save the results to outputfolder/framework directory.
    This endpoint requires no payload - it uses the framework path from settings.
    """
    try:
        # Use unified utility function
        framework_analysis, framework_results_path = analyze_framework(framework_path=request.framework_path)

        return FrameworkAnalysisResponse(
            message="Framework analysis completed and saved successfully",
            framework_results_path=framework_results_path,
        )
    except ValueError as e:
        logger.error(f"Error generating framework analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating framework analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate framework analysis: {str(e)}",
        )


@router.post(
    "/generate-test-scripts",
    response_model=GenerateScriptResponse,
    summary="Generate automation test scripts from test cases and framework",
    dependencies=[Depends(require_api_key)],
)
async def generate_test_scripts(request: GenerateScriptRequest = Body(...)) -> GenerateScriptResponse:
    """
    Generate automation test scripts for given test cases using the framework analysis markdown file.
    The markdown file should be generated first using /generate-framework-analysis endpoint.
    """
    try:
        # Validate: If review is provided, file must also be provided
        if request.review is not None and not request.file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="If 'review' is provided, 'file' field is required to specify which file to modify.",
            )

        # Convert test cases to dict format
        test_cases_dict = [tc.dict() if hasattr(tc, "dict") else tc.model_dump() for tc in request.test_cases]

        # Use unified utility function
        scripts_raw, output_dir = generate_test_scripts_util(
            test_cases=request.test_cases,
            framework_markdown_path=request.framework_analyzer_path,
            review=request.review,
            file_path=request.file,
        )

        # Convert to response format
        scripts = [TestScript(**{k: v for k, v in s.items() if k in ["test_case_code", "script"]}) for s in scripts_raw]

        return GenerateScriptResponse(scripts=scripts)
    except ValueError as e:
        logger.error(f"Error generating test scripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error generating test scripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test scripts: {str(e)}",
        )


@router.post(
    "/integrate-script-to-framework",
    response_model=IntegrateScriptToFrameworkResponse,
    summary="Integrate test script to framework and run it (no LLM used)",
    dependencies=[Depends(require_api_key)],
)
async def integrate_script_to_framework_endpoint(
    request: IntegrateScriptToFrameworkRequest = Body(...),
) -> IntegrateScriptToFrameworkResponse:
    """
    Copy test script to framework test directory and run it.
    This endpoint does NOT use LLM - it directly copies the file and executes it.

    Process:
    1. Copy test file to specified framework directory
    2. Run the test file using pytest
    3. Return success/failure with execution results

    Both test_file_name and framework_test_dir are MANDATORY.

    test_file_name can be:
    - Just filename: "test_login.py" (looks in outputfolder/testscript/)
    - Full path: "C:/path/to/test.py"

    framework_test_dir can be:
    - Relative path: "api/tests" (relative to framework root from settings)
    - Absolute path: "C:/path/to/framework/api/tests"

    Example requests:
    {
        "test_file_name": "test_login_20251230_180032.py",
        "framework_test_dir": "api/tests"
    }

    OR with full paths:
    {
        "test_file_name": "C:\\Users\\...\\test_v2_pet_123_20260108_174620.py",
        "framework_test_dir": "C:\\Users\\...\\cs-coreframework-python\\api\\tests"
    }
    """
    try:
        # Use utility function (no LLM)
        result = integrate_script_to_framework(
            test_file_name=request.test_file_name,
            framework_test_dir=request.framework_test_dir,
        )

        return IntegrateScriptToFrameworkResponse(**result)

    except ValueError as e:
        logger.error(f"Error integrating test to framework: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error integrating test to framework: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to integrate test to framework: {str(e)}",
        )


@router.post(
    "/generate-tests-llm",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using LLM",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_llm(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from OpenAPI specification using GPT-4o mini LLM
    """
    try:
        api_spec_dict = request.api_spec.dict() if hasattr(request.api_spec, "dict") else request.api_spec.model_dump()
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.LLM,
            review=request.review,
        )

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)

    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-tests-gpt5mini",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using GPT-5 mini LLM",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_gpt5mini(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from OpenAPI specification using GPT-5 mini LLM
    """
    try:
        api_spec_dict = request.api_spec.dict() if hasattr(request.api_spec, "dict") else request.api_spec.model_dump()
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.GPT5MINI,
            review=request.review,
        )

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)

    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-tests-gpt4o",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using GPT-4o",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_gpt4o(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from OpenAPI specification using GPT-4o model.
    This endpoint uses GPT-4o for comprehensive test case generation covering
    positive, negative, edge, and boundary scenarios.
    """
    try:
        api_spec_dict = request.api_spec.model_dump()
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.GPT4O,
            review=request.review,
        )

        logger.info(f"Successfully generated {len(test_cases)} test cases using GPT-4o")

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)

    except Exception as e:
        logger.error(f"Error generating test cases with GPT-4o: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-tests-o4-mini",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using o4 mini",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_runner_o4_mini(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from OpenAPI specification using o4 mini LLM
    """
    try:
        api_spec_dict = request.api_spec.model_dump()
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.O4MINI,
            review=request.review,
        )

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)

    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-tests-claude-sonnet-4",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using claude_sonnet_4",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_runner_claude_sonnet_4(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate test cases from OpenAPI specification using claude_sonnet_4 LLM
    """
    try:
        api_spec_dict = request.api_spec.model_dump()
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.CLAUDE_SONNET_4,
            review=request.review,
        )

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)
        return TestCaseResponse(test_cases=test_cases, test_cases_file_path=test_cases_file_path)

    except Exception as e:
        logger.error(f"Error generating test cases: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )


@router.post(
    "/generate-tests-gpt4",
    response_model=TestCaseResponse,
    summary="Generate test cases from API Specification using GPT-4.1",
    dependencies=[Depends(require_api_key)],
)
async def generate_tests_gpt4(request: TestCaseRequest = Body(...)) -> TestCaseResponse:
    """
    Generate comprehensive test cases from OpenAPI specification using GPT-4.1 model.
    """
    try:
        api_spec_dict = request.api_spec.dict() if hasattr(request.api_spec, "dict") else request.api_spec.model_dump()

        # Use unified utility function
        test_cases, _ = generate_test_cases(
            api_spec=api_spec_dict,
            llm_type=LLMType.GPT4,
            review=request.review,
        )

        # Save test cases to file
        test_cases_file_path = save_test_cases_to_file(test_cases, api_spec_dict)

        return TestCaseResponse(
            test_cases=test_cases,
            test_cases_file_path=test_cases_file_path,
        )

    except Exception as e:
        logger.error(f"Error generating test cases with GPT-4.1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test cases: {str(e)}",
        )