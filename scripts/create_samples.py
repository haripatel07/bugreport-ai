"""
Create curated sample test cases from collected data
Selects high-quality, diverse bug reports for testing and demos
"""

import json
from pathlib import Path
from typing import List, Dict, Any


# Configuration
INPUT_FILE = Path("data/raw/github_issues/combined_dataset.json")
OUTPUT_DIR = Path("data/samples")
OUTPUT_FILE = OUTPUT_DIR / "test_cases.json"
SIMPLE_OUTPUT = OUTPUT_DIR / "test_cases_simple.txt"
NUM_SAMPLES = 30


def load_all_issues() -> List[Dict[str, Any]]:
    """Load all collected issues from combined dataset or individual files"""
    
    all_issues = []
    
    # Try combined dataset first
    if INPUT_FILE.exists():
        print(f" Loading from combined dataset: {INPUT_FILE}")
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            all_issues = json.load(f)
        print(f"   [OK] Loaded {len(all_issues)} issues")
        return all_issues
    
    # Fallback: Load from individual repo files
    print(f" Combined dataset not found, loading individual repo files...")
    raw_dir = Path("data/raw/github_issues")
    
    if not raw_dir.exists():
        print(f"[ERROR] Error: {raw_dir} directory not found!")
        print(f"   Please run: python scripts/collect_data.py")
        return []
    
    json_files = list(raw_dir.glob("*_issues.json"))
    
    if not json_files:
        print(f"[ERROR] No issue files found in {raw_dir}")
        return []
    
    for json_file in json_files:
        if json_file.name == "combined_dataset.json":
            continue
        
        print(f"   Loading {json_file.name}...")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                issues = json.load(f)
                all_issues.extend(issues)
        except Exception as e:
            print(f"   WARNING:  Error loading {json_file.name}: {e}")
    
    print(f"   [OK] Loaded {len(all_issues)} total issues from {len(json_files)} files")
    return all_issues


def calculate_quality_score(issue: Dict[str, Any]) -> float:
    """
    Calculate quality score for an issue
    Higher score = better quality for testing/demos
    """
    
    score = 0.0
    
    # Body length (substantial description)
    body = issue.get('body', '')
    if body:
        word_count = len(body.split())
        if word_count > 50:
            score += 2.0
        if word_count > 100:
            score += 2.0
        if word_count > 200:
            score += 1.0
    else:
        return 0.0  # Skip issues with no body
    
    # Has been discussed (comments)
    comments = issue.get('comments_count', 0)
    if comments > 0:
        score += 1.0
    if comments > 3:
        score += 1.0
    
    # Closed/resolved (we can validate RCA)
    if issue.get('state') == 'closed':
        score += 2.0
    
    # Has labels (categorized)
    labels = issue.get('labels', [])
    if labels:
        score += 1.0
    
    # Technical content indicators
    technical_keywords = [
        'error', 'exception', 'crash', 'bug', 'fail',
        'traceback', 'stack', 'line', 'file',
        'function', 'method', 'class', 'module'
    ]
    
    body_lower = body.lower()
    keyword_matches = sum(1 for kw in technical_keywords if kw in body_lower)
    score += min(keyword_matches * 0.5, 3.0)  # Max 3 points
    
    # Has code blocks (technical detail)
    if '```' in body or '`' in body:
        score += 2.0
    
    # Title quality (not too short)
    title = issue.get('title', '')
    if len(title) > 20:
        score += 0.5
    
    return score


