"""Integration test fixtures with real SQLite DB + Alembic migrations."""

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def configured_app():
    backend_root = Path(__file__).resolve().parents[2]
    db_path = backend_root / "integration_test.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["JWT_SECRET_KEY"] = "integration_test_secret_key"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_EXPIRE_MINUTES"] = "60"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"

    if db_path.exists():
        db_path.unlink()

    subprocess.run(["alembic", "-c", "alembic.ini", "upgrade", "head"], cwd=backend_root, check=True)

    from app.main import app

    yield app

    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def client(configured_app):
    with TestClient(configured_app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient):
    email = f"integration_{uuid.uuid4().hex[:10]}@example.com"
    password = "StrongPass123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
