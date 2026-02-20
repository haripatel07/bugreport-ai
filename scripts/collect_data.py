"""
Data Collection Script for BugReport AI
Collects bug reports from multiple sources with better label handling
"""

import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTPUT_DIR = Path("data/raw/github_issues")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Repository list with specific label configurations
REPOSITORIES = [
    {"repo": "microsoft/vscode", "labels": ["bug"], "max_issues": 30},
    {"repo": "tensorflow/tensorflow", "labels": ["type:bug", "bug"], "max_issues": 30},
    {"repo": "facebook/react", "labels": ["Type: Bug", "bug"], "max_issues": 30},
    {"repo": "nodejs/node", "labels": ["bug"], "max_issues": 30},
    {"repo": "python/cpython", "labels": ["type-bug", "bug"], "max_issues": 30},
    {"repo": "pandas-dev/pandas", "labels": ["Bug"], "max_issues": 20},
    {"repo": "scikit-learn/scikit-learn", "labels": ["Bug"], "max_issues": 20},
    {"repo": "django/django", "labels": ["type: Bug"], "max_issues": 20},
    {"repo": "kubernetes/kubernetes", "labels": ["kind/bug"], "max_issues": 20},
    {"repo": "rust-lang/rust", "labels": ["C-bug"], "max_issues": 20},
]

def fetch_issues_flexible(repo, labels=None, state="closed", max_issues=20):
    """
    Fetch issues with flexible label matching
    Tries multiple label variants if first attempt fails
    """
    
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    all_issues = []
    
    # Try each label variant
    label_variants = labels if labels else ["bug"]
    
    for label in label_variants:
        params = {
            "state": state,
            "labels": label,
            "per_page": min(max_issues, 100),
            "sort": "created",
            "direction": "desc"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Check rate limit
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            print(f"   Rate limit remaining: {remaining}")
            
            if response.status_code == 200:
                issues = response.json()
                if issues:
                    print(f"   ✓ Found {len(issues)} issues with label '{label}'")
                    all_issues.extend(issues)
                    break  # Found issues, no need to try other labels
                else:
                    print(f"   ✗ No issues with label '{label}', trying next...")
            elif response.status_code == 403:
                print(f"   Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
            else:
                print(f"   ✗ Error {response.status_code} for label '{label}'")
                
        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {e}")
            continue
        
        time.sleep(1)  
    
    # If no labeled issues found, try without label filter (get any closed issues)
    if not all_issues:
        print(f"   → Trying without label filter...")
        params = {
            "state": state,
            "per_page": min(max_issues, 50),
            "sort": "created",
            "direction": "desc"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                issues = response.json()
                # Filter for bug-related keywords in title
                bug_keywords = ['bug', 'error', 'crash', 'fail', 'broken', 'issue', 'fix']
                all_issues = [
                    issue for issue in issues 
                    if any(keyword in issue['title'].lower() for keyword in bug_keywords)
                    and not issue.get('pull_request')
                ]
                print(f"   Found {len(all_issues)} bug-related issues (keyword filtered)")
        except Exception as e:
            print(f"   Fallback failed: {e}")
    
    return all_issues[:max_issues]

def save_issues(repo, issues):
    """Save issues to JSON file with better formatting"""
    
    repo_name = repo.replace("/", "_")
    filename = OUTPUT_DIR / f"{repo_name}_issues.json"
    
    # Extract relevant fields
    cleaned_issues = []
    for issue in issues:
        if issue.get("pull_request"):  # Skip pull requests
            continue
        
        cleaned_issue = {
            "id": issue["id"],
            "number": issue["number"],
            "title": issue["title"],
            "body": issue.get("body", ""),
            "state": issue["state"],
            "labels": [label["name"] for label in issue.get("labels", [])],
            "created_at": issue["created_at"],
            "closed_at": issue.get("closed_at"),
            "updated_at": issue.get("updated_at"),
            "comments_count": issue.get("comments", 0),
            "url": issue["html_url"],
            "repository": repo,
            "user": issue.get("user", {}).get("login", "unknown")
        }
        cleaned_issues.append(cleaned_issue)
    
    if cleaned_issues:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(cleaned_issues, f, indent=2, ensure_ascii=False)
        
        print(f"   Saved {len(cleaned_issues)} issues to {filename.name}")
    
    return len(cleaned_issues)

def create_combined_dataset():
    """Combine all collected issues into a single file"""
    
    all_issues = []
    
    for json_file in OUTPUT_DIR.glob("*_issues.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            issues = json.load(f)
            all_issues.extend(issues)
    
    if all_issues:
        combined_file = OUTPUT_DIR / "combined_dataset.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_issues, f, indent=2, ensure_ascii=False)
        
        print(f"\nCombined dataset created: {len(all_issues)} total issues")
        print(f"   Location: {combined_file}")
        
        # Create summary statistics
        repos = {}
        for issue in all_issues:
            repo = issue['repository']
            repos[repo] = repos.get(repo, 0) + 1
        
        print(f"\nIssues by repository:")
        for repo, count in sorted(repos.items(), key=lambda x: x[1], reverse=True):
            print(f"   {repo}: {count}")

def main():
    """Main data collection function"""
    
    print("Starting enhanced bug data collection...\n")
    
    if not GITHUB_TOKEN:
        print("Warning: No GITHUB_TOKEN found. Rate limits will be lower (60/hour vs 5000/hour)")
        print("   Set token with: export GITHUB_TOKEN='your_token'\n")
    
    total_issues = 0
    successful_repos = 0
    
    for repo_config in REPOSITORIES:
        repo = repo_config["repo"]
        labels = repo_config.get("labels", ["bug"])
        max_issues = repo_config.get("max_issues", 20)
        
        print(f"Fetching from {repo}...")
        issues = fetch_issues_flexible(repo, labels=labels, max_issues=max_issues)
        
        if issues:
            count = save_issues(repo, issues)
            total_issues += count
            successful_repos += 1
        else:
            print(f"   No issues collected from {repo}")
        
        print()  # Blank line between repos
        time.sleep(2)  # Rate limiting - be nice to GitHub
    
    print(f"\n{'='*60}")
    print(f"Collection complete!")
    print(f"   Total issues: {total_issues}")
    print(f"   Successful repos: {successful_repos}/{len(REPOSITORIES)}")
    print(f"   Data directory: {OUTPUT_DIR}")
    print(f"{'='*60}\n")
    
    # Create combined dataset
    if total_issues > 0:
        create_combined_dataset()
    
    # Create collection summary
    summary = {
        "collection_date": datetime.now().isoformat(),
        "total_issues": total_issues,
        "successful_repositories": successful_repos,
        "total_repositories": len(REPOSITORIES),
        "repositories": [r["repo"] for r in REPOSITORIES],
        "output_directory": str(OUTPUT_DIR),
        "github_token_used": bool(GITHUB_TOKEN)
    }
    
    with open(OUTPUT_DIR / "collection_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {OUTPUT_DIR}/collection_summary.json")
    

if __name__ == "__main__":
    main()