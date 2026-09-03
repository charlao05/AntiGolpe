# Provider Gate Sandbox — Current Authorization State

This sandbox intentionally stops before external execution by default.

A real local adapter (`openai_local_adapter.py`) exists only as an explicitly
invoked, fail-closed harness component. Its constructor requires
`ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED` before reading
`OPENAI_API_KEY`. It is never imported by production runtime or CI.

Pending human governance decisions before any paid execution:

1. Provider-specific retention/training policy verification for the exact endpoint and plan.
2. Confirmation of provider billing limits and alerts.
3. Final approval of the experimental configuration and prompts/framework.
4. Review of the adapter and harness diff.

The local adapter's spend guard performs a conservative pre-call worst-case
estimate and also records actual post-call usage as a circuit breaker. It is
not a substitute for provider-side billing limits or final accounting.

`CONFIRMED` must remain unset until the Provider Gate approval process is
complete. No external request is authorized by this branch merely because the
adapter exists.
