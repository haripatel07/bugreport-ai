#!/usr/bin/env python3
"""
Build the semantic search index from collected GitHub issues.

Run from the project root:
    python scripts/build_search_index.py

Or with extra flags:
    python scripts/build_search_index.py --data-file data/raw/github_issues/combined_dataset.json
    python scripts/build_search_index.py --quiet
"""

import argparse
import json
import sys
from pathlib import Path

# Allow importing app/ without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Build FAISS search index from GitHub issues")
    parser.add_argument(
        "--data-file",
        default=str(PROJECT_ROOT / "data" / "raw" / "github_issues" / "combined_dataset.json"),
        help="Path to the combined GitHub issues JSON file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress bar",
    )
    args = parser.parse_args()

    data_path = Path(args.data_file)
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)

    print(f"Loading issues from {data_path}…")
    with open(data_path) as f:
        issues = json.load(f)

    print(f"Found {len(issues)} issues.")

    # Validate structure (best-effort)
    required_keys = {"title"}
    valid = [i for i in issues if required_keys.issubset(i.keys())]
    if len(valid) < len(issues):
        print(f"[WARN] {len(issues) - len(valid)} issues skipped (missing 'title' field)")
    issues = valid

    print("Encoding issues and building FAISS index…")
    print("(First run downloads the model — ~22 MB, takes a few seconds)")

    from app.services.search_engine import build_index

    stats = build_index(issues, show_progress=not args.quiet)

    print("\n✅  Index built successfully!")
    print(f"   Issues indexed : {stats['total_indexed']}")
    print(f"   Embedding dim  : {stats['embedding_dim']}")
    print(f"   Build time     : {stats['build_time_seconds']}s")
    print(f"   Index size     : {stats['index_size_kb']} KB")
    print(f"\nIndex stored in: {PROJECT_ROOT / 'data' / 'processed' / 'search_index'}/")


if __name__ == "__main__":
    main()
