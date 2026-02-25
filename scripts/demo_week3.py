#!/usr/bin/env python3
"""
BugReport AI - Week 3 Demo Script
Demonstrates the core features: input processing + LLM report generation
"""

import sys
import os
import json

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.input_processor import process_bug_input
from app.services.report_generator import generate_bug_report, list_available_models

# ──────────────────────────────────────────────────────────────────────────────
# Sample bug inputs
# ──────────────────────────────────────────────────────────────────────────────

SAMPLE_PYTHON_TRACE = """
Traceback (most recent call last):
  File "app.py", line 42, in process_user
    name = user.name.upper()
AttributeError: 'NoneType' object has no attribute 'name'
"""

SAMPLE_JS_ERROR = """
TypeError: Cannot read property 'name' of undefined
    at processUser (app.js:42:15)
    at handleSubmit (form.js:18:5)
"""

SAMPLE_TEXT_BUG = (
    "Login button does not respond when the password field is left empty. "
    "The form should show a validation error but instead nothing happens."
)

SAMPLE_LOG = """
2025-02-25 10:30:00 INFO  Starting application
2025-02-25 10:30:05 ERROR Database connection failed: timeout after 30s
2025-02-25 10:30:06 CRITICAL Application shutdown due to fatal error
"""


def separator(title: str = "") -> None:
    line = "─" * 60
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(f"{line}")
    else:
        print(f"\n{line}\n")


def demo_input_processing() -> None:
    """Demo 1: Input processing for various bug formats"""
    separator("DEMO 1 — Input Processing")

    cases = [
        ("Python Stack Trace", SAMPLE_PYTHON_TRACE, "stack_trace"),
        ("JavaScript Error",   SAMPLE_JS_ERROR,     "stack_trace"),
        ("Plain Text Bug",     SAMPLE_TEXT_BUG,     "text"),
        ("Application Log",   SAMPLE_LOG,           "log"),
    ]

    for title, raw, input_type in cases:
        print(f"\n▶ {title}")
        result = process_bug_input(raw, input_type)
        extracted = result["extracted_data"]

        # Show key extractions
        lang = extracted.get("language") or "unknown"
        print(f"  Language   : {lang}")

        error_info = extracted.get("error_info", {})
        if error_info.get("error_types"):
            print(f"  Error types: {', '.join(error_info['error_types'])}")

        if extracted.get("frames"):
            frame = extracted["frames"][0]
            print(f"  Top frame  : {frame.get('file')}:{frame.get('line')}")

        if extracted.get("error_count") is not None:
            print(f"  Log errors : {extracted['error_count']}")

        files = extracted.get("files", [])
        if files:
            print(f"  Files found: {', '.join(f['path'] for f in files[:3])}")

    print("\nInput processing demo complete.")


def demo_report_generation() -> None:
    """Demo 2: LLM-based bug report generation"""
    separator("DEMO 2 — Bug Report Generation")

    # Show available models
    models_info = list_available_models()
    print(f"\nLLM provider : {models_info['provider']}")

    # Process the Python traceback
    print("\nProcessing Python stack trace …")
    processed = process_bug_input(SAMPLE_PYTHON_TRACE, "stack_trace")

    print("Generating bug report …")
    report = generate_bug_report(processed)

    # Pretty-print key fields
    print(f"\n  Title    : {report.get('title', 'N/A')}")
    print(f"  Severity : {report.get('severity', 'N/A')}")
    print(f"  Model    : {report.get('model_used', 'N/A')}")

    steps = report.get("steps_to_reproduce", [])
    if steps:
        print("\n  Steps to Reproduce:")
        for i, step in enumerate(steps, 1):
            print(f"    {i}. {step}")

    print(f"\n  Expected : {report.get('expected_behavior', 'N/A')}")
    print(f"  Actual   : {report.get('actual_behavior', 'N/A')}")

    components = report.get("affected_components", [])
    if components:
        print(f"\n  Affected components: {', '.join(str(c) for c in components)}")

    print("\nReport generation demo complete.")


def demo_json_output() -> None:
    """Demo 3: Full pipeline → JSON output"""
    separator("DEMO 3 — Full Pipeline (JSON output)")

    processed = process_bug_input(SAMPLE_TEXT_BUG, "text")
    report = generate_bug_report(processed)

    # Remove verbose fields for display
    display = {k: v for k, v in report.items()
               if k not in ("generated_at", "model_used", "source_data", "note")}

    print()
    print(json.dumps(display, indent=2))
    print("\nFull pipeline demo complete.")


def main() -> None:
    separator("BugReport AI — Week 3 Demo")
    print("Features: Data Collection ✓ | Input Processing ✓ | LLM Reports ✓")

    try:
        demo_input_processing()
        demo_report_generation()
        demo_json_output()
    except Exception as exc:
        print(f"\nDemo failed: {exc}")
        raise

    separator()
    print("All demos passed. Project is ~30% complete.")
    print("Next steps: root-cause analysis, web dashboard, deployment.\n")


if __name__ == "__main__":
    main()
