
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.main import app, pool


@pytest.fixture(scope="module")
def client():
    # Keep one application lifecycle for the shared connection pool.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def created_codes():
    # Track records created by each test and remove them even after failures.
    codes = []
    yield codes

    if codes:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM urls WHERE short_code = ANY(%s)",
                    (codes,),
                )


@pytest.fixture
def create_url(client, created_codes):
    def _create_url(url):
        response = client.post(
            "/api/urls",
            json={"original_url": url},
        )

        if response.status_code == 201:
            created_codes.append(response.json()["short_code"])

        return response

    return _create_url


def test_create_url_rejects_invalid_url(client):
    response = client.post(
        "/api/urls",
        json={"original_url": "not-a-url"},
    )

    assert response.status_code == 422


def test_create_url_rejects_missing_url(client):
    response = client.post("/api/urls", json={})

    assert response.status_code == 422


def test_create_url_successfully(create_url):
    response = create_url("https://example.com")

    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com/"
    assert len(data["short_code"]) == 6


def test_redirect_to_original_url(client, create_url):
    created = create_url("https://example.com")
    assert created.status_code == 201
    data = created.json()

    response = client.get(
        f"/{data['short_code']}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == data["original_url"]


def test_unknown_short_code_returns_404(client, create_url, created_codes):
    created = create_url("https://example.com")
    assert created.status_code == 201
    short_code = created.json()["short_code"]

    # Remove the mapping so the redirect lookup must return 404.
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM urls WHERE short_code = %s",
                (short_code,),
            )

    response = client.get(f"/{short_code}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_create_url_retries_after_short_code_collision(
    create_url, monkeypatch
):
    existing = create_url("https://first-example.com")
    assert existing.status_code == 201
    existing_code = existing.json()["short_code"]

    fresh_code = (
        "Zz9Xy8" if existing_code != "Zz9Xy8" else "Yy8Xz7"
    )
    generated_codes = iter([existing_code, fresh_code])

    monkeypatch.setattr(
        "app.main.generate_short_code",
        lambda length=6: next(generated_codes),
    )

    response = create_url("https://second-example.com")

    assert response.status_code == 201
    assert response.json()["short_code"] == fresh_code


def test_create_url_returns_503_after_collision_retries_exhausted(
    create_url, monkeypatch
):
    existing = create_url("https://existing-example.com")
    assert existing.status_code == 201
    existing_code = existing.json()["short_code"]

    monkeypatch.setattr(
        "app.main.generate_short_code",
        lambda length=6: existing_code,
    )

    response = create_url("https://another-example.com")

    assert response.status_code == 503


def test_create_url_rejects_malformed_json(client):
    response = client.post(
        "/api/urls",
        content='{"original_url": ',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_create_url_rejects_extremely_long_url(client):
    long_url = "https://example.com/" + ("a" * 100_000)

    response = client.post(
        "/api/urls",
        json={"original_url": long_url},
    )

    assert response.status_code == 422


def test_create_url_propagates_database_unavailable_error(client):
    with patch(
        "app.main.pool.connection",
        side_effect=psycopg.OperationalError("Database unavailable"),
    ):
        with pytest.raises(
            psycopg.OperationalError,
            match="Database unavailable",
        ):
            client.post(
                "/api/urls",
                json={"original_url": "https://example.com"},
            )


def test_concurrent_url_creation_generates_unique_codes(
    client, created_codes
):
    urls = [
        f"https://example.com/page/{i}"
        for i in range(10)
    ]

    def create(url):
        return client.post("/api/urls", json={"original_url": url})

    with ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(create, urls))

    # Register successful inserts for cleanup before checking assertions.
    created_codes.extend(
        response.json()["short_code"]
        for response in responses
        if response.status_code == 201
    )

    assert all(response.status_code == 201 for response in responses)

    codes = [response.json()["short_code"] for response in responses]
    assert len(codes) == len(set(codes))







def test_database_error_does_not_expose_details():
    # Prevent TestClient from raising the exception directly so the test can inspect the HTTP response.
    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        # Simulate a database failure without interrupting PostgreSQL or affecting other tests.
        with patch(
            "app.main.pool.connection",
            side_effect=psycopg.OperationalError(
                "Database unavailable"
            ),
        ):
            response = client.post(
                "/api/urls",
                json={"original_url": "https://example.com"},
            )

    # Ensure the API returns HTTP 500 instead of reporting a successful URL creation.
    assert response.status_code == 500

    # Prevent internal database error details from leaking to API clients.
    assert "Database unavailable" not in response.text
