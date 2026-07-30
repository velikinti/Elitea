import ast
from typing import List,Literal,Union,Optional
from pydantic import validator
from pydantic_settings import BaseSettings


from logconfig import LogSettings
from dotenv import load_dotenv

Environments=Literal["dev","prod","test","demo"]
Loglevels=Literal["DEBUG","INFO","WARNING","ERROR","NOTSET"]

load_dotenv()

class Settings(BaseSettings):
    """Application settings for FastAPI.These settings are loaded from environment variables or .env file."""
    environment: Environments = "dev"

    host: str
    port: int

    workers_count: int = 1

    # Enable uviorn loading
    reload: bool = False

    #List of allowed hosts for CORS middleware
    cors_origins: List[str]

    #Open API settings
    openapi_key:str
    openapi_base:str
    openapi_type:str
    openapi_version:str

    #logging settings
    log: LogSettings

    # Test framework configuration
    test_framework_path: str = "test_framework"  # Path to framework directory (from QA_TEST_FRAMEWORK_PATH in .env)
    base_output_folder: str = "outputfolder"  # Base output folder containing testcases/, framework/, and testscript/ subdirectories

    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Validate and parse CORS origins from a comma-separated string or a list."""
        if isinstance(v, str):
            try:
                result = ast.literal_eval(v)
                if isinstance(result, list) and all(isinstance(i, str) for i in result):
                    return [i.strip('/') for i in result]
                else:
                    raise ValueError("Invalid list format")
            except(SyntaxError, ValueError):
                return [i.strip().rstrip('/') for i in v.split(",")]
        elif isinstance(v, list) and all(isinstance(i, str) for i in v):
            return [i.rstrip('/') for i in v]
        raise ValueError("Invalid CORS origins format")

    @property
    def is_production(self):
        return  True if self.environment == "prod" else False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "QA_"
        str_strip_whitespace = True
        env_nested_delimiter = '__'
        
settings = Settings()