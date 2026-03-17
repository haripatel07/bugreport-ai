#!/usr/bin/env python3
"""
Week 8 Demo: Recommendation Engine

Shows the full pipeline end-to-end, without needing a running server.
Run:
    python scripts/demo_week8_recommendations.py

Requires:
    python scripts/build_search_index.py   (if requesting similar-bug context)

Works WITHOUT a Groq/OpenAI key — falls back to rule-based recommendations.
"""

import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


# ──────────────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
GREY   = "\033[90m"
BLUE   = "\033[94m"
RED    = "\033[91m"


def header(text: str):
    bar = "═" * 72
    print(f"\n{CYAN}{BOLD}{bar}{RESET}")
    print(f"{CYAN}{BOLD}  {text}{RESET}")
    print(f"{CYAN}{BOLD}{bar}{RESET}\n")


def section(label: str):
    print(f"\n{YELLOW}{BOLD}▶  {label}{RESET}")
    print(f"   {GREY}{'─' * 60}{RESET}")


def subsection(label: str):
    print(f"\n  {BLUE}{BOLD}{label}{RESET}")


def print_fix(rank: int, rec: dict):
    difficulty_colour = {
        "easy": GREEN,
        "medium": YELLOW,
        "hard": RED,
    }.get(rec.get("difficulty", "medium"), GREY)

    diff_tag = f"{difficulty_colour}[{rec.get('difficulty', '?')}]{RESET}"
    fix_text = rec.get("fix", "")
    reason = rec.get("reason", "")
    code = rec.get("code", "")

    print(f"\n  {BOLD}Fix #{rank}{RESET}  {diff_tag}")
    for line in textwrap.wrap(fix_text, 66):
        print(f"    {line}")

    if reason:
        print(f"    {GREY}Why: {reason}{RESET}")

    if code:
        print(f"    {GREY}Code example:{RESET}")
        for cline in code.strip().splitlines():
            print(f"      {CYAN}{cline}{RESET}")


# ──────────────────────────────────────────────────────────────────────────────
# Demo scenarios
# ──────────────────────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "label": "Python AttributeError on NoneType",
        "input_type": "stack_trace",
        "description": (
            "Traceback (most recent call last):\n"
            '  File "pipeline.py", line 88, in run_stage\n'
            "    output = stage.transform(data)\n"
            "AttributeError: 'NoneType' object has no attribute 'transform'"
        ),
    },
    {
        "label": "JavaScript / React TypeError",
        "input_type": "stack_trace",
        "description": (
            "TypeError: Cannot read properties of undefined (reading 'map')\n"
            "    at UserList (UserList.jsx:23)\n"
            "    at renderWithHooks (react-dom.development.js:14985)\n"
            "    at React component tree during render"
        ),
    },
    {
        "label": "Python ConnectionRefusedError (microservice)",
        "input_type": "log",
        "description": (
            "2026-03-06 11:02:45 ERROR worker.py:89 — "
            "ConnectionRefusedError: [Errno 111] Connection refused "
            "while connecting to redis://localhost:6379\n"
            "2026-03-06 11:02:45 CRITICAL task queue unavailable, "
            "worker shutting down"
        ),
    },
]


def run_scenario(scenario: dict):
    section(scenario["label"])

    # ── Step 1: Process input ──────────────────────────────────────────────
    from app.services.input_processor import process_bug_input

    processed = process_bug_input(
        raw_input=scenario["description"],
        input_type=scenario["input_type"],
    )

    extracted = processed.get("extracted_data", {})
    lang = extracted.get("language", "unknown")
    error_types = extracted.get("error_info", {}).get("error_types", [])
    print(f"\n  {GREEN}✓{RESET} Input processed — language: {lang}, "
          f"errors found: {', '.join(error_types) or 'none detected'}")

    # ── Step 2: Root cause analysis ────────────────────────────────────────
    from app.services.rca_engine import analyze_root_cause

    rca = analyze_root_cause(processed)
    causes = rca.get("probable_causes", [])
    if causes:
        top = causes[0]
        conf = int(top.get("confidence", 0) * 100)
        print(f"  {GREEN}✓{RESET} RCA complete — "
              f"top cause ({conf}%): {top.get('cause', '')[:80]}")

    # ── Step 3: Semantic search for similar bugs ───────────────────────────
    similar: list = []
    try:
        from app.services.search_engine import is_index_available, search_similar_bugs

        if is_index_available():
            similar = search_similar_bugs(scenario["description"], k=3, min_score=0.20)
            print(f"  {GREEN}✓{RESET} Semantic search — {len(similar)} similar bugs found")
        else:
            print(f"  {YELLOW}⚠{RESET}  Search index not built — skipping similar-bug context")
            print(f"      (Run: python scripts/build_search_index.py)")
    except Exception as exc:
        print(f"  {YELLOW}⚠{RESET}  Search unavailable: {exc}")

    # ── Step 4: Generate recommendations ──────────────────────────────────
    from app.services.recommendation_engine import generate_recommendations

    result = generate_recommendations(processed, rca, similar)

    source = result.get("recommendation_source", "?")
    elapsed = result.get("generation_time_ms", 0)
    source_label = {
        "llm_groq": f"{GREEN}Groq LLM (llama-3.3-70b){RESET}",
        "llm_openai": f"{GREEN}OpenAI GPT-3.5{RESET}",
        "rule_based": f"{YELLOW}Rule-based fallback{RESET}",
    }.get(source, source)

    print(f"  {GREEN}✓{RESET} Recommendations generated via {source_label} "
          f"({elapsed}ms)")

    if result.get("context_used"):
        subsection("Evidence used")
        for ctx in result["context_used"]:
            print(f"    • {ctx}")

    if similar:
        subsection("Most similar historical bugs")
        for hit in similar[:2]:
            print(f"    • [{hit.get('similarity_pct', '?')}] "
                  f"{hit.get('repository', '?')}: {hit.get('title', '')[:70]}")

    subsection("Fix Recommendations")
    for i, rec in enumerate(result.get("recommendations", []), 1):
        print_fix(i, rec)

    print()


def run_demo():
    header("BugReport AI — Week 8: Recommendation Engine Demo")

    for scenario in SCENARIOS:
        run_scenario(scenario)

    summary = f"""
{CYAN}{BOLD}{'═' * 72}{RESET}

{BOLD}Week 8 Deliverables{RESET}
  backend/app/services/recommendation_engine.py
    — Combines RCA + semantic search + LLM to generate fix recommendations
    — 3-tier fallback: Groq → OpenAI → rule-based (always produces output)
    — Rule-based lookup covers 6 common error types
  API endpoint: POST /api/recommend-fix

{BOLD}Full Pipeline (Weeks 1–8){RESET}
  Raw Error Text
    → InputProcessor        (Week 2)
    → RCAEngine             (Week 5)
    → BugReportGenerator    (Week 3)
    → SearchEngine          (Week 6–7)  ← similar historical bugs
    → RecommendationEngine  (Week 8)    ← concrete, actionable fixes
    └→ Structured response with: report + root cause + similar bugs + fixes

{BOLD}Next Steps (Weeks 9–12){RESET}
  Week 9  — React frontend dashboard
  Week 10 — PostgreSQL persistence
  Week 11 — Docker + CI/CD
  Week 12 — Cloud deployment
"""
    print(summary)


if __name__ == "__main__":
    run_demo()
