# Project Highlights

## What This Project Solves

BugReport AI helps developers move from raw error text to actionable debugging outputs quickly.

Input can be:
- text
- stack trace
- log fragment
- JSON error payload

Output includes:
- structured bug report
- root cause analysis with confidence scores
- ranked fix recommendations
- semantically similar bugs from open-source issue history

## Key Achievements

- End-to-end backend pipeline implemented and production-hardened
- JWT auth, rate limiting, API versioning, migrations, and structured logging
- Frontend dashboard with clear workflows and responsive layout
- Persisted history with record detail and deletion
- Guest mode for limited free analysis without login
- CI pipeline for backend unit tests, backend integration tests, and frontend build
- Free-tier cloud deployment plan: Render + Neon

## Technical Stack

Backend:
- FastAPI
- SQLAlchemy + Alembic
- SlowAPI
- structlog

AI/Analysis:
- Rule-based input processing
- RCA pattern engine
- LLM report and recommendation synthesis with fallback behavior
- FAISS-based semantic search

Frontend:
- React + TypeScript + Vite
- Custom CSS design system

## Current User Flows

Authenticated user:
1. Register/Login
2. Submit analysis input
3. View bug report + RCA + recommendations + similar bugs
4. View/manage saved history

Guest user:
1. Submit input using free analysis mode
2. Get analysis results
3. Prompted to sign in for persistence and full management features

## Validation Snapshot

Latest local verification:
- Backend unit tests: pass
- Backend integration tests: pass
- Frontend production build: pass
