# Provider Gate Sandbox

Este diretório é reservado ao experimento controlado de providers. Não deve ser importado por `backend/app/main.py` nem executado como parte do fluxo de produção.

## Estado atual

O sandbox permanece **bloqueado por padrão**. A infraestrutura neutra não faz chamadas de rede. O único adapter real atualmente presente é `openai_local_adapter.py`, destinado exclusivamente à execução local explícita e protegido por `guard.py`.

O adapter real:

- exige `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED` antes de ler `OPENAI_API_KEY`;
- não é importado pelo runtime de produção nem pelo CI padrão;
- limita a saída com `max_completion_tokens` e aplica pré-verificação conservadora de custo;
- registra o custo real retornado pelo provider como circuit breaker pós-chamada;
- não deve ser tratado como substituto dos limites de cobrança do provider.

Arquivos principais:

- `runner.py` — carrega exatamente os 30 casos congelados e planeja as três fases experimentais.
- `adapters.py` — contrato provider-neutral e `ProviderResponse`.
- `openai_local_adapter.py` — adapter OpenAI real, local e fail-closed.
- `guard.py` — autorização explícita para adapters reais.
- `test_runner.py` — testes do dry-run e da trava provider-neutral.
- `test_openai_local_adapter.py` — regressões da trava fail-closed e do preflight de custo.
- `scoring.py` — estruturas D1-D6/E1-E4, sem julgamento automático nesta fase.
- `cost_model.py` — estrutura provider-neutral de custos.
- `latency.py` — estrutura provider-neutral de latência.
- `SECURITY.md` — regras de segurança do sandbox.
- `NOTES.md` — estado de governança.
- `PLAN.md` — plano do experimento.

## Fases planejadas

1. **Puro** — caso sem framework AntiGolpe.
2. **Framework** — caso com framework AntiGolpe.
3. **Framework + Structured Output** — framework com schema estruturado nativo, quando suportado.

Com 30 casos, o dry-run gera 90 execuções planejadas por provider. Com três providers, o experimento completo terá 270 execuções.

## Regra de segurança

A existência do adapter real não autoriza execução. Qualquer chamada externa continua bloqueada até que todas as decisões de governança e orçamento do `docs/PROVIDER_GATE.md` estejam fechadas e aprovadas.

`CONFIRMED` permanece desligado por padrão. Nenhum resultado do experimento deve ser persistido no repositório público. Resultados locais devem permanecer fora do Git ou em diretório explicitamente gitignored.
