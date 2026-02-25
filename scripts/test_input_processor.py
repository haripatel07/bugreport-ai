"""
Test input processor with real bug data from our dataset
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.input_processor import process_bug_input


def load_sample_bugs(num_samples=10):
    """Load sample bugs from our collected data"""
    samples_file = Path("data/samples/test_cases.json")
    
    if not samples_file.exists():
        print("Sample file not found. Run create_samples.py first.")
        return []
    
    with open(samples_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data[:num_samples]


def test_processor_on_samples():
    """Test input processor on real bugs"""
    
    print("Testing Input Processor on Real Bug Data\n")
    print("="*80)
    
    samples = load_sample_bugs(num_samples=5)
    
    if not samples:
        return
    
    success_count = 0
    total = len(samples)
    
    for i, bug in enumerate(samples, 1):
        print(f"\nTEST CASE {i}/{total}")
        print(f"Title: {bug['title'][:60]}...")
        print(f"Repository: {bug['repository']}")
        
        try:
            # Process the bug description
            result = process_bug_input(bug['body'] or bug['title'], "text")
            
            extracted = result['extracted_data']
            
            print(f"\nProcessing successful!")
            print(f"   • Language detected: {extracted.get('language', 'unknown')}")
            print(f"   • Error types found: {len(extracted['error_info']['error_types'])}")
            print(f"   • Files referenced: {len(extracted['files'])}")
            print(f"   • Word count: {extracted.get('word_count', 0)}")
            
            if extracted['error_info']['error_types']:
                print(f"   • Errors: {', '.join(extracted['error_info']['error_types'][:3])}")
            
            success_count += 1
            
        except Exception as e:
            print(f"\nProcessing failed: {str(e)}")
        
        print("-" * 80)
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {success_count}/{total} tests passed ({success_count/total*100:.1f}%)")
    print(f"{'='*80}\n")


def test_specific_cases():
    """Test specific error patterns"""
    
    print("\nTesting Specific Error Patterns\n")
    
    test_cases = [
        {
            "name": "Python NullPointer",
            "input": """
Traceback (most recent call last):
  File "app.py", line 42, in process_user
    name = user.name.upper()
AttributeError: 'NoneType' object has no attribute 'name'
            """,
            "type": "stack_trace"
        },
        {
            "name": "JavaScript TypeError",
            "input": """
TypeError: Cannot read property 'name' of undefined
    at processUser (app.js:42:15)
    at handleSubmit (form.js:18:5)
            """,
            "type": "stack_trace"
        },
        {
            "name": "Application Log",
            "input": """
2025-02-25 10:30:00 INFO Starting application
2025-02-25 10:30:05 ERROR Database connection failed: Connection refused
2025-02-25 10:30:06 CRITICAL Application shutdown due to fatal error
            """,
            "type": "log"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test['name']}")
        
        try:
            result = process_bug_input(test['input'], test['type'])
            extracted = result['extracted_data']
            
            print(f"   Detected language: {extracted.get('language', 'N/A')}")
            print(f"   Error types: {extracted['error_info']['error_types']}")
            
            if test['type'] == 'log':
                print(f"   Error lines: {extracted['error_count']}")
            elif 'frames' in extracted:
                print(f"   Stack frames: {len(extracted['frames'])}")
            
        except Exception as e:
            print(f"    Failed: {e}")
        
        print()


if __name__ == "__main__":
    test_processor_on_samples()
    test_specific_cases()