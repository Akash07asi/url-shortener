import secrets
import string

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl


# Stores the relationship between a short code and its original URL.
# This is temporary storage for Phase 3; PostgreSQL will replace it later.
url_store = {}


# Defines the structure and validation rules for data sent to the API.
class URLCreate(BaseModel):
    original_url: HttpUrl


def generate_short_code(length: int = 6) -> str:
    # Generates a random 6-character identifier using letters and digits.
    # We keep this simple in Phase 3 so we can focus on understanding the
    # short-code-to-URL mapping before designing the production strategy.
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


# Creates the FastAPI application that receives and routes HTTP requests.
app = FastAPI()


@app.get("/")
def root():
    # Provides a simple endpoint to verify that the API is running.
    return {"message": "URL Shortener is running"}


@app.post("/api/urls")
def create_short_url(data: URLCreate):
    # Generates an identifier that will be used to look up the original URL.
    short_code = generate_short_code()

    # Stores the relationship between the generated code and submitted URL.
    url_store[short_code] = str(data.original_url)

    return {
        "short_code": short_code,
        "original_url": str(data.original_url)
    }

@app.get("/{short_code}")
def redirect_to_original(short_code: str):
    # Looks up the original URL using the short code created earlier.
    original_url = url_store.get(short_code)

    # A missing short code means the requested shortened URL does not exist.
    if original_url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    # Sends the browser to the original URL associated with the short code.
    return RedirectResponse(url=original_url)