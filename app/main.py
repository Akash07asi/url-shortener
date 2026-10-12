
import os
import secrets
import string

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from contextlib import asynccontextmanager
from psycopg_pool import ConnectionPool


# Stores the database connection URL so the application can connect to PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql:///url_shortener"
)

# Limits collision retries to prevent endless attempts when generating short codes.
MAX_CODE_GENERATION_ATTEMPTS = 5

# Reuses database connections across requests and limits the pool to 10 connections.
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=2,
    max_size=10,
    open=False,
)


# Opens the pool at startup and closes it when the application shuts down.
@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open(wait=True)
    try:
        yield
    finally:
        pool.close()


# Creates the FastAPI application and manages the database pool lifecycle.
app = FastAPI(lifespan=lifespan)

# Validates incoming URL data before the application attempts to store it.
class URLCreate(BaseModel):
    original_url: HttpUrl


def generate_short_code(length: int = 6) -> str:
    # Generates a random identifier to create a compact URL users can share.
    characters = string.ascii_letters + string.digits
    return "".join(
        secrets.choice(characters) for _ in range(length)
    )


@app.get("/")
def root():
    # Confirms that the API is running without requiring a database operation.
    return {"message": "URL Shortener is running"}


@app.post("/api/urls", status_code=201)
def create_short_url(data: URLCreate):
    # Stores a new URL mapping in PostgreSQL and retries if its short code collides.
    for _ in range(MAX_CODE_GENERATION_ATTEMPTS):
        short_code = generate_short_code()

        try:
            # Manages the database transaction so a successful insert is committed.
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO urls (original_url, short_code)
                        VALUES (%s, %s)
                        RETURNING short_code, original_url
                        """,
                        (str(data.original_url), short_code),
                    )
                    row = cur.fetchone()

            # Returns the newly created mapping so the client can use its short code.
            return {
                "short_code": row[0],
                "original_url": row[1],
            }

        except psycopg.errors.UniqueViolation as exc:
            # Retries only for short-code collisions; unrelated uniqueness errors must surface.
            if exc.diag.constraint_name != "urls_short_code_key":
                raise

    # Reports failure when no unique code can be generated within the retry limit.
    raise HTTPException(
        status_code=503,
        detail="Could not generate a unique short code. Please retry.",
    )


@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    # Looks up the original URL in persistent storage so redirects survive server restarts.
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT original_url
                FROM urls
                WHERE short_code = %s
                """,
                (short_code,),
            )
            row = cur.fetchone()

    # Returns 404 when no stored mapping exists for the requested short code.
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found",
        )

    # Redirects the client to the destination URL retrieved from PostgreSQL.
    return RedirectResponse(url=row[0])