def select_diverse_samples(issues: List[Dict[str, Any]], count: int = 30) -> List[Dict[str, Any]]:
    """
    Select diverse, high-quality bug reports
    Ensures variety across repositories and bug types
    """
    
    print(f"\n Analyzing {len(issues)} issues for quality...")
    
    # Filter out issues without body
    issues_with_body = [
        issue for issue in issues 
        if issue.get('body') and len(issue.get('body', '')) > 50
    ]
    
    print(f"   [OK] {len(issues_with_body)} issues have substantial descriptions")
    
    # Calculate quality scores
    scored_issues = []
    for issue in issues_with_body:
        score = calculate_quality_score(issue)
        if score > 3.0:  # Minimum quality threshold
            scored_issues.append((score, issue))
    
    # Sort by score (highest first)
    scored_issues.sort(key=lambda x: x[0], reverse=True)
    
    print(f"   [OK] {len(scored_issues)} issues meet quality threshold")
    
    # Select diverse samples
    samples = []
    repos_used = {}
    max_per_repo = max(3, count // 5)  # At most ~20% from one repo
    
    for score, issue in scored_issues:
        repo = issue['repository']
        
        # Enforce diversity
        if repos_used.get(repo, 0) >= max_per_repo:
            continue
        
        samples.append(issue)
        repos_used[repo] = repos_used.get(repo, 0) + 1
        
        if len(samples) >= count:
            break
    
    # If we don't have enough diverse samples, fill remaining
    if len(samples) < count:
        remaining_needed = count - len(samples)
        remaining_issues = [issue for score, issue in scored_issues 
                          if issue not in samples]
        samples.extend(remaining_issues[:remaining_needed])
    
    print(f"\n Selected {len(samples)} diverse samples:")
    for repo, count in sorted(repos_used.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {repo}: {count} samples")
    
    return samples


def save_samples(samples: List[Dict[str, Any]]):
    """Save samples in multiple formats"""
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Save as JSON
    print(f"\n Saving samples...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    print(f"   [OK] Saved {len(samples)} samples to {OUTPUT_FILE}")
    
    # 2. Save human-readable version
    with open(SIMPLE_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(f"BugReport AI - Test Cases\n")
        f.write(f"{'='*80}\n")
        f.write(f"Total samples: {len(samples)}\n")
        f.write(f"Generated: {Path(__file__).name}\n")
        f.write(f"{'='*80}\n\n")
        
        for i, issue in enumerate(samples, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"TEST CASE {i}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Repository: {issue['repository']}\n")
            f.write(f"Issue Number: #{issue['number']}\n")
            f.write(f"Title: {issue['title']}\n")
            f.write(f"URL: {issue['url']}\n")
            f.write(f"State: {issue['state']}\n")
            f.write(f"Labels: {', '.join(issue['labels'][:5])}\n")
            f.write(f"Created: {issue['created_at'][:10]}\n")
            f.write(f"Comments: {issue.get('comments_count', 0)}\n")
            f.write(f"\nDescription (first 500 chars):\n")
            f.write(f"{'-'*80}\n")
            body = issue['body'][:500]
            f.write(f"{body}...\n")
            f.write(f"{'-'*80}\n")
    
    print(f"   [OK] Saved readable version to {SIMPLE_OUTPUT}")
    
    # 3. Create summary statistics
    summary_file = OUTPUT_DIR / "summary.json"
    
    # Calculate statistics
    repos = {}
    languages = []
    states = {}
    
    for issue in samples:
        repo = issue['repository']
        repos[repo] = repos.get(repo, 0) + 1
        
        state = issue['state']
        states[state] = states.get(state, 0) + 1
    
    summary = {
        "total_samples": len(samples),
        "repositories": repos,
        "states": states,
        "average_body_length": sum(len(s['body']) for s in samples) // len(samples),
        "average_comments": sum(s.get('comments_count', 0) for s in samples) // len(samples)
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"   [OK] Saved summary statistics to {summary_file}")


def display_statistics(samples: List[Dict[str, Any]]):
    """Display statistics about selected samples"""
    
    print(f"\n{'='*80}")
    print(f" SAMPLE STATISTICS")
    print(f"{'='*80}")
    
    # Repository distribution
    repos = {}
    for sample in samples:
        repo = sample['repository']
        repos[repo] = repos.get(repo, 0) + 1
    
    print(f"\n Samples by Repository:")
    for repo, count in sorted(repos.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(samples)) * 100
        bar = '█' * int(percentage / 2)
        print(f"   {repo:40} {count:2} {bar} {percentage:.1f}%")
    
    # State distribution
    states = {}
    for sample in samples:
        state = sample['state']
        states[state] = states.get(state, 0) + 1
    
    print(f"\n Samples by State:")
    for state, count in states.items():
        print(f"   {state.capitalize()}: {count}")
    
    # Quality metrics
    total_words = sum(len(s['body'].split()) for s in samples)
    avg_words = total_words // len(samples)
    
    total_comments = sum(s.get('comments_count', 0) for s in samples)
    avg_comments = total_comments / len(samples)
    
    print(f"\n Quality Metrics:")
    print(f"   Average description length: {avg_words} words")
    print(f"   Average comments per issue: {avg_comments:.1f}")
    print(f"   Total samples: {len(samples)}")
    
    # Technical indicators
    has_code = sum(1 for s in samples if '```' in s['body'] or '`' in s['body'])
    has_error = sum(1 for s in samples if 'error' in s['body'].lower())
    has_stack = sum(1 for s in samples if 'stack' in s['body'].lower() or 'traceback' in s['body'].lower())
    
    print(f"\n Technical Content:")
    print(f"   Issues with code blocks: {has_code} ({has_code/len(samples)*100:.1f}%)")
    print(f"   Issues mentioning errors: {has_error} ({has_error/len(samples)*100:.1f}%)")
    print(f"   Issues with stack traces: {has_stack} ({has_stack/len(samples)*100:.1f}%)")
    
    print(f"\n{'='*80}\n")


def preview_samples(samples: List[Dict[str, Any]], num_preview: int = 3):
    """Show preview of selected samples"""
    
    print(f"\n{'='*80}")
    print(f" PREVIEW: First {num_preview} Samples")
    print(f"{'='*80}\n")
    
    for i, sample in enumerate(samples[:num_preview], 1):
        print(f"Sample {i}:")
        print(f"  Repo: {sample['repository']}")
        print(f"  Title: {sample['title'][:60]}...")
        print(f"  URL: {sample['url']}")
        print(f"  Body length: {len(sample['body'])} chars")
        print(f"  Labels: {', '.join(sample['labels'][:3])}")
        print()


def main():
    """Main function"""
    
    print("\n" + "="*80)
    print(" "*20 + "BugReport AI - Sample Creator")
    print(" "*15 + "Creating curated test cases for demos")
    print("="*80 + "\n")
    
    # Step 1: Load all issues
    print("Step 1: Loading collected bug data...")
    all_issues = load_all_issues()
    
    if not all_issues:
        print("\n[ERROR] No issues found!")
        print("\nPlease collect data first:")
        print("   python scripts/collect_data.py")
        return
    
    print(f"[OK] Found {len(all_issues)} total issues\n")
    
    # Step 2: Select best samples
    print(f"Step 2: Selecting {NUM_SAMPLES} high-quality samples...")
    samples = select_diverse_samples(all_issues, count=NUM_SAMPLES)
    
    if not samples:
        print("\n[ERROR] No samples met quality criteria!")
        return
    
    # Step 3: Display statistics
    display_statistics(samples)
    
    # Step 4: Preview
    preview_samples(samples)
    
    # Step 5: Save
    print(f"Step 3: Saving samples...")
    save_samples(samples)
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"SAMPLE CREATION COMPLETE!")
    print(f"{'='*80}")
    print(f"\nOutput files created:")
    print(f"   - {OUTPUT_FILE}")
    print(f"   - {SIMPLE_OUTPUT}")
    print(f"   - {OUTPUT_DIR / 'summary.json'}")
    
    print(f"\nNext steps:")
    print(f"   1. Review samples: cat {SIMPLE_OUTPUT}")
    print(f"   2. Run demo: python scripts/demo_week3.py")
    print(f"   3. Test API: python scripts/demo_api_with_real_data.py")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()