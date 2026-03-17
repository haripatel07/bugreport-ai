#!/usr/bin/env python3
"""
Week 6–7 Demo: Semantic Bug Search

Demonstrates the new similarity-search feature without needing a running API server.
Just run:
    python scripts/demo_week67_search.py

Requires the search index to be built first:
    python scripts/build_search_index.py
"""

import sys
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


# ──────────────────────────────────────────────────────────────────────────────
# ANSI colour helpers
# ──────────────────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
GREY   = "\033[90m"
RED    = "\033[91m"


def header(text: str):
    bar = "─" * 70
    print(f"\n{CYAN}{BOLD}{bar}{RESET}")
    print(f"{CYAN}{BOLD}  {text}{RESET}")
    print(f"{CYAN}{BOLD}{bar}{RESET}\n")


def section(label: str):
    print(f"\n{YELLOW}{BOLD}▶  {label}{RESET}")


def result_card(rank: int, hit: dict):
    score_pct = hit.get("similarity_pct", "?")
    score_val = hit.get("similarity_score", 0)

    # Colour the score based on confidence
    if score_val >= 0.70:
        colour = GREEN
    elif score_val >= 0.50:
        colour = YELLOW
    else:
        colour = GREY

    repo = hit.get("repository", "unknown/repo")
    number = hit.get("number", "?")
    state = hit.get("state", "?")
    title = hit.get("title", "(no title)")
    snippet = hit.get("body_snippet", "")[:200].replace("\n", " ").strip()

    print(f"  {BOLD}#{rank}  [{colour}{score_pct}{RESET}{BOLD}]{RESET}  {title}")
    print(f"      {GREY}repo: {repo}  ·  issue #{number}  ·  state: {state}{RESET}")
    if snippet:
        wrapped = textwrap.fill(snippet, width=65, initial_indent="      ", subsequent_indent="      ")
        print(f"{GREY}{wrapped}{RESET}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Main demo
# ──────────────────────────────────────────────────────────────────────────────

DEMO_QUERIES = [
    {
        "label": "Python AttributeError (stack trace)",
        "query": (
            "Traceback (most recent call last):\n"
            '  File "main.py", line 42, in process\n'
            "    result = obj.compute()\n"
            "AttributeError: 'NoneType' object has no attribute 'compute'"
        ),
    },
    {
        "label": "React / JavaScript TypeError",
        "query": "TypeError: Cannot read properties of undefined (reading 'map') at React component render",
    },
    {
        "label": "Kubernetes Pod crash-loop",
        "query": (
            "Pod keeps restarting with CrashLoopBackOff. "
            "Container exits with code 1. OOMKilled in events log."
        ),
    },
    {
        "label": "TensorFlow shape mismatch",
        "query": (
            "InvalidArgumentError: Incompatible shapes: [32,128] vs [32,64] "
            "during model.fit() in tensorflow training loop"
        ),
    },
]


def run_demo():
    header("BugReport AI — Week 6/7: Semantic Bug Search Demo")

    # ── Check index exists ─────────────────────────────────────────────────
    from app.services.search_engine import get_index_stats, is_index_available

    if not is_index_available():
        print(f"{RED}Search index not found.{RESET}")
        print("Build it first with:")
        print(f"  {BOLD}python scripts/build_search_index.py{RESET}\n")
        sys.exit(1)

    stats = get_index_stats()
    print(f"{GREEN}✓{RESET} Index ready — {stats.get('total_indexed', '?')} bugs indexed")
    print(f"  Embedding model : sentence-transformers/all-MiniLM-L6-v2  (384-dim)")
    print(f"  Index type      : {stats.get('index_type', 'FAISS IndexFlatIP (cosine)')}")
    print(f"  Built in        : {stats.get('build_time_seconds', '?')}s\n")

    # ── Run each demo query ────────────────────────────────────────────────
    from app.services.search_engine import search_similar_bugs

    for demo in DEMO_QUERIES:
        section(demo["label"])

        q = demo["query"]
        display_q = q[:120] + ("…" if len(q) > 120 else "")
        print(f"  {GREY}Query: {display_q}{RESET}\n")

        hits = search_similar_bugs(q, k=3, min_score=0.20)

        if not hits:
            print(f"  {YELLOW}No results above similarity threshold.{RESET}\n")
            continue

        for rank, hit in enumerate(hits, start=1):
            result_card(rank, hit)

    # ── Closing summary ────────────────────────────────────────────────────
    summary = f"""
{BOLD}Week 6–7 Deliverables{RESET}
  backend/app/services/embedding_service.py  — text → 384-dim vector
  backend/app/services/search_engine.py      — FAISS index build + ANN search
  scripts/build_search_index.py              — offline index builder
  API endpoint: POST /api/search/similar
  API endpoint: GET  /api/search/stats

{BOLD}How it works{RESET}
  1. All 177 GitHub issues are encoded into 384-dim vectors (all-MiniLM-L6-v2).
  2. Vectors are stored in a FAISS IndexFlatIP (cosine similarity).
  3. At query time, the error text is embedded and compared against the full corpus.
  4. Top-k issues with similarity ≥ threshold are returned with metadata.

This feeds directly into the Week 8 Recommendation Engine.
"""
    print(f"{CYAN}{BOLD}{'─' * 70}{RESET}")
    print(summary)


if __name__ == "__main__":
    run_demo()
