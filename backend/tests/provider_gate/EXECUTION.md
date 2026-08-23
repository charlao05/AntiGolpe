# Provider Gate — Execution Authorization

## Not authorized yet

This repository contains only the non-network dry-run harness. Do **not** execute real provider calls until `docs/PROVIDER_GATE.md` records and the project owner approves:

- total spend ceiling;
- per-provider spend ceiling;
- credential/account ownership;
- execution environment;
- provider-specific retention/training policy for the exact plan and endpoint;
- result-storage location and access policy.

## Required invariants before real execution

- exactly 30 frozen benchmark cases;
- exactly three experimental phases per provider;
- no production traffic;
- no real user data;
- no API key in source control;
- results outside the public repository;
- automatic stop at the spend ceiling;
- automatic stop on any D1-D5 critical security failure;
- D6 recorded separately as exploratory.
