# API Reference

## Base URL

For local development:

`http://127.0.0.1:8000`

Interactive API documentation is available at `/docs` while the
FastAPI application is running.

## 1. Check Application Status

### `GET /`

Returns a status message confirming that the API is running.

**Success response:** `200 OK`

```json
{
  "message": "URL Shortener is running"
}
```

This endpoint does not query PostgreSQL.

## 2. Create a Short URL

### `POST /api/urls`

Creates a short-code mapping for a submitted URL.

**Request body:**

```json
{
  "original_url": "https://example.com"
}
```

The request body must contain `original_url`. Pydantic validates
the URL using `HttpUrl` before the endpoint processes it.

**Success response:** `201 Created`

```json
{
  "short_code": "Ab12Cd",
  "original_url": "https://example.com/"
}
```

The returned short code is randomly generated. The example code
above is illustrative; actual codes vary.

**Possible error responses:**

- `422 Unprocessable Entity`: The request body is missing required
  data, contains invalid JSON, or contains an invalid URL.
- `503 Service Unavailable`: The application exhausts its five
  short-code generation attempts because of uniqueness collisions.

Other database failures are not converted into the documented
503 collision response by this endpoint.

## 3. Redirect to the Original URL

### `GET /{short_code}`

Looks up a short code in PostgreSQL and redirects the client to
the stored destination.

**Example request:**

`GET /Ab12Cd`

**Success response:** `307 Temporary Redirect`

The response's `Location` header contains the original URL.

**Error response:**

- `404 Not Found`: No mapping exists for the requested short code.

## Error Handling Summary

| Situation | Status |
|---|---:|
| Root endpoint succeeds | 200 |
| Short URL created | 201 |
| Invalid request data | 422 |
| Unknown short code | 404 |
| Short-code collision retries exhausted | 503 |

Database failures outside the explicitly handled collision case
are not mapped to a custom API error by the current implementation.

## Current API Scope

The API currently provides status checking, short URL creation,
and redirection. Authentication, authorization, rate limiting,
and analytics are not implemented in this version.
