"""BugReport AI FastAPI application with v1 API contract and production hardening."""

import logging
import os
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth.router import router as auth_router
from app.db import get_db, init_db
from app.middleware.logging import RequestLoggingMiddleware
from app.models.analysis_record import AnalysisRecord
from app.models.bug_input import BugInputRequest
from app.rate_limit import limiter
from app.services.input_processor import process_bug_input
from app.services.rca_engine import RCAEngine, analyze_root_cause
from app.services.report_generator import generate_bug_report, list_available_models


def configure_logging() -> None:
    """Configure structlog for json/console output."""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "console").lower()
    renderer: structlog.types.Processor
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level, logging.INFO)),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger(__name__)
configure_logging()

app = FastAPI(
    title="BugReport AI API",
    description="AI-powered bug analysis API (versioned under /api/v1)",
    version="1.1.0",
)
app.state.limiter = limiter


class ContentSizeLimitMiddleware:
    """Reject requests larger than configured content-length threshold."""

    def __init__(self, app: FastAPI, max_content_size: int):
        self.app = app
        self.max_content_size = max_content_size

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers") or [])
            content_length = headers.get(b"content-length")
            if content_length and int(content_length) > self.max_content_size:
                response = JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request payload too large. Maximum allowed size is 1MB."},
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Too many requests. Retry after {retry_after}s.",
        },
        headers={"Retry-After": str(retry_after)},
    )


@app.on_event("startup")
def startup_event() -> None:
    """Initialize application resources on startup."""

    init_db()


app.add_middleware(ContentSizeLimitMiddleware, max_content_size=1024 * 1024)
app.add_middleware(RequestLoggingMiddleware)

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """Request for processing + analysis operations."""

    description: Optional[str] = None
    error_input: Optional[str] = None
    query: Optional[str] = None
    input_type: str = "text"
    environment: Optional[dict] = None
    model: Optional[str] = None

    @model_validator(mode="after")
    def populate_description(self):
        self.description = self.description or self.error_input or self.query
        if not self.description:
            raise ValueError("description is required")
        return self


class RecommendRequest(BaseModel):
    """Request body for the recommend-fix endpoint."""

    description: Optional[str] = None
    error_input: Optional[str] = None
    query: Optional[str] = None
    input_type: str = "text"
    environment: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    use_search: bool = True

    @model_validator(mode="after")
    def populate_description(self):
        self.description = self.description or self.error_input or self.query
        if not self.description:
            raise ValueError("description is required")
        return self


def _persist_record(
    db: Session,
    *,
    user_id: int,
    description: str,
    input_type: str,
    environment: Optional[Dict[str, Any]] = None,
    processed_input: Optional[Dict[str, Any]] = None,
    bug_report: Optional[Dict[str, Any]] = None,
    root_cause_analysis: Optional[Dict[str, Any]] = None,
    recommendations: Optional[Dict[str, Any]] = None,
    similar_bugs: Optional[List[Dict[str, Any]]] = None,
    status_value: str = "completed",
    error_message: Optional[str] = None,
) -> AnalysisRecord:
    record = AnalysisRecord(
        user_id=user_id,
        description=description,
        input_type=input_type,
        environment=environment,
        processed_input=processed_input,
        bug_report=bug_report,
        root_cause_analysis=root_cause_analysis,
        recommendations=recommendations,
        similar_bugs=similar_bugs,
        status=status_value,
        error_message=error_message,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_router)


@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request, response: Response):
    """Service root endpoint."""

    return {
        "message": "BugReport AI API",
        "status": "running",
        "version": "1.1.0",
        "api_prefix": "/api/v1",
    }


