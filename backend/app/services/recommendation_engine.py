"""Recommendation engine that blends RCA, semantic search, and LLM synthesis."""

import json
import os
import time
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


def _try_groq(prompt: str, system: str, preferred_model: Optional[str] = None) -> tuple[Optional[str], str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None, "groq", "none"
    try:
        from groq import Groq

        model_map = {
            "llama3-70b": "llama-3.3-70b-versatile",
            "llama3-8b": "llama-3.1-8b-instant",
            "gemma": "gemma2-9b-it",
        }
        model_name = model_map.get(preferred_model or "", "llama-3.3-70b-versatile")
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content.strip(), "groq", model_name
    except Exception as exc:
        logger.warning("recommendation_llm_failed", provider="groq", error=str(exc))
        return None, "groq", "none"


def _try_openai(prompt: str, system: str, preferred_model: Optional[str] = None) -> tuple[Optional[str], str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "openai", "none"
    try:
        import openai

        model_name = preferred_model or "gpt-4o-mini"
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content.strip(), "openai", model_name
    except Exception as exc:
        logger.warning("recommendation_llm_failed", provider="openai", error=str(exc))
        return None, "openai", "none"


def _build_prompt(
    processed_input: Dict[str, Any],
    rca_results: Dict[str, Any],
    similar_bugs: List[Dict[str, Any]],
) -> str:
    extracted = processed_input.get("extracted_data", {})
    error_info = extracted.get("error_info", {})

    return (
        "Generate concrete debugging recommendations from this context.\n"
        f"Error input: {(processed_input.get('raw_input') or '')[:1200]}\n"
        f"Error types: {error_info.get('error_types', [])}\n"
        f"Language: {extracted.get('language')}\n"
        f"Top RCA causes: {rca_results.get('probable_causes', [])[:3]}\n"
        f"Similar bugs: {similar_bugs[:3]}\n\n"
        "Return strict JSON with this shape:\n"
        "{\n"
        '  "recommendations": [\n'
        "    {\n"
        '      "title": "short fix title",\n'
        '      "description": "why this fix works",\n'
        '      "implementation_steps": ["step 1", "step 2"],\n'
        '      "code_example": "optional code snippet or null",\n'
        '      "difficulty": "easy|medium|hard"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Return 3 recommendations."
    )


_SYSTEM_PROMPT = (
    "You are a senior software engineer. Provide practical, high-signal fixes only. "
    "If uncertain, provide the safest deterministic remediation path."
)


def _normalize_item(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    difficulty = str(item.get("difficulty") or "medium").lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    steps = item.get("implementation_steps")
    if not isinstance(steps, list):
        steps = [s.strip() for s in str(steps or "").split("\n") if s.strip()]

    code_example = item.get("code_example")
    if code_example == "":
        code_example = None

    return {
        "title": str(item.get("title") or f"Recommendation {index + 1}")[:140],
        "description": str(item.get("description") or "Apply this targeted fix and verify with tests.")[:600],
        "implementation_steps": [str(step)[:220] for step in steps][:6],
        "code_example": str(code_example)[:1200] if code_example is not None else None,
        "difficulty": difficulty,
    }


def _parse_llm_recommendations(raw: str) -> List[Dict[str, Any]]:
    try:
        payload = json.loads(raw)
    except Exception:
        return []

    recs = payload.get("recommendations", []) if isinstance(payload, dict) else []
    if not isinstance(recs, list):
        return []

    normalized = []
    for index, item in enumerate(recs[:5]):
        if isinstance(item, dict):
            normalized.append(_normalize_item(item, index))
    return normalized


_FALLBACK_RULES: Dict[str, List[Dict[str, Any]]] = {
    "AttributeError": [
        {
            "title": "Guard object attribute access",
            "description": "The crash indicates an attribute is accessed on None or on an object without that field.",
            "implementation_steps": [
                "Use getattr(obj, 'attribute', None) when reading optional fields.",
                "Add a guard clause before invoking methods on the object.",
                "Write a regression test for the missing-attribute path.",
            ],
            "code_example": "value = getattr(obj, 'attribute_name', None)\nif value is None:\n    return None\nreturn value.compute()",
            "difficulty": "easy",
        }
    ],
    "TypeError": [
        {
            "title": "Validate and coerce boundary input types",
            "description": "TypeError usually comes from implicit type assumptions across function boundaries.",
            "implementation_steps": [
                "Validate argument types at API/service boundaries.",
                "Convert incoming values to expected types before use.",
                "Raise descriptive errors when coercion fails.",
            ],
            "code_example": "if not isinstance(payload.get('count'), int):\n    raise TypeError('count must be int')",
            "difficulty": "easy",
        }
    ],
    "ImportError": [
        {
            "title": "Stabilize dependency resolution",
            "description": "Import errors are commonly caused by missing packages or inconsistent environments.",
            "implementation_steps": [
                "Pin and install dependencies from requirements.txt.",
                "Run imports during startup checks to fail fast.",
                "Add optional import guards for truly optional packages.",
            ],
            "code_example": "pip install -r requirements.txt",
            "difficulty": "easy",
        }
    ],
}

_GENERIC_FALLBACK: List[Dict[str, Any]] = [
    {
        "title": "Add focused diagnostics around the failure",
        "description": "Capture critical state before the failing operation so the exact trigger is visible.",
        "implementation_steps": [
            "Log key inputs right before the error path.",
            "Capture exception stack traces with context.",
            "Verify with a reproducible test case.",
        ],
        "code_example": "logger.info('pre_failure_state', payload=payload)",
        "difficulty": "easy",
    },
    {
        "title": "Create a regression test and patch the guard path",
        "description": "A failing test for the known bad input prevents future regressions after the fix.",
        "implementation_steps": [
            "Write a test that reproduces the current failure.",
            "Apply the smallest code guard/fix to make the test pass.",
            "Run full test suite to ensure no collateral breakage.",
        ],
        "code_example": "def test_regression_case():\n    with pytest.raises(ExpectedError):\n        handler(bad_input)",
        "difficulty": "medium",
    },
]


def _rule_based_recommendations(processed_input: Dict[str, Any], rca_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    error_types = processed_input.get("extracted_data", {}).get("error_info", {}).get("error_types", [])
    for err_type in error_types:
        for key, fixes in _FALLBACK_RULES.items():
            if key.lower() in str(err_type).lower():
                return fixes

    probable_causes = rca_results.get("probable_causes", [])
    if probable_causes:
        top = probable_causes[0]
        enriched = {
            "title": "Address top RCA probable cause",
            "description": str(top.get("recommendation") or top.get("cause") or "Apply RCA recommendation."),
            "implementation_steps": [
                "Apply the RCA recommendation in the failing code path.",
                "Add or update tests for this failure mode.",
                "Re-run analysis to confirm confidence decreases for the old cause.",
            ],
            "code_example": top.get("code_example"),
            "difficulty": "medium",
        }
        return [enriched, *_GENERIC_FALLBACK][:3]

    return _GENERIC_FALLBACK


def generate_recommendations(
    processed_input: Dict[str, Any],
    rca_results: Dict[str, Any],
    similar_bugs: Optional[List[Dict[str, Any]]] = None,
    preferred_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate recommendations with unified schema for frontend consumption."""

    similar_bugs = similar_bugs or []
    started = time.perf_counter()

    prompt = _build_prompt(processed_input, rca_results, similar_bugs)

    llm_raw = None
    llm_provider = "none"
    llm_model = "none"

    for caller in (_try_groq, _try_openai):
        llm_raw, llm_provider, llm_model = caller(prompt, _SYSTEM_PROMPT, preferred_model)
        if llm_raw:
            break

    recommendations: List[Dict[str, Any]]
    source: str

    if llm_raw:
        recommendations = _parse_llm_recommendations(llm_raw)
        if recommendations:
            source = f"llm_{llm_provider}"
        else:
            recommendations = _rule_based_recommendations(processed_input, rca_results)
            source = "rule_based"
    else:
        recommendations = _rule_based_recommendations(processed_input, rca_results)
        source = "rule_based"

    duration_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "recommendation_generation",
        provider=llm_provider,
        model=llm_model,
        duration_ms=duration_ms,
        success=bool(recommendations),
        source=source,
    )

    return {
        "recommendations": recommendations[:5],
        "recommendation_source": source,
        "context_used": [
            f"rca_causes={len(rca_results.get('probable_causes', []))}",
            f"similar_bugs={len(similar_bugs)}",
        ],
        "generation_time_ms": duration_ms,
        "similar_bugs_consulted": len(similar_bugs),
        "rca_causes_consulted": len(rca_results.get("probable_causes", [])),
    }
