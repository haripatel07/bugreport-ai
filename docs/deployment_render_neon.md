# Free Cloud Deployment: Render + Neon

This project can be deployed fully on free tiers with:

- Render free web service (backend)
- Render static site (frontend)
- Neon free PostgreSQL (database)

## 1. Create Neon database (free)

1. Create a Neon account and project.
2. Create a database named `bugreport_ai`.
3. Copy the pooled connection string.
4. Ensure SSL mode is required (`?sslmode=require`).

Example:

postgresql+psycopg://<user>:<password>@<host>/<db>?sslmode=require

## 2. Deploy on Render with blueprint

1. Push this repository to GitHub.
2. In Render, create a new Blueprint and select this repository.
3. Render will detect `render.yaml` and propose two services:
   - `bugreport-ai-backend`
   - `bugreport-ai-frontend`

## 3. Configure environment variables in Render

### Backend (`bugreport-ai-backend`)

Set these values:

- `DATABASE_URL`: Neon connection string from step 1
- `CORS_ORIGINS`: frontend URL from Render static site, for example `https://bugreport-ai-frontend.onrender.com`
- `GROQ_API_KEY` and/or `OPENAI_API_KEY`: optional, if using hosted LLMs

Already defined by blueprint:

- `JWT_SECRET_KEY` (auto-generated)
- `JWT_ALGORITHM=HS256`
- `JWT_EXPIRE_MINUTES=60`
- `LOG_LEVEL=INFO`
- `LOG_FORMAT=json`

### Frontend (`bugreport-ai-frontend`)

Set:

- `VITE_API_BASE_URL`: backend URL with version prefix, for example `https://bugreport-ai-backend.onrender.com/api/v1`

## 4. Validate deployment

1. Open backend health endpoint: `/api/health`
2. Open frontend site URL.
3. Register a user and run an analysis.
4. Confirm history table loads and delete action works.

## Notes

- Render free web services may sleep after inactivity; first request can be slow.
- Keep CORS origin exact (no trailing slash).
- For local development, frontend continues to use `/api/v1` via Vite proxy.
