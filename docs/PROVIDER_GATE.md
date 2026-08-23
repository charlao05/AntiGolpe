# Provider Gate — Contrato de Execução

## Objetivo

Comparar candidatos de LLM sem conectar nenhum provider real ao runtime de produção.

## Fases experimentais

1. **Puro:** modelo recebe o caso sem o framework AntiGolpe.
2. **Framework:** modelo recebe estados, critérios, instruções de decisão segura e formato AntiGolpe.
3. **Framework + Structured Output:** mesma configuração, com schema estruturado nativo quando suportado.

## Dados

- Exatamente os 30 casos congelados do benchmark.
- Nenhum dado real de usuário.
- Nenhuma chave de API em arquivos versionados.
- Execução somente em ambiente controlado separado da produção.

## Critérios

A ordem de decisão é:

**Segurança > Privacidade > Estrutura > Qualidade > Latência > Custo**

D1–D6 são critérios de segurança determinísticos definidos no Master Brief.
E1–E4 serão registrados como métricas de qualidade do experimento, sem substituir os gates de segurança.

## Governança obrigatória antes da execução

- teto de gasto explicitamente definido;
- conta e credenciais pertencentes ao operador;
- limites de gasto configurados no provider quando disponíveis;
- ambiente de execução identificado;
- local de armazenamento dos resultados identificado;
- política de retenção/uso de dados do modelo, plano e endpoint documentada.

## Regra de produção

Nenhum provider real será integrado ao `main.py`, ao Render ou ao fluxo de usuários até que o Provider Gate esteja concluído e aprovado.
