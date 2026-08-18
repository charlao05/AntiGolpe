# Arquitetura

## Camada 1 — determinística
Sanitização, normalização, schema, estado, rate limiting e protocolos.

## Camada 2 — raciocínio
`LLMProvider` é uma abstração substituível. O MVP usa `MockProvider` determinístico.

## Camada 3 — segurança
Valida schema e remove saídas proibidas. Nunca é um LLM.

## Frontend
HTML/CSS/JavaScript simples, mobile-first, sem framework pesado.

## Backend
FastAPI com endpoint `/api/analyze`, sem banco, sem acesso a URLs do usuário.

## Deploy
`render.yaml` fornece um serviço web Render básico. Provider real continua bloqueado pelo provider gate.
