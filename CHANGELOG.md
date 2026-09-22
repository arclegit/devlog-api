# Changelog

All notable changes to DevLog API are documented here.

## [2.0.0] - 2026-09-22

- Added `POST /ai/activity-summary` for AI-generated activity summaries built from structured analytics context.
- Added an AI provider boundary with mock and OpenAI provider implementations, selected via `AI_PROVIDER`.
- Hardened AI provider failures with mapped HTTP errors (timeout → 504, provider rate limit → 503, API/invalid response → 502).
- Rate-limited AI summary generation to 5 requests per minute.
- Added provider, service, context, and API-level tests for the AI feature; OpenAI tests mock the client and make no paid API calls.

## [1.0.0] - 2026-09-19

- Added account password change and soft deletion.
- Added timezone preference, analytics date filters, and operational probes.
- Added request IDs, structured logs, auth rate limits, Docker, and CI coverage reporting.
- Standardized HTTP and validation error responses.

## [0.1.0]

- Initial production-oriented DevLog API release.
