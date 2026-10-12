
# Development Log

This file records important implementation decisions, the reasoning behind them, and lessons learned during development.

## 1. PostgreSQL for Persistent Storage

**Decision:** Store URL mappings in PostgreSQL instead of an in-memory dictionary.

**Reason:** In-memory mappings disappear when the application restarts. PostgreSQL provides persistent storage.

**Trade-off:** The application must manage database connections, transactions, schema changes, and database failures.

## 2. Database-Enforced Short-Code Uniqueness

**Decision:** Use a unique constraint on `short_code`.

**Reason:** Two requests could generate the same code. Application-level checks alone cannot reliably prevent concurrent requests from inserting duplicate codes.

**Implementation:** PostgreSQL rejects duplicate codes, and the application retries when the violation comes from `urls_short_code_key`.

**Lesson:** Let the database enforce critical integrity rules and handle expected constraint violations in the application.

## 3. Six-Character Short Codes

**Decision:** Require short codes to contain exactly six characters.

**Reason:** A fixed length keeps the generated codes consistent.

**Implementation:** The application generates six-character codes, and PostgreSQL enforces the length with a check constraint.

## 4. Connection Pooling

**Decision:** Reuse database connections with `psycopg_pool.ConnectionPool`.

**Reason:** Opening a new connection for every request creates unnecessary connection overhead.

**Current configuration:** Minimum 2 connections and maximum 10 connections per application process.

**Trade-off:** Pool size must be considered alongside request concurrency and the database's connection limit.

## 5. Versioned Database Migrations

**Decision:** Use Alembic to track schema changes.

**Reason:** A new environment needs a repeatable way to create the database schema, and existing environments need controlled upgrades.

**Lesson:** A migration revision records intended schema changes. Always verify that the actual database schema matches the expected state.

## 6. Environment Consistency

**Decision:** Run Alembic using `python -m alembic` inside the project's virtual environment.

**Reason:** The standalone `alembic` executable resolved to the Anaconda environment, which did not have the project's database driver available.

**Lesson:** Verify which Python interpreter runs a command when environment-related errors occur.

## 7. Redirect Testing

**Decision:** Use `curl -i --max-redirs 0` to inspect redirect responses.

**Reason:** Swagger UI may report `Failed to fetch` when following an external redirect, even when the API correctly returns a redirect response.

**Lesson:** Test the actual HTTP status and `Location` header before concluding that an endpoint is broken.
