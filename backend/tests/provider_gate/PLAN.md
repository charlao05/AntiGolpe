# Provider Gate Sandbox — Execution Plan

The sandbox will support three controlled phases over the frozen 30-case benchmark:

1. `pure`
2. `framework`
3. `framework_structured`

The provider-neutral runner still only plans runs and validates fixtures. A
separate `openai_local_adapter.py` exists for explicitly authorized local
execution; it is not used by the dry-run planner or CI.

The local adapter is fail-closed, checks authorization before reading the API
key, applies a conservative pre-call spend guard, and caps output with
`max_completion_tokens=800`. Its post-call usage accounting is a circuit
breaker and not a substitute for provider-side billing controls.

For N approved providers, the full experiment is `30 x 3 x N` calls. The
runner/harness must stop on the configured spend ceiling and immediately report
any D1-D6 critical failure.
