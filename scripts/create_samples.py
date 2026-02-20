"""
Create curated sample test cases from collected data
"""

import json
from pathlib import Path

INPUT_FILE = Path("data/raw/github_issues/combined_dataset.json")
OUTPUT_DIR = Path("data/samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_issues():
    """Load all collected issues"""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def select_diverse_samples(issues, count=30):
    """
    Select diverse bug reports for testing
    Criteria: Good description, closed state, variety of repos
    """
    
    # Filter quality issues
    quality_issues = [
        issue for issue in issues
        if issue.get('body') 
        and len(issue.get('body', '')) > 100  # Has substantial description
        and issue['state'] == 'closed'  # Was resolved
        and issue.get('comments_count', 0) > 0  # Has discussion
    ]
    
    # Sort by quality indicators
    quality_issues.sort(
        key=lambda x: (
            len(x.get('body', '')),  # Longer descriptions
            x.get('comments_count', 0)  # More discussion
        ),
        reverse=True
    )
    
    # Select diverse samples (different repos)
    samples = []
    repos_used = set()
    
    for issue in quality_issues:
        repo = issue['repository']
        
        # Try to get variety
        if repo not in repos_used or len(samples) > count * 0.7:
            samples.append(issue)
            repos_used.add(repo)
        
        if len(samples) >= count:
            break
    
    return samples

def save_samples(samples):
    """Save samples in different formats"""
    
    # Full samples JSON
    with open(OUTPUT_DIR / "test_cases.json", 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(samples)} test cases to {OUTPUT_DIR / 'test_cases.json'}")
    
    # Simple format for manual review
    with open(OUTPUT_DIR / "test_cases_simple.txt", 'w', encoding='utf-8') as f:
        for i, issue in enumerate(samples, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"TEST CASE {i}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Repository: {issue['repository']}\n")
            f.write(f"Issue #: {issue['number']}\n")
            f.write(f"Title: {issue['title']}\n")
            f.write(f"URL: {issue['url']}\n")
            f.write(f"\nDescription:\n{issue['body'][:500]}...\n")
    
    print(f"Saved readable version to {OUTPUT_DIR / 'test_cases_simple.txt'}")
    
    # Category breakdown
    categories = {}
    for issue in samples:
        repo = issue['repository']
        categories[repo] = categories.get(repo, 0) + 1
    
    print(f"\nSample distribution:")
    for repo, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {repo}: {count}")

def main():
    print("Creating curated sample test cases...\n")
    
    issues = load_issues()
    print(f" Loaded {len(issues)} total issues")
    
    samples = select_diverse_samples(issues, count=30)
    print(f"Selected {len(samples)} high-quality samples\n")
    
    save_samples(samples)
    
    print(f"\n{'='*80}")
    print("Sample creation complete!")
    print(f"   Review samples at: {OUTPUT_DIR}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()