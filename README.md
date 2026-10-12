# URL Shortener

A production-oriented URL shortener built with Python, FastAPI, and PostgreSQL.

## Features

- Create short URLs through a REST API
- Redirect short codes to their original URLs
- Validate submitted URLs using Pydantic
- Generate random six-character short codes
- Persist URL mappings in PostgreSQL
- Enforce unique short codes and length constraints at the database level
- Retry short-code collisions with a bounded retry limit
- Reuse database connections through a connection pool
- Manage database schema changes with Alembic migrations
- Return appropriate HTTP responses for redirects and unknown short codes

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- Psycopg 3
- Psycopg connection pool
- Alembic
- SQLAlchemy (used by Alembic)

## Project Structure

```text
url-shortener/
├── app/
│   └── main.py
├── migrations/
│   ├── versions/
│   └── env.py
├── alembic.ini
├── requirements.txt
├── README.md
└── .gitignore
```

## Database Schema

The `urls` table contains:

| Column | Purpose |
|---|---|
| `id` | Generated primary key |
| `original_url` | Destination URL |
| `short_code` | Unique six-character identifier |
| `created_at` | Record creation timestamp |

Database constraints enforce primary-key uniqueness, short-code uniqueness, and the six-character short-code rule.

The `original_url` column is not unique because multiple short codes may point to the same destination.

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure PostgreSQL

Create a PostgreSQL database named `url_shortener` and ensure PostgreSQL is running.

The application defaults to:

```text
postgresql:///url_shortener
```

To use another database connection string, set `DATABASE_URL` in your environment.

### 4. Run the application

```bash
python -m uvicorn app.main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Check API status |
| `POST` | `/api/urls` | Create a short URL |
| `GET` | `/{short_code}` | Redirect to the original URL |

Creating a short URL returns `201 Created`. An unknown short code returns `404 Not Found`. A successful redirect typically returns `307 Temporary Redirect`.

## Database Migrations

Run Alembic through the project's Python environment:

```bash
python -m alembic current
python -m alembic history
python -m alembic upgrade head
```

Create a new migration when changing the schema:

```bash
python -m alembic revision -m "describe schema change"
```

Edit the generated migration's `upgrade()` and `downgrade()` functions before applying it.

**Important:** The existing database was initialized before Alembic was introduced. The baseline revision was stamped against that existing schema. For a fresh database, the baseline migration creates the initial table, and subsequent migrations apply later schema changes.

Do not stamp an uninitialized database simply to bypass migrations.

## Verification

The current implementation has been tested for:

- Creating URL mappings
- Redirecting valid short codes
- Returning `404 Not Found` for unknown codes
- Enforcing unique short codes
- Rejecting short codes that are not exactly six characters
- Applying and tracking schema migrations

## Current Scope

This project focuses on API engineering and database engineering. Additional capabilities should be introduced in separate phases rather than mixed into the current implementation.




├── docs/
│   ├── database-design.md
│   ├── development-log.md
│   └── troubleshooting.md