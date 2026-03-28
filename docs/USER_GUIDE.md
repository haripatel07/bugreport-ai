# User Guide

## Quick Start

### 1) Start Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Using the App

### Analyze Page

1. Paste your error content.
2. Pick input type: text, stack trace, log, or JSON.
3. (Optional) add environment key-value lines.
4. Run analysis.

You will receive:
- Bug Report
- Root Cause Analysis
- Fix Recommendations
- Similar Bugs (if found)

### Guest vs Signed-in Mode

Guest mode:
- Limited free analysis
- No history persistence

Signed-in mode:
- Full authenticated analysis
- Saved history records
- View and delete history entries

### History Page

- Lists your saved analysis records (signed-in users)
- Supports pagination
- Open each record for details
- Delete records as needed

### Settings Page

- Set preferred model (if available)
- Check API reachability and runtime status

## Tips for Better Results

- Include the full stack trace when available.
- Include environment details (runtime, framework, OS, versions).
- Keep input focused on one issue at a time.

## Common Issues

### "Sign in to view your saved analysis history"

Reason:
- History is available only for authenticated users.

Fix:
- Login/Register from the Analyze page.

### Slow first response in cloud deployment

Reason:
- Free-tier services may sleep when idle.

Fix:
- Retry after warm-up.

## Data Privacy Notes

- Guest analyses are not persisted to history.
- Authenticated analyses are stored for your account history.
- Avoid submitting sensitive secrets in logs or stack traces.
