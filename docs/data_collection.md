# Data Collection Guide

## Overview
This project uses real-world bug reports from open-source GitHub repositories.

## Collected Dataset Statistics
- **Total Issues:** 200+
- **Repositories:** 10 major open-source projects
- **Date Collected:** [Your date]
- **Size:** ~15-20 MB

## How to Reproduce

### Step 1: Get GitHub Token
```bash
# Get token from: https://github.com/settings/tokens
# Permissions needed: public_repo (read-only)
export GITHUB_TOKEN="your_token_here"