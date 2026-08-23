# Fase 4.0 — Hygiene Gate

Objetivo: manter a `main` limpa e confiável antes de qualquer integração de LLM real.

## Escopo

- Corrigir a construção da URL OData do utilitário `backend/tools/pix_fraud_trends.py`.
- Adicionar teste unitário específico para a URL construída.
- Avaliar PRs do Dependabot individualmente.
- Executar CI e CodeQL antes do merge.
- Não alterar o benchmark congelado.
- Não integrar provider real.
- Não alterar a arquitetura de produção.

## Resultado esperado

`main` sem bugs conhecidos identificados nesta auditoria, CI verde e dependências pendentes tratadas conscientemente.
