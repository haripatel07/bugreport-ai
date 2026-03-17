"""
Recommendation Engine
Produces targeted fix suggestions by combining three evidence sources:

  1. RCA Engine output   — rule-based probable causes with confidence scores
  2. Semantic Search     — historically similar bugs from real OSS projects
  3. LLM synthesis       — Groq/OpenAI/Ollama used to produce concrete fixes
                           (falls back to rule-based synthesis when no LLM key present)

Public interface
----------------
  generate_recommendations(processed_input, rca_results, similar_bugs) -> dict
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# LLM helpers (mirrors patterns from report_generator.py)
# ──────────────────────────────────────────────────────────────────────────────

def _try_groq(prompt: str, system: str) -> Optional[str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("Groq call failed: %s", exc)
        return None


def _try_openai(prompt: str, system: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None


def _call_llm(prompt: str, system: str) -> Optional[str]:
    """Try every provider in priority order; return first success or None."""
    return _try_groq(prompt, system) or _try_openai(prompt, system)


# ──────────────────────────────────────────────────────────────────────────────
# Context builders
# ──────────────────────────────────────────────────────────────────────────────

def _build_prompt(
    processed_input: Dict[str, Any],
    rca_results: Dict[str, Any],
    similar_bugs: List[Dict[str, Any]],
) -> str:
    """Construct a rich, structured prompt for the LLM."""

    lines: List[str] = ["# Bug Fix Recommendation Request\n"]

    # ── Error context ──────────────────────────────────────────────────────
    raw = (processed_input.get("raw_input") or "")[:500]
    if raw:
        lines.append(f"## Error Description\n{raw}\n")

    extracted = processed_input.get("extracted_data", {})
    error_info = extracted.get("error_info", {})
    error_types = error_info.get("error_types", [])
    if error_types:
        lines.append(f"Error types detected: {', '.join(error_types)}\n")

    lang = extracted.get("language")
    if lang:
        lines.append(f"Language: {lang}\n")

    # ── RCA summary ────────────────────────────────────────────────────────
    causes = rca_results.get("probable_causes", [])[:3]
    if causes:
        lines.append("## Root Cause Analysis (automated)")
        for i, c in enumerate(causes, 1):
            conf = int(c.get("confidence", 0) * 100)
            lines.append(f"  {i}. [{conf}% confidence] {c.get('cause', '')}")
            rec = c.get("recommendation", "")
            if rec:
                lines.append(f"     Hint: {rec}")
        lines.append("")

    # ── Similar historical bugs ────────────────────────────────────────────
    if similar_bugs:
        lines.append("## Similar Historical Bugs (from OSS issue tracker)")
        for bug in similar_bugs[:3]:
            sim = bug.get("similarity_pct", "?")
            repo = bug.get("repository", "?")
            title = bug.get("title", "")
            snippet = (bug.get("body_snippet") or "")[:200].replace("\n", " ")
            lines.append(f"  - [{sim} match] {repo}: {title}")
            if snippet:
                lines.append(f"    Context: {snippet}")
        lines.append("")

    lines.append(
        "## Task\n"
        "Provide 3 concrete, actionable fix recommendations.\n"
        "For each fix include:\n"
        "  - A plain-English explanation of WHY this fixes the bug\n"
        "  - A specific code snippet or command (language-appropriate)\n"
        "  - Difficulty: easy / medium / hard\n\n"
        "Be specific. Avoid generic advice.\n"
        "Format as plain numbered list — no markdown headers inside the fix text."
    )

    return "\n".join(lines)


_SYSTEM_PROMPT = (
    "You are a senior software engineer specialising in debugging production systems. "
    "Given an automated root cause analysis and a shortlist of similar historical bugs, "
    "you produce concise, implementable fix recommendations. "
    "Be direct and technically precise. Never hallucinate library names or APIs."
)


# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback (no LLM required)
# ──────────────────────────────────────────────────────────────────────────────

_FALLBACK_RULES: Dict[str, List[Dict[str, str]]] = {
    "AttributeError": [
        {
            "fix": "Guard attribute access with hasattr() or getattr(obj, 'attr', None)",
            "code": "value = getattr(obj, 'attribute_name', None)\nif value is not None:\n    result = value.compute()",
            "difficulty": "easy",
            "reason": "Prevents AttributeError when the attribute doesn't exist or the object is None",
        },
        {
            "fix": "Add a None-check before method calls on the object",
            "code": "if obj is not None:\n    result = obj.compute()\nelse:\n    logger.warning('obj was None, skipping compute')",
            "difficulty": "easy",
            "reason": "NoneType objects have no user-defined attributes; guarding eliminates the crash",
        },
    ],
    "TypeError": [
        {
            "fix": "Validate input type before the operation",
            "code": "if not isinstance(value, expected_type):\n    raise TypeError(f'Expected {expected_type}, got {type(value).__name__}')",
            "difficulty": "easy",
            "reason": "Surfaces the type mismatch earlier with a descriptive message",
        },
        {
            "fix": "Add explicit type conversion at the call site",
            "code": "result = process(str(value))  # or int(), float(), list() as needed",
            "difficulty": "easy",
            "reason": "Many TypeErrors arise from implicitly mismatched types at function boundaries",
        },
    ],
    "ImportError": [
        {
            "fix": "Install the missing package",
            "code": "pip install <package-name>\n# or, if using a virtual environment:\npip install -r requirements.txt",
            "difficulty": "easy",
            "reason": "ImportError most often means the package is absent from the environment",
        },
        {
            "fix": "Use a try/except import guard for optional dependencies",
            "code": "try:\n    import optional_lib\n    HAS_OPTIONAL = True\nexcept ImportError:\n    HAS_OPTIONAL = False",
            "difficulty": "easy",
            "reason": "Makes optional dependencies graceful so the module loads regardless",
        },
    ],
    "KeyError": [
        {
            "fix": "Use dict.get() with a sensible default instead of direct key access",
            "code": "value = my_dict.get('expected_key', default_value)",
            "difficulty": "easy",
            "reason": "dict.get() returns None (or the default) when the key is absent, no exception",
        },
        {
            "fix": "Log and validate dictionary keys before accessing them",
            "code": "if 'expected_key' not in my_dict:\n    logger.error('Missing key: %s. Available: %s', 'expected_key', list(my_dict.keys()))\n    return",
            "difficulty": "easy",
            "reason": "Makes the failure point explicit with actionable debug output",
        },
    ],
    "IndexError": [
        {
            "fix": "Check list length before indexing",
            "code": "if index < len(my_list):\n    item = my_list[index]\nelse:\n    item = None  # or a safe default",
            "difficulty": "easy",
            "reason": "IndexError happens when accessing a position that doesn't exist in the sequence",
        },
    ],
    "ConnectionRefusedError": [
        {
            "fix": "Add retry logic with exponential back-off",
            "code": (
                "import time\nfor attempt in range(5):\n"
                "    try:\n        conn = connect_to_service()\n        break\n"
                "    except ConnectionRefusedError:\n"
                "        wait = 2 ** attempt\n        time.sleep(wait)"
            ),
            "difficulty": "medium",
            "reason": "Services may be temporarily unavailable; retrying with back-off handles transient failures",
        },
        {
            "fix": "Verify the service is running and the port/host are correct",
            "code": "# Check service\ncurl -s http://localhost:YOUR_PORT/health\n# or\nnetstat -tlnp | grep YOUR_PORT",
            "difficulty": "easy",
            "reason": "ConnectionRefused often means the target process isn't running or is listening on a different port",
        },
    ],
}

_GENERIC_FALLBACK = [
    {
        "fix": "Add detailed logging around the failing code path",
        "code": "import logging\nlogger = logging.getLogger(__name__)\nlogger.debug('State before operation: %s', locals())",
        "difficulty": "easy",
        "reason": "Visibility into the state at the point of failure is the fastest path to a root cause",
    },
    {
        "fix": "Wrap the operation in a try/except and surface a meaningful error message",
        "code": (
            "try:\n    result = risky_operation()\nexcept Exception as exc:\n"
            "    logger.exception('risky_operation failed: %s', exc)\n    raise"
        ),
        "difficulty": "easy",
        "reason": "Catching the raw exception prevents silent failures and makes the stack trace actionable",
    },
    {
        "fix": "Write a small unit test that reproduces the failure",
        "code": (
            "def test_reproduce_bug():\n"
            "    # Arrange — set up the minimal state that triggers the error\n"
            "    # Act\n"
            "    with pytest.raises(ExpectedException):\n"
            "        broken_function(bad_input)"
        ),
        "difficulty": "medium",
        "reason": "A failing test gives you a fast feedback loop and prevents regression once fixed",
    },
]


def _rule_based_recommendations(
    processed_input: Dict[str, Any],
    rca_results: Dict[str, Any],
    similar_bugs: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """Produce fix suggestions without an LLM by matching error types to a lookup table."""
    extracted = processed_input.get("extracted_data", {})
    error_types = extracted.get("error_info", {}).get("error_types", [])

    for err_type in error_types:
        for key, fixes in _FALLBACK_RULES.items():
            if key.lower() in err_type.lower():
                return fixes

    # Augment generic fallback with the top RCA recommendation if available
    causes = rca_results.get("probable_causes", [])
    if causes:
        top_rec = causes[0].get("recommendation", "")
        if top_rec:
            augmented = [
                {
                    "fix": top_rec,
                    "code": causes[0].get("code_example") or "# See recommendation above",
                    "difficulty": "medium",
                    "reason": "Derived from automated root cause analysis",
                }
            ]
            augmented.extend(_GENERIC_FALLBACK[:2])
            return augmented

    return _GENERIC_FALLBACK


def _parse_llm_recommendations(raw: str) -> List[Dict[str, str]]:
    """
    Parse a free-form numbered list from the LLM into structured dicts.
    Tolerates a wide range of formatting styles.
    """
    items: List[Dict[str, str]] = []

    # Split on blank lines or numbered-list starters
    blocks = re.split(r"\n(?=\d+[\.\)])", raw.strip())
    for block in blocks:
        if not block.strip():
            continue
        # Strip leading number
        text = re.sub(r"^\d+[\.\)]\s*", "", block.strip())

        # Extract code block if present
        code_match = re.search(r"```[\w]*\n(.*?)```", text, re.DOTALL)
        code = code_match.group(1).strip() if code_match else ""
        if code_match:
            text = text[: code_match.start()] + text[code_match.end() :]

        # Extract difficulty tag
        diff_match = re.search(r"\bdifficulty[:\s]+(easy|medium|hard)\b", text, re.IGNORECASE)
        difficulty = diff_match.group(1).lower() if diff_match else "medium"
        if diff_match:
            text = text[: diff_match.start()] + text[diff_match.end() :]

        fix_text = text.strip()
        if len(fix_text) < 10:
            continue

        items.append(
            {
                "fix": fix_text[:400],
                "code": code[:600] if code else "",
                "difficulty": difficulty,
                "reason": "",  # LLM weaves reason into the fix text
            }
        )

    return items or [{"fix": raw[:600], "code": "", "difficulty": "medium", "reason": ""}]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_recommendations(
    processed_input: Dict[str, Any],
    rca_results: Dict[str, Any],
    similar_bugs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generate fix recommendations for a bug.

    Args:
        processed_input: Output from InputProcessor.process()
        rca_results:     Output from RCAEngine.analyze()
        similar_bugs:    Output from SearchEngine.search_similar_bugs() (optional)

    Returns:
        Dict with keys:
            recommendations       — list of fix dicts (fix, code, difficulty, reason)
            recommendation_source — 'llm_groq' | 'llm_openai' | 'rule_based'
            context_used          — summary of evidence sources consulted
            generation_time_ms    — wall-clock time in milliseconds
    """
    similar_bugs = similar_bugs or []
    t0 = time.perf_counter()

    prompt = _build_prompt(processed_input, rca_results, similar_bugs)
    llm_response = _call_llm(prompt, _SYSTEM_PROMPT)

    if llm_response:
        recommendations = _parse_llm_recommendations(llm_response)
        provider_key = "GROQ_API_KEY"
        source = "llm_groq" if os.getenv("GROQ_API_KEY") else "llm_openai"
    else:
        recommendations = _rule_based_recommendations(processed_input, rca_results, similar_bugs)
        source = "rule_based"

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    # Build a human-readable summary of what context drove the recommendations
    context_summary: List[str] = []
    causes = rca_results.get("probable_causes", [])
    if causes:
        context_summary.append(f"Top RCA cause: {causes[0].get('cause', '')[:100]}")
    if similar_bugs:
        top = similar_bugs[0]
        context_summary.append(
            f"Closest match: {top.get('repository', '?')} #{top.get('number', '?')} "
            f"({top.get('similarity_pct', '?')} similar)"
        )

    return {
        "recommendations": recommendations[:5],
        "recommendation_source": source,
        "context_used": context_summary,
        "generation_time_ms": elapsed_ms,
        "similar_bugs_consulted": len(similar_bugs),
        "rca_causes_consulted": len(causes),
    }
