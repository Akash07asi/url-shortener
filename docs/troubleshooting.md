
# Troubleshooting Log

This document records errors encountered during development, their root causes, fixes, and verification steps.

## 1. Alembic Uses the Wrong Python Environment

**Problem:** Running `alembic current` fails with `ModuleNotFoundError: No module named 'psycopg'`.

**Root cause:** The `alembic` executable points to the Anaconda environment instead of the project's `.venv`.

**Fix:**

```bash
python -m alembic current
```

Run this command with the project's virtual environment activated.

**Verification:**

```bash
which python
python -m alembic current
```

**Lesson:** Use `python -m <module>` when you need to ensure a command runs through the active Python interpreter.

## 2. Swagger UI Fails to Display an External Redirect

**Problem:** Testing the redirect endpoint in Swagger UI displays `Failed to fetch`.

**Root cause:** The endpoint redirects the browser to an external destination, and Swagger UI may fail while following that redirect.

**Fix:** Inspect the response using curl without following redirects.

```bash
curl -i --max-redirs 0 http://127.0.0.1:8000/R7o3Y7
```

**Expected result:** HTTP `307 Temporary Redirect` with a `Location` header containing the destination URL.

**Lesson:** A browser-based API testing error does not necessarily mean the API endpoint is broken. Inspect the actual HTTP response.

## 3. Alembic Migration State and Database Schema

**Problem:** Alembic reports a migration as applied, but the database schema needs independent verification.

**Root cause:** `alembic stamp` records a migration revision without executing its migration operations.

**Fix:** Check the recorded revision and inspect the actual database constraints separately.

```bash
python -m alembic current
```

Inside `psql`:

```sql
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.urls'::regclass;
```

**Lesson:** Migration history and actual database schema are different things. Verify both when debugging migrations.

## 4. SQL Commands Entered in the Shell Instead of PostgreSQL

**Problem:** Commands such as `SELECT` produce `zsh: command not found`.

**Root cause:** SQL was entered in the terminal shell rather than inside the PostgreSQL client.

**Fix:**

```bash
psql url_shortener
```

Wait for the `url_shortener=#` prompt before entering SQL. Exit with:

```text
\q
```

**Lesson:** Shell commands and SQL commands run in different environments.

## 5. Short-Code Length Constraint

**Problem:** A short code with fewer than six characters is rejected by PostgreSQL.

**Root cause:** The database has a check constraint requiring exactly six characters.

**Verification:**

```sql
SELECT id, short_code
FROM urls
WHERE LENGTH(short_code) <> 6;
```

**Expected result:** Zero rows.

**Lesson:** Database constraints enforce data integrity even when data bypasses application-level validation.
