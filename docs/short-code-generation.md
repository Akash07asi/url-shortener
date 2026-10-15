# Short-Code Generation

## 1. Current Strategy

The application generates random six-character codes using `secrets.choice()`.

The alphabet contains:
- Digits: `0-9` (10)
- Lowercase letters: `a-z` (26)
- Uppercase letters: `A-Z` (26)

Total alphabet size: 62 characters.

For six-character codes:

\[
N = 62^6 = 56,800,235,584
\]

`secrets.choice()` provides security-oriented randomness. It does not guarantee uniqueness.

## 2. Collision Probability

A collision occurs when two generations produce the same code.

The approximate probability of at least one collision among `k` generated codes is:

\[
P \approx 1 - e^{-k(k-1)/(2N)}
\]

where `N = 62^6`.

| Generated codes | Approximate probability of at least one collision |
|---:|---:|
| 10,000 | 0.088% |
| 100,000 | 8.4% |
| 500,000 | 89.0% |
| 1,000,000 | 99.985% |

This is the probability of a collision somewhere in the collection, not the probability that the next insertion collides.

## 3. Collision Handling

1. Generate a candidate code.
2. Attempt to insert it into PostgreSQL.
3. The `urls_short_code_key` unique constraint rejects duplicates.
4. Retry only when that specific constraint is violated.
5. Stop after the configured retry limit.
6. Return HTTP 503 if all attempts fail.

The database constraint is essential because concurrent requests can generate the same code. An application-level pre-check alone cannot reliably prevent this.

## 4. Code Length

| Length | Possible codes |
|---:|---:|
| 4 | 14,776,336 |
| 5 | 916,132,832 |
| 6 | 56,800,235,584 |
| 7 | 3,521,614,606,208 |
| 8 | 218,340,105,584,896 |

Capacity is `62^L`, where `L` is code length. Longer codes provide more capacity but produce longer URLs.

## 5. Alternative Strategies

### Sequential IDs
- Simple and naturally distinct within the ID sequence.
- Can reveal ordering and make enumeration easier.

### Base62-encoded IDs
- Converts integers into compact strings using 62 symbols.
- Encoding does not hide sequential patterns or provide encryption.

### Hash-based codes
- Deterministic for the same input.
- Truncation can cause collisions, so uniqueness enforcement is still required.

### UUID-based codes
- Provide a large identifier space.
- Standard UUIDs are longer than six characters; truncation increases collision risk.

## 6. Why Random Six-Character Codes?

The current strategy prioritizes compact URLs and less predictable identifiers. PostgreSQL enforces uniqueness, and the application retries collisions with a bounded limit.

The database `id` is separate from the public short code.

## 7. Security Limitations

An unpredictable code is not an access-control mechanism. Private resources still require authentication and authorization.

## 8. Scope

This document explains the existing strategy and trade-offs. It does not change application behavior. Testing remains part of Phase 11.
