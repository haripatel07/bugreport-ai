"""Integration tests for /api/v1/analyze and persisted history endpoints."""


def test_analyze_requires_authentication(client):
    response = client.post(
        "/api/v1/analyze",
        json={
            "description": "Traceback (most recent call last):\nTypeError: unsupported operand type(s)",
            "input_type": "stack_trace",
        },
    )
    assert response.status_code == 401


def test_analyze_free_guest_mode_without_auth(client):
    response = client.post(
        "/api/v1/analyze-free",
        json={
            "description": "TypeError: Cannot read properties of undefined (reading 'map')",
            "input_type": "text",
            "environment": {"runtime": "node18"},
            "use_search": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["guest_mode"] is True
    assert payload["data"]["bug_report"] is not None
    assert payload["data"]["root_cause_analysis"] is not None

    history_response = client.get("/api/v1/history?limit=20&offset=0")
    assert history_response.status_code == 401


def test_analyze_and_history_roundtrip(client, auth_headers):
    analyze_response = client.post(
        "/api/v1/analyze",
        json={
            "description": "Traceback (most recent call last):\n  File \"main.py\", line 10, in <module>\n    print(1 + 'x')\nTypeError: unsupported operand type(s) for +: 'int' and 'str'",
            "input_type": "stack_trace",
            "environment": {"python": "3.12"},
        },
        headers=auth_headers,
    )

    assert analyze_response.status_code == 200
    payload = analyze_response.json()
    assert payload["success"] is True
    assert payload["data"]["bug_report"]
    assert payload["data"]["root_cause_analysis"]

    record_id = payload["data"]["record_id"]
    history_list_response = client.get("/api/v1/history?limit=20&offset=0", headers=auth_headers)
    assert history_list_response.status_code == 200
    history_list_payload = history_list_response.json()
    assert history_list_payload["total_count"] >= 1
    assert any(entry["id"] == record_id for entry in history_list_payload["records"])

    history_record_response = client.get(f"/api/v1/history/{record_id}", headers=auth_headers)
    assert history_record_response.status_code == 200

    history_payload = history_record_response.json()
    assert history_payload["record"]["id"] == record_id
    assert history_payload["record"]["bug_report"] is not None

    delete_response = client.delete(f"/api/v1/history/{record_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    deleted_fetch_response = client.get(f"/api/v1/history/{record_id}", headers=auth_headers)
    assert deleted_fetch_response.status_code == 404
