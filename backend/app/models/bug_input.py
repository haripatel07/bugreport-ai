"""
Pydantic models for bug input validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InputType(str, Enum):
    """Supported input types"""
    TEXT = "text"
    STACK_TRACE = "stack_trace"
    LOG = "log"
    JSON = "json"


class ProgrammingLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"


class EnvironmentInfo(BaseModel):
    """Environment details"""
    os: Optional[str] = Field(None, description="Operating system")
    os_version: Optional[str] = None
    language_version: Optional[str] = Field(None, description="Python 3.9, Node 18, etc.")
    dependencies: Optional[List[str]] = Field(default_factory=list)
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class StackFrame(BaseModel):
    """Single stack trace frame"""
    file: str
    line: int
    function: Optional[str] = None
    code: Optional[str] = None
    column: Optional[int] = None


class ErrorInfo(BaseModel):
    """Extracted error information"""
    error_types: List[str] = Field(default_factory=list)
    error_messages: List[str] = Field(default_factory=list)
    error_codes: List[str] = Field(default_factory=list)


class FileReference(BaseModel):
    """File referenced in bug report"""
    path: str
    line: Optional[int] = None
    language: Optional[str] = None


class BugInputRequest(BaseModel):
    """Request model for bug input submission"""
    
    description: str = Field(..., min_length=10, description="Bug description")
    input_type: InputType = Field(InputType.TEXT, description="Type of input")
    environment: Optional[EnvironmentInfo] = None
    additional_context: Optional[str] = Field(None, max_length=2000)
    
    @validator('description')
    def description_must_be_meaningful(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Application crashes with NullPointerException when user clicks submit button",
                "input_type": "text",
                "environment": {
                    "os": "Ubuntu 22.04",
                    "language_version": "Python 3.9.7"
                },
                "additional_context": "This only happens when user field is empty"
            }
        }


class ProcessedBugData(BaseModel):
    """Result of input processing"""
    
    raw_input: str
    input_type: str
    processed_at: datetime
    extracted_data: Dict[str, Any]
    
    # Structured extractions
    error_info: Optional[ErrorInfo] = None
    files: List[FileReference] = Field(default_factory=list)
    language: Optional[ProgrammingLanguage] = None
    stack_frames: Optional[List[StackFrame]] = None
    
    # Quality metrics
    completeness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    class Config:
        schema_extra = {
            "example": {
                "raw_input": "Traceback...",
                "input_type": "stack_trace",
                "processed_at": "2025-02-25T10:30:00",
                "extracted_data": {},
                "language": "python"
            }
        }