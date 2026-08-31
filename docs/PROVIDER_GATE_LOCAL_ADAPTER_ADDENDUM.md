# Provider Gate — Local Adapter Audit Addendum

> This addendum records the current code/documentation alignment while PR #14 remains under review. It does not authorize external execution.

## 20.6. Estado dos adapters locais

Os adapters reais locais coexistem com a infraestrutura provider-neutral. `adapters.py` continua sendo o contrato neutro; `openai_local_adapter.py` é um adapter real destinado exclusivamente à execução local explícita.

O adapter real:

- chama `require_authorization()` antes de ler `OPENAI_API_KEY`;
- falha fechado sem `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED`;
- não é importado pelo runtime de produção nem pelo CI padrão;
- limita a saída com `max_completion_tokens=800`;
- executa uma estimativa conservadora de custo máximo antes da chamada;
- registra o custo efetivamente retornado depois da chamada como circuit breaker do loop.

O `SpendTracker` não deve ser descrito como hard cap de faturamento. O preflight local é uma barreira de execução baseada em estimativa; limites e alertas do provider permanecem uma camada independente e necessária.

### Pricing congelado para o adapter OpenAI atual

Para `gpt-4o-mini` no endpoint Chat Completions, as tarifas verificadas na documentação oficial em 2026-08-30 são US$ 0,15 por 1M tokens de entrada e US$ 0,60 por 1M tokens de saída. O modelo documenta suporte a Chat Completions e `max_completion_tokens` é o parâmetro atual para limitar tokens de saída nesse endpoint.

Esses valores são usados pelo adapter como estimativa local e devem continuar vinculados à versão/modelo/endpoint do experimento. Não constituem contabilidade final de faturamento.

## 20.7. Protocolo de avaliação cega

A identidade real do provider não deve ser entregue aos avaliadores antes das notas E1-E4.

O fluxo obrigatório é:

```text
Provider real
    ↓
ID interno / Provider_A, Provider_B, Provider_C
    ↓
execution_results.json (sem identidade real)
    ↓
avaliadores independentes → E1-E4
    ↓
notas congeladas
    ↓
mapping_key.json separado
    ↓
desclassificação / custo / decisão final
```

Regras:

- `execution_results.json` não contém `openai`, `anthropic`, `google` ou o nome/modelo real no campo de identificação entregue aos avaliadores;
- `mapping_key.json` permanece fora dos artefatos de avaliação e é coberto pelo `.gitignore`;
- a chave de mapeamento só é revelada depois que E1-E4 estiverem registradas;
- metadados que possam revelar indiretamente a identidade do provider devem ser revisados antes da entrega aos avaliadores;
- retries técnicos são marcados separadamente e não alteram a amostra principal.

## Estado

Este addendum formaliza o desenho de execução e avaliação. Ele não altera a regra de que `CONFIRMED` permanece desligado até a aprovação completa do Provider Gate.
