# API Reference

Base URL (local):
- http://localhost:8000

Versioned API prefix:
- /api/v1

## Public Endpoints

- GET /                      : service root
- GET /api/health            : infrastructure health
- GET /api/stats             : infrastructure stats

## Auth Endpoints

- POST /api/v1/auth/register : create user account
- POST /api/v1/auth/login    : get JWT access token
- GET /api/v1/auth/me        : current authenticated user

Use Authorization header for protected endpoints:
- Authorization: Bearer <access_token>

## Analysis Endpoints

Protected:
- POST /api/v1/process-input
- POST /api/v1/generate-report
- POST /api/v1/analyze-root-cause
- POST /api/v1/analyze
- POST /api/v1/search/similar
- POST /api/v1/recommend-fix

Guest-access:
- POST /api/v1/analyze-free

## History Endpoints (Protected)

- GET /api/v1/history
- GET /api/v1/history/{record_id}
- DELETE /api/v1/history/{record_id}

## Utility Endpoints

- GET /api/v1/health
- GET /api/v1/stats
- GET /api/v1/models
- GET /api/v1/supported-languages
- GET /api/v1/rca/statistics
- GET /api/v1/search/stats

## Example: Login

Request:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "StrongPass123"
}
```

Response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

## Example: Authenticated Recommendation Pipeline

Request:

```http
POST /api/v1/recommend-fix
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "description": "TypeError: Cannot read property 'map' of undefined",
  "input_type": "text",
  "environment": {
    "runtime": "node18"
  },
  "use_search": true
}
```

Response shape:
- record_id
- processed_input
- bug_report
- root_cause_analysis
- similar_bugs
- recommendations

## Rate Limiting

Key protected routes are rate-limited per client IP.
On limit exceed:
- HTTP 429
- JSON payload with error details
- Retry-After header

## Deprecated Alias

- POST /api/analyze-cause
  - Redirect/deprecation path for older references
  - Use /api/v1/analyze-root-cause instead
