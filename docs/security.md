# Security

## Existing Protections

### URL Validation
- Pydantic's `HttpUrl` validates submitted URLs.
- Only HTTP and HTTPS schemes are accepted.
- Validating URL format does not guarantee that a destination is safe.

### SQL Injection Protection
- Use parameterized SQL queries for user-provided values.
- Parameterization separates SQL commands from input values.

### Database Constraints
- PostgreSQL enforces uniqueness of `short_code`.
- The database enforces the six-character short-code requirement.
- These constraints protect data integrity even when application logic fails.

### Collision Handling
- Short-code generation retries collisions up to five times.
- If all attempts collide, the API returns HTTP 503.
- The unique database constraint remains the final safeguard against duplicate codes.

### Error Behavior
- Unknown short codes return HTTP 404.
- Database failures should not expose credentials or internal database details to API clients.

## Configuration and Secrets

- The application reads its database connection string from `DATABASE_URL`.
- A local fallback connection string is configured for development.
- Environment files containing real secrets must not be committed.
- The `.env.example` file should contain placeholders only, never real credentials.
- If credentials are exposed, rotate them and investigate the exposure.

## Limitations and Risks

- A syntactically valid HTTP or HTTPS URL may still lead to a malicious destination.
- Authentication and authorization are not implemented.
- Rate limiting is not implemented.
- A database connection pool limits pooled connections, not incoming HTTP requests.
- Short codes are identifiers, not authentication credentials.
- Dependency audits can identify known vulnerabilities but cannot prove the application is vulnerability-free.
- Production deployment requires appropriate secret management, monitoring, and abuse-prevention controls.
