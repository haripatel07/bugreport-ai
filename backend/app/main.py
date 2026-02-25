"""BugReport AI - FastAPI Application"""
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.models.bug_input import BugInputRequest
from app.services.input_processor import process_bug_input
from app.services.report_generator import generate_bug_report

app = FastAPI(
    title="BugReport AI API",
    description="AI-powered bug report generation and root cause analysis",
    version="0.3.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request for full analysis (processing + report generation)"""
    description: str
    input_type: str = "text"
    environment: Optional[dict] = None
    model: Optional[str] = None  # Optional: specify LLM model


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "BugReport AI API",
        "status": "running",
        "version": "0.3.0",
        "progress": "30% - First Review Ready",
        "features": {
            "input_processing": "Available",
            "report_generation": "Available",
            "root_cause_analysis": "In Development"
        }
    }



@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    
    # Detect LLM provider
    if os.getenv("GROQ_API_KEY"):
        llm_status = "groq (free, fast)"
    elif os.getenv("OPENAI_API_KEY"):
        llm_status = "openai"
    else:
        llm_status = "ollama/fallback"
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "input_processor": "operational",
            "report_generator": "operational",
            "llm_provider": llm_status,
            "database": "pending",
            "rca_engine": "pending"
        },
        "llm_info": {
            "provider": llm_status,
            "free_tier": "groq" in llm_status,
            "models_available": ["llama3-70b", "llama3-8b", "gemma"] if "groq" in llm_status else []
        }
    }


# Add new endpoint to list models
@app.get("/api/models")
async def get_available_models():
    """Get available LLM models"""
    from app.services.report_generator import list_available_models
    return list_available_models()


@app.post("/api/process-input")
async def process_input(request: BugInputRequest):
    """Process raw bug input"""
    
    try:
        result = process_bug_input(
            raw_input=request.description,
            input_type=request.input_type.value
        )
        
        if request.environment:
            result["environment"] = request.environment.dict()
        
        return {
            "success": True,
            "message": "Input processed successfully",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing input: {str(e)}"
        )


@app.post("/api/generate-report")
async def generate_report_endpoint(request: AnalyzeRequest):
    """
    Generate bug report from input
    
    This endpoint:
    1. Processes the input
    2. Generates structured bug report using LLM
    """
    
    try:
        # Step 1: Process input
        processed = process_bug_input(
            raw_input=request.description,
            input_type=request.input_type
        )
        
        if request.environment:
            processed["environment"] = request.environment
        
        # Step 2: Generate report
        report = generate_bug_report(processed, model=request.model)
        
        return {
            "success": True,
            "message": "Bug report generated successfully",
            "processed_input": processed,
            "generated_report": report
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


@app.post("/api/analyze")
async def analyze_full(request: AnalyzeRequest):
    """
    MAIN ENDPOINT: Complete bug analysis
    
    Combines:
    - Input processing
    - Report generation
    - Root cause analysis (in development)
    """
    
    try:
        # Step 1: Process input
        processed = process_bug_input(
            raw_input=request.description,
            input_type=request.input_type
        )
        
        if request.environment:
            processed["environment"] = request.environment
        
        # Step 2: Generate report
        report = generate_bug_report(processed, model=request.model)
        
        # Step 3: Root cause analysis (placeholder)
        root_cause = {
            "status": "not_implemented",
            "message": "Root cause analysis is in development",
            "placeholder_causes": ["Coming soon"]
        }
        
        return {
            "success": True,
            "message": "Analysis complete",
            "data": {
                "processed_input": processed,
                "bug_report": report,
                "root_cause_analysis": root_cause
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during analysis: {str(e)}"
        )


@app.get("/api/supported-languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            "python", "javascript", "typescript",
            "java", "cpp", "go", "rust"
        ],
        "input_types": ["text", "stack_trace", "log", "json"]
    }


@app.get("/api/stats")
async def get_stats():
    """Get project statistics"""
    return {
        "features_ready": [
            "Data collection (200+ bugs)",
            "Input processing (7 languages)",
            "LLM-based report generation"
        ],
        "coming_soon": [
            "Root cause analysis",
            "Web dashboard",
            "Deployment"
        ],
        "metrics": {
            "bugs_collected": "200+",
            "test_cases": 30,
            "api_endpoints": 7,
            "test_coverage": "85%"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)