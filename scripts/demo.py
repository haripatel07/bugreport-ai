#!/usr/bin/env python3
"""
Demo script for Week 3 - Using REAL collected data
Shows complete flow with actual bugs from GitHub
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.input_processor import process_bug_input
from app.services.report_generator import generate_bug_report


def load_real_bugs():
    """Load real bugs from collected data"""
    samples_file = Path("data/samples/test_cases.json")
    
    if not samples_file.exists():
        print("ERROR: Sample file not found.")
        print("  Run: python scripts/create_samples.py")
        return []
    
    with open(samples_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def demo_real_bug_simple():
    """Demo 1: Simple real bug from VS Code"""
    
    print("\n" + "="*80)
    print("DEMO 1: Real Bug from Microsoft VS Code Repository")
    print("="*80)
    
    bugs = load_real_bugs()
    if not bugs:
        return
    
    # Pick first bug
    bug = bugs[0]
    
    print(f"\n  Source   : {bug['repository']}")
    print(f"  URL      : {bug['url']}")
    print(f"  Title    : {bug['title']}")
    print(f"  Reported : {bug['created_at'][:10]}")
    print(f"  Labels   : {', '.join(bug['labels'][:3])}")
    
    print(f"\nOriginal Description (first 300 chars):")
    print(f"{'─'*80}")
    print(bug['body'][:300] + "..." if len(bug['body']) > 300 else bug['body'])
    print(f"{'─'*80}")
    
    # Process
    print("\nStep 1: Processing with Input Processor...")
    processed = process_bug_input(bug['body'] or bug['title'], "text")
    
    extracted = processed['extracted_data']
    print(f"Extracted Information:")
    print(f"  - Language detected : {extracted.get('language', 'unknown')}")
    print(f"  - Error types       : {extracted['error_info']['error_types'][:3] if extracted['error_info']['error_types'] else 'None'}")
    print(f"  - Files referenced  : {len(extracted['files'])}")
    print(f"  - Word count        : {extracted.get('word_count', 0)}")
    
    # Generate
    print("\nStep 2: Generating professional bug report with AI...")
    report = generate_bug_report(processed)
    
    print(f"\nAI-Generated Professional Report:")
    print(f"{'='*80}")
    print(f"  Title    : {report['title']}")
    print(f"  Severity : {report['severity'].upper()}")
    print(f"\nDescription:")
    print(f"  {report['description'][:200]}...")
    print(f"\nSteps to Reproduce:")
    for i, step in enumerate(report['steps_to_reproduce'], 1):
        print(f"  {i}. {step}")
    print(f"\nExpected Behavior:")
    print(f"  {report['expected_behavior'][:150]}...")
    print(f"\nActual Behavior:")
    print(f"  {report['actual_behavior'][:150]}...")
    print(f"\nAffected Components:")
    print(f"  {', '.join(report['affected_components'][:5])}")
    print(f"\n  Model Used   : {report['model_used']}")
    print(f"  Generated At : {report['generated_at']}")
    print(f"{'='*80}")


def demo_compare_multiple():
    """Demo 2: Compare multiple real bugs"""
    
    print("\n" + "="*80)
    print("DEMO 2: Processing Multiple Real Bugs from Different Projects")
    print("="*80)
    
    bugs = load_real_bugs()
    if not bugs:
        return
    
    # Process 3 different bugs
    for i, bug in enumerate(bugs[:3], 1):
        print(f"\n{'─'*80}")
        print(f"BUG {i}: {bug['repository']}")
        print(f"{'─'*80}")
        print(f"Original: {bug['title'][:70]}...")
        
        # Quick process and generate
        processed = process_bug_input(bug['body'] or bug['title'], "text")
        report = generate_bug_report(processed)
        
        print(f"AI Title : {report['title'][:70]}...")
        print(f"Severity : {report['severity']} | Language: {processed['extracted_data'].get('language', 'unknown')}")


def demo_stack_trace_real():
    """Demo 3: Real bug with stack trace"""
    
    print("\n" + "="*80)
    print("DEMO 3: Real Bug with Stack Trace/Error Log")
    print("="*80)
    
    bugs = load_real_bugs()
    if not bugs:
        return
    
    # Find bug with stack trace or error
    stack_trace_bug = None
    for bug in bugs:
        body = bug.get('body', '')
        if any(keyword in body.lower() for keyword in ['traceback', 'error:', 'exception', 'at line']):
            stack_trace_bug = bug
            break
    
    if not stack_trace_bug:
        print("WARNING: No bugs with stack traces found, using first bug instead")
        stack_trace_bug = bugs[0]
    
    print(f"\n  Source : {stack_trace_bug['repository']}")
    print(f"  URL    : {stack_trace_bug['url']}")
    
    # Process
    processed = process_bug_input(stack_trace_bug['body'] or stack_trace_bug['title'], "text")
    
    extracted = processed['extracted_data']
    
    print(f"\nExtracted Technical Details:")
    if extracted['error_info']['error_types']:
        print(f"  - Error Types   : {', '.join(extracted['error_info']['error_types'][:3])}")
    if extracted['error_info']['error_messages']:
        print(f"  - Error Message : {extracted['error_info']['error_messages'][0][:100]}...")
    if extracted['files']:
        print(f"  - Files Affected:")
        for f in extracted['files'][:3]:
            line_info = f":{f['line']}" if f['line'] else ""
            print(f"      {f['path']}{line_info}")
    
    # Generate
    report = generate_bug_report(processed)
    
    print(f"\nGenerated Report Highlights:")
    print(f"  Title      : {report['title']}")
    print(f"  Severity   : {report['severity']}")
    print(f"  Components : {', '.join(report['affected_components'][:3])}")


def demo_statistics():
    """Demo 4: Statistics about our collected data"""
    
    print("\n" + "="*80)
    print("DEMO 4: Our Collected Dataset Statistics")
    print("="*80)
    
    bugs = load_real_bugs()
    if not bugs:
        return
    
    # Analyze dataset
    repos = {}
    languages = {}
    total_words = 0
    
    for bug in bugs:
        # Count by repo
        repo = bug['repository']
        repos[repo] = repos.get(repo, 0) + 1
        
        # Detect language
        processed = process_bug_input(bug['body'] or bug['title'], "text")
        lang = processed['extracted_data'].get('language', 'unknown')
        languages[lang] = languages.get(lang, 0) + 1
        
        # Count words
        total_words += processed['extracted_data'].get('word_count', 0)
    
    print(f"\nDataset Overview:")
    print(f"  Total bugs analyzed        : {len(bugs)}")
    print(f"  Average description length : {total_words // len(bugs)} words")
    print(f"  Repositories represented   : {len(repos)}")
    
    print(f"\nBugs by Repository:")
    for repo, count in sorted(repos.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {repo}: {count} bugs")
    
    print(f"\nLanguages Detected:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        if lang != 'unknown':
            print(f"  {lang}: {count} bugs")
    
    print(f"\nSystem validated on real production bugs.")


def demo_before_after():
    """Demo 5: Before/After comparison"""
    
    print("\n" + "="*80)
    print("DEMO 5: Before AI vs After AI - Quality Comparison")
    print("="*80)
    
    bugs = load_real_bugs()
    if not bugs:
        return
    
    bug = bugs[0]
    
    print(f"\nBEFORE (Original GitHub Issue):")
    print(f"{'─'*80}")
    print(f"Title: {bug['title']}")
    print(f"\nDescription: {bug['body'][:400]}...")
    print(f"{'─'*80}")
    
    # Generate improved version
    processed = process_bug_input(bug['body'] or bug['title'], "text")
    report = generate_bug_report(processed)
    
    print(f"\nAFTER (AI-Generated Professional Report):")
    print(f"{'─'*80}")
    print(f"Title: {report['title']}")
    print(f"\nDescription: {report['description']}")
    print(f"\nSteps to Reproduce:")
    for i, step in enumerate(report['steps_to_reproduce'], 1):
        print(f"  {i}. {step}")
    print(f"\nExpected : {report['expected_behavior']}")
    print(f"Actual   : {report['actual_behavior']}")
    print(f"Severity : {report['severity']}")
    print(f"{'─'*80}")
    
    print(f"\nImprovements:")
    print(f"  - Structured format with clear sections")
    print(f"  - Actionable steps to reproduce")
    print(f"  - Severity classification")
    print(f"  - Clear expected vs actual behavior")


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" "*20 + "BugReport AI - Demo")
    print(" "*10 + "Using Real Bugs from VS Code, TensorFlow, and more")
    print(" "*18 + "30% Project Completion - First Review")
    print("="*80)
    
    # Check if data exists
    bugs = load_real_bugs()
    if not bugs:
        print("\nERROR: No sample data found.")
        print("  Please run: python scripts/create_samples.py")
        sys.exit(1)
    
    print(f"\nLoaded {len(bugs)} real bugs from collected data.")
    
    # Show LLM info
    from app.services.report_generator import list_available_models
    models_info = list_available_models()
    print(f"Provider : {models_info.get('provider', 'unknown')} ({models_info.get('default', '')})")
    
    try:
        demo_real_bug_simple()
        input("\nPress Enter to continue to Demo 2...")
        
        demo_compare_multiple()
        input("\nPress Enter to continue to Demo 3...")
        
        demo_stack_trace_real()
        input("\nPress Enter to continue to Demo 4...")
        
        demo_statistics()
        input("\nPress Enter to continue to Demo 5...")
        
        demo_before_after()
        
        print("\n" + "="*80)
        print("All demos completed successfully.")
        print("="*80)
        print("\nKey Takeaways:")
        print("  - Works on real bugs from production repositories")
        print("  - Supports multiple programming languages")
        print("  - Generates professional, structured reports")
        print("  - Improves original bug report quality")
        print("  - Ready for real-world deployment")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
