from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class SwaggerSpecRequest(BaseModel):
    content: str = Field(..., description="Swagger/OpenAPI JSON or YAML content")

class CurlSpecRequest(BaseModel):
    content: str = Field(..., description="Curl command string")

class APISpecRequest(BaseModel):
    input_type: str = Field(..., description="Type of input (swagger/curl)")
    content: str = Field(..., description="Swagger JSON or curl command")

class APISpec(BaseModel):
    method: str = Field(..., description="HTTP method")
    url: str = Field(..., description="Full URL")
    headers: Dict[str, Any] = Field(default={}, description="Request headers")
    body: Optional[Union[Dict[str, Any], List[Any]]] = Field(default=None, description="Request body")
    query_params: Dict[str, Any] = Field(default={}, description="Query parameters")

class APISpecResponse(BaseModel):
    specs: List[APISpec] = Field(..., description="List of API specifications")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GeneratorType(str, Enum):
    LLM = "llm"
    DETERMINISTIC = "deterministic"

class TestCaseRequest(BaseModel):
    api_spec: APISpec = Field(..., description="API specification")
    generator_type: GeneratorType = Field(default=GeneratorType.LLM, description="Type of test generator to use")
    review: Optional[str] = Field(
        None,
        description="Optional review/feedback to consider when generating test cases. If provided, the agent will fine-tune the prompt based on the review."
    )
    
    
class TestCase(BaseModel):
    name: str
    code: str
    description: str
    request: Dict[str, Any]
    expected_status: int
    steps: List[str]

class TestCaseResponse(BaseModel):
    test_cases: List[TestCase]
    test_cases_file_path: Optional[str] = Field(
        None,
        description="Path where test cases JSON file was saved (e.g., outputfolder/testcases/test_cases_20250102_120000.json)"
    )

class GenerateScriptRequest(BaseModel):
    test_cases: List[TestCase]
    framework_analyzer_path: str = Field(
        ..., 
        description="Path to framework analysis markdown file (.md) (required). Example: outputfolder/framework/framework_analysis_20251230_173305.md"
    )
    review: Optional[str] = Field(
        None,
        description="Optional review/feedback to consider when generating scripts. If provided, 'file' must also be provided to specify which file to modify."
    )
    file: Optional[str] = Field(
        None,
        description="Required if 'review' is provided: Specific test file path to modify (e.g., 'outputfolder/testscript/test_v2_pet_1_uploadImage_20260102_145622.py'). If 'review' is provided, this field is mandatory."
    )
 
class TestScript(BaseModel):
    test_case_code: str
    script: str
 
class GenerateScriptResponse(BaseModel):
    scripts: List[TestScript]

class FrameworkAnalysisResponse(BaseModel):
    message: str = Field(..., description="Status message")
    framework_results_path: str = Field(..., description="Path where framework analysis was saved")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FrameworkAnalysisRequest(BaseModel):
    framework_path: str = Field(..., description="Path to the framework markdown file to analyze")

class IntegrateScriptToFrameworkRequest(BaseModel):
    test_file_name: str = Field(..., description="Name of test file (can be just filename like 'test_login.py' or full path like 'C:/path/to/test.py')")
    framework_test_dir: str = Field(..., description="Framework test directory path where the test file should be placed (can be relative like 'api/tests' or absolute path like 'C:/path/to/framework/api/tests')")

class IntegrateScriptToFrameworkResponse(BaseModel):
    success: bool
    message: str
    source_file: str
    destination_file: str
    test_execution_success: Optional[bool] = Field(None, description="Whether the test execution passed")
    test_execution_output: Optional[str] = Field(None, description="Test execution output or failure reason")