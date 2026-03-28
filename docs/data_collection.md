# Data Collection Guide

## Overview

BugReport AI uses real-world open-source issues to support semantic search and recommendation context.

Data is collected from major GitHub repositories, normalized, and then indexed for similarity retrieval.

## Dataset Snapshot

- Total issues collected: 200+
- Source repositories: major OSS projects (for example language runtimes, frameworks, and tooling)
- Output location: data/raw/github_issues
- Processed artifacts: data/processed and data/samples

## Prerequisites

- Python environment with backend dependencies installed
- GitHub token with read access to public repositories

## Reproduction Steps

### 1) Export GitHub token

```bash
export GITHUB_TOKEN="your_token_here"
```

### 2) Run base collection

```bash
cd scripts
python collect_data.py
```

### 3) Optional: run extended collection

```bash
python collect_more_data.py
```

### 4) Build semantic search index

```bash
python build_search_index.py
```

### 5) Regenerate demo/sample inputs (optional)

```bash
python create_samples.py
```

## Output Files

Common output files include:

- data/raw/github_issues/combined_dataset.json
- data/raw/github_issues/collection_summary.json
- data/samples/test_cases.json
- data/samples/summary.json

## Validation Checklist

After collection, verify:

1. collection_summary.json exists and has non-zero counts
2. combined_dataset.json exists and is valid JSON
3. search index build script completes successfully
4. /api/v1/search/similar returns results when index is available

## Notes

- API rate limits may affect collection speed.
- Keep the token private and avoid committing environment secrets.
- Collection can be re-run safely to refresh data snapshots.