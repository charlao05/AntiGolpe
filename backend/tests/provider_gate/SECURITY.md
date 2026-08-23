# Provider Gate Sandbox Security Rules

- No provider SDKs or network calls are permitted in the dry-run harness.
- API keys are never read by the current implementation.
- Real adapters require explicit Provider Gate approval before implementation.
- Benchmark inputs are the frozen synthetic 30 cases only.
- Local results must remain outside the public repository.
