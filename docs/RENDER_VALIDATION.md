# Render Validation

## Before production validation

1. Confirm the Render service is Live.
2. Call `GET /api/health` and confirm `provider.external` is `false`.
3. Call `POST /api/analyze` using synthetic data only.
4. Exercise all four states.
5. Confirm rate limiting identifies clients correctly behind Render's proxy.
6. Review application logs and, where available, Render HTTP request logs for absence of request bodies, prompts, responses, credentials, and PII.
7. Do not integrate a real LLM until the Provider Gate is approved.
