# Fase 5.1 — Addendum de Governança de Providers — 2026-09-08

**Estado:** INFORMATIVO / NÃO AUTORIZA EXECUÇÃO REAL

Este addendum atualiza evidências públicas oficiais consultadas em 2026-09-08. Ele não escolhe provider, não configura conta/projeto e não altera `CONFIRMED`.

## 1. OpenAI — snapshot exato

A documentação oficial atual de controles de dados da OpenAI informa que a API, por padrão, não usa dados enviados para treinar ou melhorar modelos, salvo opt-in. Também informa que logs de monitoramento de abuso podem reter conteúdo por até 30 dias por padrão e que Zero Data Retention exige aprovação/configuração da organização.

Para `/v1/chat/completions`, a tabela oficial de controles lista explicitamente `gpt-4o-mini-2024-07-18` entre os snapshots compatíveis com Zero Data Retention.

O modelo `gpt-4o-mini-2024-07-18` continua listado como snapshot disponível do GPT-4o mini, com preço oficial atual de US$ 0,15/M tokens de entrada e US$ 0,60/M tokens de saída.

**Conclusão operacional:** o snapshot exato registrado anteriormente está tecnicamente compatível com a exigência de ZDR no endpoint pretendido, mas isso não prova que a organização/projeto do experimento esteja aprovado e configurado para ZDR. Essa configuração efetiva continua pendente.

Fontes oficiais:
- https://platform.openai.com/docs/models/default-usage-policies-by-endpoint
- https://developers.openai.com/api/docs/models/gpt-4o-mini
- https://openai.com/index/offering-zero-data-retention-for-frontier-models/

## 2. Anthropic — Haiku 4.5

A Anthropic informa atualmente que usuários da API, em regime padrão, têm inputs/outputs excluídos do backend em até 30 dias, salvo acordos diferentes, necessidades legais ou de política de uso. A empresa também informa que ZDR existe para clientes aprovados/elegíveis.

O preço oficial publicado para Claude Haiku 4.5 é US$ 1/M tokens de entrada e US$ 5/M tokens de saída.

**Conclusão operacional:** o modelo e o preço podem ser registrados como candidatos, mas a elegibilidade/configuração de retenção da conta experimental ainda não está comprovada. Além disso, a governança deve verificar se o modelo escolhido está sujeito a uma política especial de retenção/cobertura no momento da execução.

Fontes oficiais:
- https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data
- https://www.anthropic.com/news/claude-haiku-4-5
- https://www.anthropic.com/transparency/voluntary-commitments

## 3. Google — modelo exato e superfície

A documentação atual do Gemini Developer API lista `gemini-2.5-flash-lite` como modelo estável e econômico, com preço de US$ 0,10/M tokens de entrada e US$ 0,40/M tokens de saída no nível pago padrão.

A mesma documentação informa que a versão `gemini-2.0-flash-lite` foi desativada em 1º de junho de 2026, portanto ela não deve ser usada como candidato atual do benchmark.

A política atual de logs do Gemini API informa retenção padrão máxima de 55 dias para logs de projetos com faturamento, com janela configurável de 7, 14, 28 ou 55 dias. A política também distingue esses logs de registros usados apenas para monitoramento de abuso.

A documentação de Interactions API informa que interações armazenadas (`store=true`) podem permanecer por até 55 dias no nível pago; `store=false` desativa esse armazenamento de interação, quando aplicável.

**Decisão ainda aberta:** Gemini Developer API versus Vertex AI. O benchmark não deve registrar "Google" genericamente: deve registrar superfície, projeto, modelo exato e política de retenção aplicável.

Fontes oficiais:
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/logs-policy
- https://ai.google.dev/gemini-api/docs/interactions-overview

## 4. Matriz atualizada de evidência

| Provider | Candidato | Preço base atual | Retenção pública relevante | Configuração concreta comprovada? | Estado |
|---|---|---:|---|---|---|
| OpenAI | `gpt-4o-mini-2024-07-18` | $0,15/M input; $0,60/M output | ZDR elegível no `/v1/chat/completions`; padrão pode ter abuso até 30 dias | Não | Pendente de configuração/aprovação |
| Anthropic | `claude-haiku-4-5` | $1/M input; $5/M output | API padrão até 30 dias; ZDR por acordo/elegibilidade | Não | Pendente de configuração/aprovação |
| Google | `gemini-2.5-flash-lite` | $0,10/M input; $0,40/M output | Gemini API: logs até 55 dias; `store=false` depende da superfície/API usada | Não | Pendente de superfície/projeto |

## 5. O que esta pesquisa resolve

- Confirma novamente o snapshot exato da OpenAI que é compatível com ZDR no endpoint planejado.
- Atualiza os preços dos três candidatos em fontes oficiais.
- Elimina `gemini-2.0-flash-lite` como candidato atual, pois foi desativado em 2026-06-01.
- Define `gemini-2.5-flash-lite` como candidato atual economicamente compatível com o benchmark, sem afirmar que ele foi escolhido.
- Reforça que "provider escolhido" e "política pública do provider" são coisas diferentes de "conta/projeto configurado".

## 6. O que continua impossível fechar apenas por pesquisa pública

Não é possível, apenas por documentação pública, provar que a conta/projeto específico que será usado no experimento está:

1. aprovado para ZDR quando essa aprovação é exigida;
2. configurado com a política de retenção desejada;
3. com limites externos de gasto efetivamente aplicados;
4. usando o endpoint/modelo exatos pretendidos;
5. sem configurações adicionais que alterem retenção ou armazenamento.

Esses itens exigem verificação dentro das respectivas contas/projetos e decisão humana. Nenhum deles deve ser inferido a partir da documentação geral.

## 7. Regra de segurança

Este addendum **não** autoriza:

- `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED`;
- leitura ou criação de API key para o benchmark;
- chamada externa;
- Fase A;
- Fase B;
- benchmark de 270 chamadas;
- integração com runtime de produção.