@app.get("/api/health")
@limiter.limit("60/minute")
async def health_check(request: Request, response: Response, db: Session = Depends(get_db)):
    """Infrastructure health check kept at legacy path."""

    if os.getenv("GROQ_API_KEY"):
        llm_status = "groq"
    elif os.getenv("OPENAI_API_KEY"):
        llm_status = "openai"
    else:
        llm_status = "fallback"

    try:
        rca_stats = RCAEngine().get_statistics()
        rca_status = f"operational ({rca_stats['total_patterns']} patterns)"
    except Exception as exc:
        rca_status = f"error: {exc}"

    try:
        db.execute(text("SELECT 1"))
        db_status = "operational"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "rca_engine": rca_status,
            "llm_provider": llm_status,
            "database": db_status,
        },
    }


@api_v1.get("/health")
@limiter.limit("60/minute")
async def versioned_health_check(request: Request, response: Response, db: Session = Depends(get_db)):
    """Versioned health endpoint for application clients."""

    return await health_check(request, response, db)


@app.get("/api/stats")
@limiter.limit("60/minute")
async def infra_stats(request: Request, response: Response):
    """Infrastructure stats endpoint kept at legacy path."""

    return {
        "version": "1.1.0",
        "api_version": "v1",
        "features": ["auth", "rate_limiting", "versioned_api", "structured_logging"],
    }


@api_v1.post("/process-input")
@limiter.limit("60/minute")
async def process_input(
    request: Request,
    response: Response,
    payload: BugInputRequest,
    current_user: User = Depends(get_current_user),
):
    """Process raw bug input into structured fields."""

    try:
        result = process_bug_input(raw_input=payload.description, input_type=payload.input_type.value)
        if payload.environment:
            result["environment"] = payload.environment.model_dump()
        return {"success": True, "message": "Input processed successfully", "data": result}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing input: {exc}")


