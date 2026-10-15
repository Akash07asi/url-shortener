# Architecture

## Overview

The URL Shortener is a FastAPI application backed by PostgreSQL.
It creates short codes for submitted URLs and redirects requests
to the original URLs stored in the database.

The application uses Psycopg for database access and a connection
pool to reuse PostgreSQL connections.

## Components

- **FastAPI (`app/main.py`):** Defines the HTTP endpoints and
  coordinates request processing.
- **Pydantic (`URLCreate`):** Validates the submitted `original_url`
  using `HttpUrl` before the endpoint processes the request.
- **Short-code generator:** Uses `secrets.choice()` to generate
  six-character identifiers from uppercase letters, lowercase
  letters, and digits.
- **Psycopg:** Executes parameterized SQL queries against PostgreSQL.
- **Connection pool:** Reuses database connections. It is configured
  with a minimum of 2 and a maximum of 10 connections.
- **PostgreSQL:** Stores URL mappings in the `urls` table.
- **Alembic:** Manages database schema migrations separately from
  normal HTTP request processing.

## Architecture Diagram

```text
Client
  |
  v
FastAPI application
  |
  +-- GET /
  |     `-- Return status message
  |
  +-- POST /api/urls
  |     |
  |     v
  |   Pydantic URL validation
  |     |
  |     v
  |   Generate short code
  |     |
  |     v
  |   Psycopg connection pool
  |     |
  |     v
  |   INSERT URL mapping into PostgreSQL
  |     |
  |     v
  |   Return short_code and original_url
  |
  `-- GET /{short_code}
        |
        v
      Query PostgreSQL for original_url
        |
        +-- Mapping found --> HTTP redirect
        |
        `-- Mapping missing --> HTTP 404

Alembic --> Database schema migrations
```

## Request Flows

### 1. Create a Short URL

1. The client sends `POST /api/urls` with an `original_url`.
2. Pydantic validates the request body.
3. The application generates a six-character short code.
4. The application inserts the URL and code into PostgreSQL using
   a parameterized SQL statement.
5. If the short code violates the `urls_short_code_key` constraint,
   the application retries code generation, up to five attempts.
6. On success, the API returns HTTP 201 with `short_code` and
   `original_url`.
7. If all five attempts collide, the API returns HTTP 503.

Other database uniqueness violations are not treated as short-code
collisions and are allowed to propagate.

### 2. Redirect to the Original URL

1. The client requests `GET /{short_code}`.
2. The application queries PostgreSQL for the matching URL.
3. If the mapping exists, `RedirectResponse` redirects the client
   to the stored destination. Its default status is HTTP 307.
4. If no mapping exists, the application returns HTTP 404.

### 3. Root Endpoint

`GET /` returns a JSON status message indicating that the URL
Shortener is running. This endpoint does not query PostgreSQL.

## Database Access and Lifecycle

The application reads `DATABASE_URL` from the environment.
If it is not set, the configured fallback is
`postgresql:///url_shortener`.

The connection pool is configured when the application module loads.
FastAPI's lifespan handler opens the pool at startup and closes it
during shutdown.

Database operations acquire connections from the pool and execute
SQL through Psycopg cursors. Parameterized queries keep user-provided
values separate from SQL statement text.

## Schema Migrations

Alembic manages changes to the PostgreSQL schema. Migrations are
applied through development or deployment commands, not as part of
each URL creation or redirect request.

The existing database was initialized before Alembic was introduced.
Its baseline migration was stamped against the existing schema.
A fresh database follows the baseline migration to create the initial
table, followed by later migrations.

See [Database Design](database-design.md) for the schema, constraints,
and migration details.

## Current Scope and Limitations

- URL mappings are stored in PostgreSQL and persist across application
  restarts.
- The application uses a connection pool but does not currently use
  a cache.
- Short-code collisions are handled with a bounded retry loop and a
  database uniqueness constraint.
- Authentication, authorization, and rate limiting are not currently
  implemented.
- URL format validation does not guarantee that a destination is safe
  to visit.
- The application does not currently implement analytics or
  background processing.
