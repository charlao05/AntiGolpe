# Provider Gate Sandbox Security Rules

- The provider-neutral dry-run harness makes no network calls.
- The local OpenAI adapter is real code but is not imported by production runtime or CI.
- `OpenAIAdapter` calls `require_authorization()` before reading `OPENAI_API_KEY`.
- Without `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED`, adapter construction fails closed.
- `OPENAI_API_KEY` is read only from the local process environment and is never logged or persisted.
- The adapter applies a conservative pre-call spend check and `max_completion_tokens=800`; provider-side billing limits remain a required independent control.
- Benchmark inputs are the frozen synthetic 30 cases only.
- Local results must remain outside the public repository.
- `CONFIRMED` must remain unset until Provider Gate approval is complete.
