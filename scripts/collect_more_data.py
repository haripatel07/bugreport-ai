"""
Targeted top-up data collection for BugReport AI.

Collects from repos NOT yet in the dataset to push total above 200.
Merges results into the existing combined_dataset.json.
"""

import os
import json
import requests
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OUTPUT_DIR = Path("data/raw/github_issues")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ADDITIONAL_REPOSITORIES = [
    {"repo": "django/django",       "labels": ["type: Bug", "Bug"],   "max_issues": 25},
    {"repo": "golang/go",           "labels": ["NeedsFix", "bug"],     "max_issues": 25},
    {"repo": "vuejs/core",          "labels": ["bug"],                 "max_issues": 20},
    {"repo": "docker/compose",      "labels": ["kind/bug", "bug"],     "max_issues": 15},
]


def fetch_issues(repo: str, labels: list[str], max_issues: int) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    for label in labels:
        params = {
            "state": "closed",
            "labels": label,
            "per_page": min(max_issues, 100),
            "sort": "created",
            "direction": "desc",
        }
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            remaining = response.headers.get("X-RateLimit-Remaining", "?")
            print(f"   Rate limit remaining: {remaining}")

            if response.status_code == 200:
                issues = [i for i in response.json() if not i.get("pull_request")]
                if issues:
                    print(f"   ✓ {len(issues)} issues via label '{label}'")
                    return issues[:max_issues]
                print(f"   ✗ No issues for label '{label}', trying next…")
            elif response.status_code == 403:
                print("   Rate limit hit — waiting 60 s…")
                time.sleep(60)
            else:
                print(f"   ✗ HTTP {response.status_code}")
        except requests.exceptions.RequestException as exc:
            print(f"   Request error: {exc}")
        time.sleep(1)

    # Keyword fallback — no label filter
    print(f"   → Keyword fallback (no label filter)…")
    try:
        resp = requests.get(
            url, headers=headers,
            params={"state": "closed", "per_page": min(max_issues * 2, 100),
                    "sort": "created", "direction": "desc"},
            timeout=15,
        )
        if resp.status_code == 200:
            kw = {"bug", "error", "crash", "fail", "broken", "fix", "issue"}
            hits = [
                i for i in resp.json()
                if not i.get("pull_request")
                and any(w in i["title"].lower() for w in kw)
            ]
            print(f"   Found {len(hits)} issues via keyword filter")
            return hits[:max_issues]
    except Exception as exc:
        print(f"   Fallback error: {exc}")

    return []


def clean_issue(issue: dict, repo: str) -> dict:
    return {
        "id": issue["id"],
        "number": issue["number"],
        "title": issue["title"],
        "body": issue.get("body", ""),
        "state": issue["state"],
        "labels": [lb["name"] for lb in issue.get("labels", [])],
        "created_at": issue["created_at"],
        "closed_at": issue.get("closed_at"),
        "updated_at": issue.get("updated_at"),
        "comments_count": issue.get("comments", 0),
        "url": issue["html_url"],
        "repository": repo,
        "user": issue.get("user", {}).get("login", "unknown"),
    }


def save_repo_file(repo: str, issues: list[dict]) -> int:
    name = repo.replace("/", "_")
    path = OUTPUT_DIR / f"{name}_issues.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)
    print(f"   Saved {len(issues)} issues → {path.name}")
    return len(issues)


def rebuild_combined():
    """Re-read every *_issues.json and write combined_dataset.json."""
    all_issues: list[dict] = []
    for fp in sorted(OUTPUT_DIR.glob("*_issues.json")):
        with open(fp, encoding="utf-8") as f:
            all_issues.extend(json.load(f))

    combined = OUTPUT_DIR / "combined_dataset.json"
    with open(combined, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False)

    by_repo: dict[str, int] = {}
    for i in all_issues:
        by_repo[i["repository"]] = by_repo.get(i["repository"], 0) + 1

    print(f"\n{'='*60}")
    print(f"Combined dataset: {len(all_issues)} total issues across {len(by_repo)} repos")
    for repo, cnt in sorted(by_repo.items(), key=lambda x: -x[1]):
        print(f"   {repo}: {cnt}")
    print(f"{'='*60}")
    return len(all_issues)


def main():
    if not GITHUB_TOKEN:
        print("⚠  No GITHUB_TOKEN found — unauthenticated rate limit is 60 req/h.")
        print("   Set token: export GITHUB_TOKEN='ghp_…'\n")
    else:
        print("✓  GitHub token loaded.\n")

    already_collected = {
        fp.stem.replace("_issues", "").replace("_", "/", 1)
        for fp in OUTPUT_DIR.glob("*_issues.json")
    }
    print(f"Already collected from: {', '.join(sorted(already_collected)) or 'none'}\n")

    new_count = 0
    for cfg in ADDITIONAL_REPOSITORIES:
        repo = cfg["repo"]
        repo_key = repo.replace("/", "_", 1)
        existing_file = OUTPUT_DIR / f"{repo_key}_issues.json"

        if existing_file.exists():
            with open(existing_file, encoding="utf-8") as f:
                existing = json.load(f)
            print(f"→ {repo}: already has {len(existing)} issues — skipping.")
            print()
            continue

        print(f"→ Collecting from {repo}…")
        raw = fetch_issues(repo, cfg["labels"], cfg["max_issues"])
        if not raw:
            print(f"   No issues collected.\n")
            continue

        cleaned = [clean_issue(i, repo) for i in raw]
        saved = save_repo_file(repo, cleaned)
        new_count += saved
        print()
        time.sleep(2)

    total = rebuild_combined()

    summary_path = OUTPUT_DIR / "collection_summary.json"
    summary: dict = {}
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            summary = json.load(f)

    summary.update({
        "last_updated": datetime.now().isoformat(),
        "total_issues": total,
        "new_issues_this_run": new_count,
    })
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Collection complete. New issues added: {new_count}. Grand total: {total}.")
    if total >= 200:
        print("  🎯 200+ bugs claim is now satisfied.")
    else:
        print(f"  ⚠  Still {200 - total} short of 200. Add more repos or increase max_issues.")


if __name__ == "__main__":
    main()
