"""BugReport AI - FastAPI Application
Weeks 1-8 complete: Input processing, report generation, RCA, semantic search,
and recommendation engine.
"""
import os
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.models.bug_input import BugInputRequest
from app.services.input_processor import process_bug_input
from app.services.report_generator import generate_bug_report
from app.services.rca_engine import analyze_root_cause

app = FastAPI(
    title="BugReport AI API",
    description="AI-powered bug report generation, root cause analysis, semantic search, and fix recommendations",
    version="0.8.0"
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
        "version": "0.8.0",
        "progress": "65% - Weeks 1-8 Complete",
        "features": {
            "input_processing":    "✅ Available (Week 2)",
            "report_generation":   "✅ Available (Week 3)",
            "root_cause_analysis": "✅ Available (Week 5)",
            "semantic_search":     "✅ Available (Week 6-7)",
            "recommendations":     "✅ Available (Week 8)",
            "database":            "⏳ Coming in Week 10",
            "frontend":            "⏳ Coming in Week 9"
        }
    }



@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    
    from app.services.rca_engine import RCAEngine
    
    # Detect LLM provider
    if os.getenv("GROQ_API_KEY"):
        llm_status = "groq (free, fast)"
    elif os.getenv("OPENAI_API_KEY"):
        llm_status = "openai"
    else:
        llm_status = "ollama/fallback"
    
    # Check RCA engine
    try:
        engine = RCAEngine()
        stats = engine.get_statistics()
        rca_status = f"operational ({stats['total_patterns']} patterns)"
    except Exception as e:
        rca_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "input_processor": "operational",
            "report_generator": "operational",
            "rca_engine": rca_status,
            "llm_provider": llm_status,
            "database": "pending"
        },
        "llm_info": {
            "provider": llm_status,
            "free_tier": "groq" in llm_status,
            "models_available": ["llama3-70b", "llama3-8b", "gemma"] if "groq" in llm_status else []
        },
        "weeks_completed": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6", "Week 7", "Week 8"]
    }


@app.post("/api/search/similar")
async def search_similar_bugs_endpoint(
    request: AnalyzeRequest,
    k: int = Query(default=5, ge=1, le=20, description="Number of results to return"),
    min_score: float = Query(default=0.25, ge=0.0, le=1.0, description="Minimum similarity score"),
):
    """
    Find semantically similar bugs from the indexed OSS issue corpus. (Week 6–7)

    Encodes the input text as a vector and performs approximate nearest-neighbour
    search over the FAISS index built from 177 real GitHub issues.

    Requires the search index to be built first:
        python scripts/build_search_index.py
    """
    try:
        from app.services.search_engine import is_index_available, search_similar_bugs

        if not is_index_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Search index not built yet. "
                    "Run: python scripts/build_search_index.py"
                ),
            )

        results = search_similar_bugs(request.description, k=k, min_score=min_score)
        return {
            "success": True,
            "query": request.description[:200],
            "results_returned": len(results),
            "similar_bugs": results,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {exc}",
        )


@app.get("/api/search/stats")
async def get_search_stats():
    """Return statistics about the current semantic search index. (Week 6–7)"""
    try:
        from app.services.search_engine import get_index_stats
        stats = get_index_stats()
        return {"success": True, "index_stats": stats}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


class RecommendRequest(BaseModel):
    """Request body for the recommend-fix endpoint"""
    description: str
    input_type: str = "text"
    environment: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    use_search: bool = True  # whether to enrich with semantic search context


@app.post("/api/recommend-fix")
async def recommend_fix(request: RecommendRequest):
    """
    Full pipeline: process → RCA → semantic search → recommendations. (Week 8)

    Returns actionable fix suggestions derived from:
    • Automated root cause analysis (pattern matching)
    • Semantically similar historical bugs (FAISS vector search)
    • LLM synthesis (Groq / OpenAI / rule-based fallback)
    """
    try:
        # Step 1 — Process input
        processed = process_bug_input(
            raw_input=request.description,
            input_type=request.input_type,
        )
        if request.environment:
            processed["environment"] = request.environment

        # Step 2 — Root cause analysis
        rca = analyze_root_cause(processed)

        # Step 3 — Semantic search (optional, gracefully degraded)
        similar: List[Dict] = []
        if request.use_search:
            try:
                from app.services.search_engine import is_index_available, search_similar_bugs
                if is_index_available():
                    similar = search_similar_bugs(request.description, k=3, min_score=0.25)
            except Exception as search_exc:
                # Search failure must not block recommendations
                pass

        # Step 4 — Generate recommendations
        from app.services.recommendation_engine import generate_recommendations
        recommendations = generate_recommendations(processed, rca, similar)

        return {
            "success": True,
            "message": "Fix recommendations generated",
            "data": {
                "processed_input": processed,
                "root_cause_analysis": rca,
                "similar_bugs": similar,
                "recommendations": recommendations,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {exc}",
        )


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


@app.post("/api/analyze-root-cause")
async def analyze_root_cause_endpoint(request: AnalyzeRequest):
    """
    Analyze root cause of a bug (Week 5 feature)

    Takes processed bug input and returns probable causes with recommendations.
    """

    try:
        # Process input first
        processed = process_bug_input(
            raw_input=request.description,
            input_type=request.input_type
        )

        if request.environment:
            processed["environment"] = request.environment

        # Perform RCA
        rca_result = analyze_root_cause(processed)

        return {
            "success": True,
            "message": "Root cause analysis complete",
            "processed_input": processed,
            "root_cause_analysis": rca_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing root cause: {str(e)}"
        )


# Alias kept for backwards-compatibility with older PPT/demo references
@app.post("/api/analyze-cause", include_in_schema=False)
async def analyze_cause_alias(request: AnalyzeRequest):
    """Alias for /api/analyze-root-cause — kept for backwards compatibility."""
    return await analyze_root_cause_endpoint(request)


@app.post("/api/analyze")
async def analyze_full(request: AnalyzeRequest):
    """
    MAIN ENDPOINT: Complete bug analysis
    
    NOW INCLUDES ROOT CAUSE ANALYSIS (Week 5)
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
        
        # Step 3: Root cause analysis (NOW REAL!)
        root_cause = analyze_root_cause(processed)
        
        return {
            "success": True,
            "message": "Complete analysis finished (40% project milestone)",
            "data": {
                "processed_input": processed,
                "bug_report": report,
                "root_cause_analysis": root_cause,
                "completion_status": "65% - Weeks 1-8 Complete"
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


@app.get("/api/rca/statistics")
async def get_rca_statistics():
    """Get RCA engine statistics (Week 5 feature)"""
    
    try:
        from app.services.rca_engine import RCAEngine
        engine = RCAEngine()
        stats = engine.get_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting RCA statistics: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """Get project statistics"""
    return {
        "features_ready": [
            "Data collection (200+ bugs)",
            "Input processing (7 languages)",
            "LLM-based report generation",
            "Root cause analysis (10 error patterns)"
        ],
        "coming_soon": [
            "React frontend dashboard (Week 9)",
            "PostgreSQL persistence (Week 10)",
            "Docker + CI/CD (Week 11-12)"
        ],
        "metrics": {
            "bugs_collected": "177",
            "test_cases": 30,
            "api_endpoints": 13,
            "test_coverage": "85%",
            "rca_patterns": 10,
            "embedding_model": "all-MiniLM-L6-v2 (384-dim)",
            "vector_index": "FAISS IndexFlatIP"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)