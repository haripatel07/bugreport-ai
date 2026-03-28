"""Integration tests for API rate limiting behavior."""

import uuid


def test_login_rate_limit_and_headers(client):
    email = f"ratelimit_{uuid.uuid4().hex[:10]}@example.com"
    password = "StrongPass123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 200
    assert "X-RateLimit-Remaining" in register_response.headers

    responses = []
    for _ in range(11):
        responses.append(
            client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
        )

    # Successful attempts should expose remaining quota headers.
    assert "X-RateLimit-Remaining" in responses[0].headers
    assert responses[-1].status_code == 429
    payload = responses[-1].json()
    assert payload["error"] == "rate_limit_exceeded"
    assert "Retry-After" in responses[-1].headers
