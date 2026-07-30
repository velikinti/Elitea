import os
from typing import Literal
from pydantic import BaseModel, validator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


Environments = Literal["dev", "prod", "test", "demo"]   
Loglevels = Literal["DEBUG", "INFO", "WARNING", "ERROR", "NOTSET"]  
__current_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.abspath(os.path.join(__current_dir, os.pardir))


class LogSettings(BaseModel):
    level: Loglevels = "INFO"
    directory: str = os.path.join(_project_dir, "logs")
    dblogger: bool = False

    def __repr__(self):
        fields = "\n\t".join(f"{fld} = {getattr(self, fld)!r}" for fld in self.__annotations__)
        
        return f"{self.__class__.__name__}(\n\t{fields}\n)"
    
    @validator("directory")
    def validate_directory(cls, value):
        
        if not os.path.isdir(value):
            logging.info(f"Log directory {value} does not exist. Creating it.")
            os.makedirs(value, exist_ok=True)
        
        return value
              