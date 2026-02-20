"""
Data Collection Script for BugReport AI
Collects bug reports from GitHub Issues
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Add your token
OUTPUT_DIR = Path("data/raw/github_issues")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Target repositories with good bug reports
REPOSITORIES = [
    "tensorflow/tensorflow",
    "microsoft/vscode",
    "facebook/react",
    "nodejs/node",
    "python/cpython"
]

def fetch_issues(repo, state="closed", labels="bug", max_issues=20):
    """Fetch issues from a GitHub repository"""
    
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {}
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    params = {
        "state": state,
        "labels": labels,
        "per_page": max_issues,
        "sort": "created",
        "direction": "desc"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {repo}: {e}")
        return []

def save_issues(repo, issues):
    """Save issues to JSON file"""
    
    repo_name = repo.replace("/", "_")
    filename = OUTPUT_DIR / f"{repo_name}_issues.json"
    
    # Extract relevant fields
    cleaned_issues = []
    for issue in issues:
        if issue.get("pull_request"):  # Skip pull requests
            continue
            
        cleaned_issues.append({
            "id": issue["id"],
            "number": issue["number"],
            "title": issue["title"],
            "body": issue["body"],
            "state": issue["state"],
            "labels": [label["name"] for label in issue["labels"]],
            "created_at": issue["created_at"],
            "closed_at": issue.get("closed_at"),
            "url": issue["html_url"],
            "repository": repo
        })
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cleaned_issues, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(cleaned_issues)} issues from {repo}")
    return len(cleaned_issues)

def main():
    """Main data collection function"""
    
    print("Starting bug data collection...\n")
    
    total_issues = 0
    
    for repo in REPOSITORIES:
        print(f"Fetching issues from {repo}...")
        issues = fetch_issues(repo, max_issues=20)
        count = save_issues(repo, issues)
        total_issues += count
        print()
    
    print(f"Collection complete! Total issues collected: {total_issues}")
    print(f"Data saved in: {OUTPUT_DIR}")
    
    # Create summary file
    summary = {
        "collection_date": datetime.now().isoformat(),
        "total_issues": total_issues,
        "repositories": REPOSITORIES,
        "output_directory": str(OUTPUT_DIR)
    }
    
    with open(OUTPUT_DIR / "collection_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()