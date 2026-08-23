# Provider Gate Sandbox — Execution Plan

The sandbox will support three controlled phases over the frozen 30-case benchmark:

1. `pure`
2. `framework`
3. `framework_structured`

The current implementation only plans runs and validates fixtures. It does not call providers, read API keys, persist responses, or access the network.

For N approved providers, the full experiment is `30 x 3 x N` calls. The runner must stop on the configured spend ceiling and immediately report any D1-D6 critical failure.
