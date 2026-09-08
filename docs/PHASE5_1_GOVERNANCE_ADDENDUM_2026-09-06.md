# Fase 5.1 — Addendum de Governança e Verificação Técnica

**Data:** 2026-09-06

**Base:** `phase5-postmerge-governance`, PR #18

Este addendum registra verificações feitas após a revisão externa do PR #16. Não autoriza execução real e não altera o contrato congelado da Fase 5.1.

## 1. OpenAI — elegibilidade ZDR do modelo escolhido

A revisão externa levantou uma dúvida correta: o anúncio da OpenAI de 19/08/2026 sobre ZDR para modelos de fronteira não bastava, sozinho, para concluir que `gpt-4o-mini` estava coberto.

A verificação adicional foi feita na documentação oficial de controles de dados da API.

A tabela oficial de suporte de `/v1/chat/completions` lista explicitamente o snapshot `gpt-4o-mini-2024-07-18` entre os modelos compatíveis com Zero Data Retention. A mesma documentação explica que ZDR exige aprovação prévia e configuração de controle de retenção na organização/projeto.

Conclusão:

- a dúvida sobre a aplicabilidade de ZDR ao GPT-4o mini foi resolvida positivamente **para o snapshot explicitamente listado**;
- isso não significa que a conta/projeto do experimento já esteja aprovada ou configurada para ZDR;
- para reprodutibilidade e governança, o experimento deve registrar/pinar o snapshot exato aprovado, em vez de depender apenas do alias `gpt-4o-mini`;
- a aprovação/configuração efetiva da organização/projeto continua pendente.

Fonte oficial consultada em 2026-09-06:

- OpenAI — Data controls in the OpenAI platform: `https://platform.openai.com/docs/models/default-usage-policies-by-endpoint`

## 2. Verificação do código sugerido para Fase A

O runner sugerido na revisão externa **não deve ser aplicado como está**.

A inspeção do código real do `main` confirmou as seguintes assinaturas:

- `OpenAIAdapter.__init__(model="gpt-4o-mini")`;
- `SpendTracker.__init__(*, global_ceiling, provider_ceiling, per_call_ceiling)`;
- `ExecutionOrchestrator.__init__(*, providers, spend_tracker, safety_authority, incident_recorder=None, authorization_check=require_authorization)`;
- a unidade de execução é `ExecutionOrchestrator.execute_one(...)`, e não `run(...)`;
- `execute_one()` exige um `SafetyAuthority` com método `evaluate(response) -> bool`.

Portanto, o pseudo-runner externo que usa `provider=`, `safety_layer=` e `orchestrator.run(...)` é incompatível com a implementação atual e **não será incorporado**.

Isso é uma correção deliberada de segurança: não introduzimos código operacional baseado em interfaces inferidas sem validação do repositório.

## 3. Bloqueio técnico adicional identificado antes da Fase A

A inspeção também mostrou que o `SafetyEngine` existente em `backend/app/safety.py` não implementa diretamente a interface `SafetyAuthority` exigida pelo Orchestrator. Ele expõe `validate(...)`, enquanto o Orchestrator exige `evaluate(ProviderResponse) -> bool`.

Isso não é um defeito do PR #16: o contrato de Fase 5.1 já exige uma autoridade de segurança separada. Porém, significa que **a integração operacional da Fase A ainda precisa definir/adaptar formalmente a autoridade D1-D5** antes de qualquer chamada real.

Não devemos simplesmente passar `SafetyEngine` ao Orchestrator por conveniência.

## 4. Benchmark e localização

O benchmark congelado continua em:

`tests/fixtures/benchmark_cases.json`

O harness dry-run existente já referencia corretamente esse caminho a partir de `backend/tests/provider_gate/runner.py` e continua sem rede, sem SDK de provider e sem leitura de API keys.

## 5. Decisões mantidas

- `run_benchmark()` permanece fora do Orchestrator.
- `SpendTracker` continua exclusivamente no Orchestrator como autoridade financeira.
- A chamada defensiva de `require_authorization()` no adapter permanece como defesa em profundidade.
- `CONFIRMED` permanece desligado.
- Nenhuma chamada real será feita até que governança, configuração e integração da Safety Authority estejam fechadas.

## 6. Estado após este addendum

### Resolvido

- dúvida sobre ZDR do GPT-4o mini: resolvida para o snapshot oficial explicitamente listado;
- assinaturas reais do adapter, tracker e Orchestrator: verificadas;
- incompatibilidades do runner sugerido: identificadas e rejeitadas antes de implementação;
- localização do benchmark: verificada.

### Pendente

1. decidir e registrar o snapshot exato do modelo OpenAI;
2. confirmar aprovação/configuração ZDR da organização/projeto, se essa for a política escolhida;
3. fechar provider, endpoint e conta da Fase A;
4. definir a implementação/adaptação formal da `SafetyAuthority` D1-D5 para a execução do benchmark;
5. configurar limite externo de gasto quando disponível;
6. obter autorização humana explícita;
7. somente então preparar e executar exatamente uma chamada da Fase A.

**Este addendum não autoriza execução.**
