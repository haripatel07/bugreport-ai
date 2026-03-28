"""Integration tests for recommendation contract schema."""


def test_recommendation_schema_fields(client, auth_headers):
    response = client.post(
        "/api/v1/recommend-fix",
        json={
            "description": "KeyError: 'token' raised in auth middleware when request headers are missing",
            "input_type": "text",
            "use_search": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["bug_report"] is not None

    recommendations = payload["data"]["recommendations"]["recommendations"]
    assert recommendations

    first_item = recommendations[0]
    assert "title" in first_item
    assert "description" in first_item
    assert "implementation_steps" in first_item
    assert "difficulty" in first_item
    assert "code_example" in first_item

    history_response = client.get("/api/v1/history?limit=20&offset=0", headers=auth_headers)
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert history_payload["count"] == 1