@api_v1.post("/generate-report")
@limiter.limit("60/minute")
async def generate_report_endpoint(
    request: Request,
    response: Response,
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate bug report from processed input."""

    try:
        processed = process_bug_input(raw_input=payload.description, input_type=payload.input_type)
        if payload.environment:
            processed["environment"] = payload.environment
        report = generate_bug_report(processed, model=payload.model)
        return {
            "success": True,
            "message": "Bug report generated successfully",
            "processed_input": processed,
            "generated_report": report,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating report: {exc}")


@api_v1.post("/analyze-root-cause")
@limiter.limit("60/minute")
async def analyze_root_cause_endpoint(
    request: Request,
    response: Response,
    payload: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze probable root causes. Deprecated alias exists at /api/analyze-cause."""

    try:
        processed = process_bug_input(raw_input=payload.description, input_type=payload.input_type)
        if payload.environment:
            processed["environment"] = payload.environment
        rca_result = analyze_root_cause(processed)
        return {
            "success": True,
            "message": "Root cause analysis complete",
            "processed_input": processed,
            "root_cause_analysis": rca_result,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error analyzing root cause: {exc}")


@app.post(
    "/api/analyze-cause",
    deprecated=True,
    summary="Deprecated root cause endpoint alias",
)
@limiter.limit("60/minute")
async def analyze_cause_alias(request: Request, response: Response, payload: AnalyzeRequest):
    """Deprecated. Use /api/v1/analyze-root-cause instead."""

    return Response(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={
            "Location": "/api/v1/analyze-root-cause",
            "Deprecation": "true",
            "Sunset": "2026-09-01",
        },
    )


@api_v1.post("/analyze")
@limiter.limit("10/minute")
async def analyze_full(
    request: Request,
    response: Response,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full pipeline analysis under versioned contract."""

    try:
        processed = process_bug_input(raw_input=payload.description, input_type=payload.input_type)
        if payload.environment:
            processed["environment"] = payload.environment

        report = generate_bug_report(processed, model=payload.model)
        root_cause = analyze_root_cause(processed)

        record = _persist_record(
            db,
            user_id=current_user.id,
            description=payload.description,
            input_type=payload.input_type,
            environment=payload.environment,
            processed_input=processed,
            bug_report=report,
            root_cause_analysis=root_cause,
        )

        return {
            "success": True,
            "message": "Complete analysis finished",
            "data": {
                "record_id": record.id,
                "processed_input": processed,
                "bug_report": report,
                "root_cause_analysis": root_cause,
            },
        }
    except Exception as exc:
        db.rollback()
        _persist_record(
            db,
            user_id=current_user.id,
            description=payload.description,
            input_type=payload.input_type,
            environment=payload.environment,
            status_value="failed",
            error_message=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during analysis: {exc}")


@api_v1.post("/search/similar")
@limiter.limit("30/minute")
async def search_similar_bugs_endpoint(
    request: Request,
    response: Response,
    payload: AnalyzeRequest,
    k: int = Query(default=5, ge=1, le=20),
    min_score: float = Query(default=0.25, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
):
    """Find semantically similar bugs in indexed OSS issue corpus."""

    try:
        from app.services.search_engine import is_index_available, search_similar_bugs

        if not is_index_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search index not built yet. Run: python scripts/build_search_index.py",
            )

        results = search_similar_bugs(payload.description, k=k, min_score=min_score)
        return {
            "success": True,
            "query": payload.description[:200],
            "results_returned": len(results),
            "similar_bugs": results,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search error: {exc}")


@api_v1.post("/recommend-fix")
@limiter.limit("10/minute")
async def recommend_fix(
    request: Request,
    response: Response,
    payload: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full recommendation pipeline with optional semantic context."""

    try:
        processed = process_bug_input(raw_input=payload.description, input_type=payload.input_type)
        if payload.environment:
            processed["environment"] = payload.environment

        report = generate_bug_report(processed, model=payload.model)
        rca = analyze_root_cause(processed)

        similar: List[Dict[str, Any]] = []
        if payload.use_search:
            try:
                from app.services.search_engine import is_index_available, search_similar_bugs

                if is_index_available():
                    similar = search_similar_bugs(payload.description, k=3, min_score=0.25)
            except Exception as search_exc:
                logger.warning("similar_bug_search_failed", error=str(search_exc))

        from app.services.recommendation_engine import generate_recommendations

        recommendations = generate_recommendations(processed, rca, similar, preferred_model=payload.model)

        record = _persist_record(
            db,
            user_id=current_user.id,
            description=payload.description,
            input_type=payload.input_type,
            environment=payload.environment,
            processed_input=processed,
            bug_report=report,
            root_cause_analysis=rca,
            recommendations=recommendations,
            similar_bugs=similar,
        )

        return {
            "success": True,
            "message": "Fix recommendations generated",
            "data": {
                "record_id": record.id,
                "processed_input": processed,
                "bug_report": report,
                "root_cause_analysis": rca,
                "similar_bugs": similar,
                "recommendations": recommendations,
            },
        }
    except Exception as exc:
        db.rollback()
        _persist_record(
            db,
            user_id=current_user.id,
            description=payload.description,
            input_type=payload.input_type,
            environment=payload.environment,
            status_value="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {exc}",
        )


@api_v1.post("/analyze-free")
@limiter.limit("3/minute")
async def analyze_free(
    request: Request,
    response: Response,
    payload: RecommendRequest,
):
    """Guest analysis endpoint with strict rate limits and no history persistence."""

    try:
        processed = process_bug_input(raw_input=payload.description, input_type=payload.input_type)
        if payload.environment:
            processed["environment"] = payload.environment

        report = generate_bug_report(processed, model=payload.model)
        rca = analyze_root_cause(processed)

        similar: List[Dict[str, Any]] = []
        if payload.use_search:
            try:
                from app.services.search_engine import is_index_available, search_similar_bugs

                if is_index_available():
                    similar = search_similar_bugs(payload.description, k=2, min_score=0.25)
            except Exception as search_exc:
                logger.warning("similar_bug_search_failed", error=str(search_exc), guest_mode=True)

        from app.services.recommendation_engine import generate_recommendations

        recommendations = generate_recommendations(processed, rca, similar, preferred_model=payload.model)
        recommendations["recommendations"] = recommendations.get("recommendations", [])[:2]

        return {
            "success": True,
            "message": "Guest analysis complete. Sign in for full features and persistent history.",
            "guest_mode": True,
            "data": {
                "processed_input": processed,
                "bug_report": report,
                "root_cause_analysis": rca,
                "recommendations": recommendations,
                "similar_bugs": similar,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error during guest analysis: {exc}")


@api_v1.get("/history")
@limiter.limit("60/minute")
async def get_analysis_history(
    request: Request,
    response: Response,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return recent persisted analysis records for the authenticated user only."""

    base_query = db.query(AnalysisRecord).filter(AnalysisRecord.user_id == current_user.id)
    total_count = base_query.count()

    records = base_query.order_by(AnalysisRecord.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "count": len(records),
        "total_count": total_count,
        "offset": offset,
        "limit": limit,
        "records": [
            {
                "id": record.id,
                "description": record.description[:200],
                "input_type": record.input_type,
                "severity": (record.bug_report or {}).get("severity", "unknown"),
                "status": record.status,
                "created_at": record.created_at.isoformat(),
                "has_bug_report": bool(record.bug_report),
                "has_rca": bool(record.root_cause_analysis),
                "has_recommendations": bool(record.recommendations),
            }
            for record in records
        ],
    }


@api_v1.get("/history/{record_id}")
@limiter.limit("60/minute")
async def get_analysis_record(
    request: Request,
    response: Response,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return full details of a persisted analysis record for authenticated user."""

    record = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.id == record_id, AnalysisRecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    return {
        "success": True,
        "record": {
            "id": record.id,
            "description": record.description,
            "input_type": record.input_type,
            "environment": record.environment,
            "processed_input": record.processed_input,
            "bug_report": record.bug_report,
            "root_cause_analysis": record.root_cause_analysis,
            "recommendations": record.recommendations,
            "similar_bugs": record.similar_bugs,
            "status": record.status,
            "error_message": record.error_message,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        },
    }


@api_v1.delete("/history/{record_id}")
@limiter.limit("30/minute")
async def delete_analysis_record(
    request: Request,
    response: Response,
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a persisted analysis record belonging to authenticated user."""

    record = (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.id == record_id, AnalysisRecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    db.delete(record)
    db.commit()
    return {"success": True, "message": "Record deleted", "record_id": record_id}


@api_v1.get("/models")
@limiter.limit("60/minute")
async def get_available_models(request: Request, response: Response):
    """List available LLM models."""

    return list_available_models()


@api_v1.get("/supported-languages")
@limiter.limit("60/minute")
async def get_supported_languages(request: Request, response: Response):
    """List supported programming languages and input types."""

    return {
        "languages": ["python", "javascript", "typescript", "java", "cpp", "go", "rust"],
        "input_types": ["text", "stack_trace", "log", "json"],
    }


@api_v1.get("/rca/statistics")
@limiter.limit("60/minute")
async def get_rca_statistics(request: Request, response: Response):
    """Return root cause pattern coverage stats."""

    try:
        stats = RCAEngine().get_statistics()
        return {"success": True, "statistics": stats}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error getting RCA stats: {exc}")


@api_v1.get("/search/stats")
@limiter.limit("60/minute")
async def get_search_stats(request: Request, response: Response):
    """Return semantic search index metadata."""

    try:
        from app.services.search_engine import get_index_stats

        return {"success": True, "index_stats": get_index_stats()}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@api_v1.get("/stats")
@limiter.limit("60/minute")
async def get_api_stats(request: Request, response: Response):
    """Versioned API stats endpoint."""

    return {
        "api_version": "v1",
        "metrics": {
            "bugs_collected": 218,
            "rca_patterns": 31,
            "vector_index": "FAISS IndexFlatIP",
        },
    }


app.include_router(api_v1)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
