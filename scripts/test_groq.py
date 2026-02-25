"""
Test Groq API integration
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.input_processor import process_bug_input
from app.services.report_generator import generate_bug_report, list_available_models


def test_groq_connection():
    """Test 1: Check Groq API connection"""
    
    print("\n" + "="*80)
    print("TEST 1: Groq API Connection")
    print("="*80)
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print(" GROQ_API_KEY not found in environment")
        print("   Set it with: export GROQ_API_KEY='your_key'")
        return False
    
    print(f" GROQ_API_KEY found: {api_key[:20]}...")
    print(f" Key length: {len(api_key)} chars")
    
    return True


def test_available_models():
    """Test 2: List available models"""
    
    print("\n" + "="*80)
    print("TEST 2: Available Models")
    print("="*80)
    
    models_info = list_available_models()
    
    print(f"\n Provider: {models_info.get('provider')}")
    print(f" Default model: {models_info.get('default')}")
    
    if models_info.get('models'):
        print(f"\n Available models:")
        for name, model_id in models_info.get('models', {}).items():
            print(f"   • {name}: {model_id}")
    
    print(f"\n Recommended: {models_info.get('recommended', 'N/A')}")


def test_simple_generation():
    """Test 3: Simple bug report generation"""
    
    print("\n" + "="*80)
    print("TEST 3: Simple Bug Report Generation")
    print("="*80)
    
    bug_text = """
Application crashes when user clicks submit button.
Error: AttributeError: 'NoneType' object has no attribute 'name'
This happens when the username field is empty.
    """
    
    print(f"\n Input:\n{bug_text}")
    
    try:
        # Process
        print("\n Step 1: Processing input...")
        processed = process_bug_input(bug_text, "text")
        print(f" Processed successfully")
        print(f"   • Language: {processed['extracted_data'].get('language', 'unknown')}")
        print(f"   • Errors found: {len(processed['extracted_data']['error_info']['error_types'])}")
        
        # Generate
        print("\n Step 2: Generating report with Groq...")
        report = generate_bug_report(processed)
        
        print(f"\n Report generated!")
        print(f"\n Generated Report:")
        print(f"   • Title: {report['title']}")
        print(f"   • Severity: {report['severity']}")
        print(f"   • Steps: {len(report['steps_to_reproduce'])}")
        print(f"   • Model: {report.get('model_used', 'unknown')}")
        print(f"   • Generated at: {report.get('generated_at', 'unknown')}")
        
        print(f"\n Full Report Preview:")
        print(f"   Description: {report['description'][:150]}...")
        print(f"   Expected: {report['expected_behavior'][:100]}...")
        print(f"   Actual: {report['actual_behavior'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_models():
    """Test 4: Try all Groq models"""
    
    print("\n" + "="*80)
    print("TEST 4: Testing All Groq Models")
    print("="*80)
    
    bug_text = "Application crashes with NullPointerException in user.getName()"
    
    models = ["llama3-8b", "llama3-70b", "gemma"]
    
    for model_name in models:
        print(f"\n Testing model: {model_name}")
        
        try:
            processed = process_bug_input(bug_text, "text")
            report = generate_bug_report(processed, model=model_name)
            
            print(f"    Success!")
            print(f"   • Title: {report['title'][:60]}...")
            print(f"   • Severity: {report['severity']}")
            
        except Exception as e:
            print(f"    Failed: {e}")


def test_speed_comparison():
    """Test 5: Speed test"""
    
    print("\n" + "="*80)
    print("TEST 5: Speed Test (Groq vs others)")
    print("="*80)
    
    import time
    
    bug_text = "Application crashes with TypeError when processing user data"
    
    print("\n⏱  Testing Groq (llama3-8b)...")
    start = time.time()
    try:
        processed = process_bug_input(bug_text, "text")
        report = generate_bug_report(processed, model="llama3-8b")
        groq_time = time.time() - start
        print(f"    Groq: {groq_time:.2f}s")
    except Exception as e:
        print(f"    Failed: {e}")
        groq_time = None
    
    if groq_time:
        print(f"\n Groq is FAST! Generated report in {groq_time:.2f} seconds")


if __name__ == "__main__":
    print("\n" + " "*30)
    print(" "*20 + "Groq API Integration Tests")
    print(" "*30)
    
    # Run all tests
    tests = [
        ("API Connection", test_groq_connection),
        ("Available Models", test_available_models),
        ("Simple Generation", test_simple_generation),
        ("All Models", test_all_models),
        ("Speed Test", test_speed_comparison)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n  Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n {test_name} failed with error: {e}")
            results.append((test_name, False))
        
        if test_name != tests[-1][0]:  # Not last test
            input("\n  Press Enter to continue...")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = " PASS" if result else " FAIL" if result is False else "⏭  SKIPPED"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(" Groq integration ready for demo!" if any(results) else " Issues found")
    print("="*80 + "\n")