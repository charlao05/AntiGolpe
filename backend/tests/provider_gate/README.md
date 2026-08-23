# Provider Gate Sandbox

Este diretório é reservado ao experimento controlado de providers. Não deve ser importado por `backend/app/main.py` nem executado como parte do fluxo de produção.

## Estado atual

O sandbox está em **modo dry-run**. Ele não faz chamadas de rede, não importa SDKs de providers reais e não lê API keys.

Arquivos atuais:

- `runner.py` — carrega exatamente os 30 casos congelados e planeja as três fases experimentais.
- `adapters.py` — contrato provider-neutral; adapters externos permanecem bloqueados.
- `test_runner.py` — testes do dry-run e da trava de autorização.

## Fases planejadas

1. **Puro** — caso sem framework AntiGolpe.
2. **Framework** — caso com framework AntiGolpe.
3. **Framework + Structured Output** — framework com schema estruturado nativo, quando suportado.

Com 30 casos, o dry-run gera 90 execuções planejadas por provider. Com três providers, o experimento completo terá 270 execuções.

## Regra de segurança

A implementação de qualquer adapter real e qualquer chamada externa permanece bloqueada até que todas as decisões de governança e orçamento do `docs/PROVIDER_GATE.md` estejam fechadas e aprovadas.

Nenhum resultado do experimento deve ser persistido no repositório público. Resultados locais devem permanecer fora do Git ou em diretório explicitamente gitignored.
