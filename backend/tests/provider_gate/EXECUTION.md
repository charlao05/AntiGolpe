# Provider Gate — Execution Authorization

## Not authorized yet

The repository contains a provider-neutral dry-run harness plus an explicitly
local OpenAI adapter. The adapter is **fail-closed** and does not authorize
itself: `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED` is required before it
reads `OPENAI_API_KEY` or can make a provider request.

Do **not** execute real provider calls until `docs/PROVIDER_GATE.md` records
and the project owner approves:

- total spend ceiling;
- per-provider spend ceiling;
- credential/account ownership;
- execution environment;
- provider-specific retention/training policy for the exact plan and endpoint;
- result-storage location and access policy;
- frozen prompts/framework configuration;
- provider-side billing limits/alerts where available.

## Required invariants before real execution

- exactly 30 frozen benchmark cases;
- exactly three experimental phases per provider;
- no production traffic;
- no real user data;
- no API key in source control;
- results outside the public repository;
- pre-call local spend check;
- provider-side billing controls where available;
- automatic stop on any D1-D5 critical security failure;
- D6 recorded separately as exploratory;
- blind provider identifiers (`Provider_A`, `Provider_B`, `Provider_C`) for evaluator-facing results;
- the provider-to-identifier mapping stored separately from evaluator artifacts.

`CONFIRMED` remains unset until these prerequisites are closed and the Provider
Gate is explicitly approved.
