# BugReport AI

BugReport AI is an AI-assisted debugging platform that converts raw software errors into structured engineering outputs.

It accepts text descriptions, stack traces, logs, and JSON payloads, then performs:

- input extraction and normalization,
- root cause analysis,
- bug report generation,
- semantic similarity search,
- fix recommendation synthesis.

The project includes a FastAPI backend, a React TypeScript frontend, persisted analysis history, and containerized deployment assets.

## Current Status

- Core implementation: complete (Weeks 1-12)
- Academic/demo readiness: complete
- Remaining production step: final cloud target deployment selection and wiring

## Key Capabilities

- Multi-format input support: `text`, `stack_trace`, `log`, `json`
- Language detection for seven languages: Python, JavaScript, TypeScript, Java, C++, Go, Rust
- Root Cause Analysis (RCA) using a curated pattern base
- LLM-assisted report generation with fallback behavior
- Semantic bug retrieval over collected open-source issues (FAISS)
- Recommendation generation using RCA context and optional semantic context
- Analysis history persistence with query endpoints

## Project Structure

```text
bugreport-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models/
│   │   └── services/
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   └── types/
│   └── package.json
├── data/
│   ├── raw/
│   ├── processed/
│   └── samples/
├── scripts/
├── docker-compose.yml
└── CONTEXT.md
```

## Architecture Overview

1. Input Processor parses raw error input and extracts structured fields.
2. RCA Engine matches error patterns and ranks probable causes with confidence.
3. Report Generator creates a structured bug report using configured LLM fallback chain.
4. Search Engine retrieves semantically similar historical bugs using embeddings + FAISS.
5. Recommendation Engine produces actionable fixes using RCA, optional similarity context, and fallback rules.
6. Persistence Layer stores analysis records and history in the configured database.
7. Frontend Dashboard presents report, RCA, and recommendations in a reviewer-friendly workflow.

## Backend API

### Public Endpoints

- `GET /`
- `GET /api/health`
- `GET /api/models`
- `GET /api/stats`
- `GET /api/supported-languages`
- `GET /api/rca/statistics`
- `GET /api/search/stats`
- `GET /api/history`
- `GET /api/history/{record_id}`
- `POST /api/process-input`
- `POST /api/generate-report`
- `POST /api/analyze-root-cause`
- `POST /api/analyze`
- `POST /api/search/similar`
- `POST /api/recommend-fix`

### Compatibility Alias

- `POST /api/analyze-cause` (hidden alias for backwards compatibility)

## Data and Evaluation Snapshot

- Collected issues: 218
- Evaluation cases: 30
- RCA patterns: 31
- RCA cause entries: 79
- RCA categories: 19

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1) Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### Access points

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## Database Configuration

The backend reads `DATABASE_URL` from environment variables.

- Default local fallback: SQLite (`sqlite:///./bugreport_ai.db`)
- Postgres supported in containerized setup via `docker-compose.yml`

## Testing

Run backend tests:

```bash
cd backend
source .venv/bin/activate
pytest tests/test_input_processor.py tests/test_rca_engine.py -v
```

Run frontend production build check:

```bash
cd frontend
npm run build
```

## Containerized Run

From repository root:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## CI

GitHub Actions workflow is provided at:

- `.github/workflows/ci.yml`

It validates:

- backend unit tests,
- frontend production build.

## Notes for Review/Demo

- Frontend review mode currently focuses on analyze + RCA + recommendations.
- Semantic search remains available at backend API level.
- Analysis records are persisted and can be queried through history endpoints.

## License

This repository includes an MIT-style `LICENSE` file at the project root.
