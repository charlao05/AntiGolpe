# Fase 5.1 — Governança Pós-Merge e Preparação da Fase A

**Estado:** PREPARAÇÃO — execução real ainda bloqueada

**Base:** merge do PR #16 no `main`, commit `a7fece6093fd72035b07efe6bd860fe30e34dfd6`

**Data da verificação:** 2026-09-06

---

## 1. Objetivo

Registrar, após o merge da Fase 5.1, o que está implementado, o que foi validado e quais condições ainda precisam ser fechadas antes de qualquer execução real de provider.

Este documento não autoriza execução real e não altera o contrato congelado da Fase 5.1.

---

## 2. Estado técnico pós-merge

O PR #16 foi mesclado no `main` após CI e CodeQL verdes.

A implementação incorporada inclui:

- `SpendTracker` global e único para o experimento;
- tetos globais, por provider e por chamada;
- preflight financeiro antes da rede;
- contabilização pelo custo real;
- estados de execução e estados terminais irreversíveis;
- precedência de segurança sobre orçamento;
- `ExecutionOrchestrator` serial;
- adapter OpenAI sem autoridade financeira local;
- hooks de estimativa e custo real no protocolo provider-neutral;
- tratamento explícito de usage ausente/inválido;
- testes determinísticos para limites, estado, pré-rede, pós-rede e D1-D5.

Nenhuma chamada real foi executada pelo merge.

---

## 3. Separação de autoridades

### 3.1 Provider Gate — autoridade ambiental

O `ExecutionOrchestrator` consulta o Provider Gate, mas não ativa `CONFIRMED` nem cria autorização ambiental.

### 3.2 SpendTracker — autoridade financeira

O `SpendTracker` é a autoridade única para preflight e contabilização financeira. O adapter não possui um teto financeiro independente do experimento.

### 3.3 Safety Authority — autoridade de segurança

D1-D5 permanece fora da lógica financeira/orquestradora. Uma falha crítica de segurança pode produzir `SECURITY_ABORT` mesmo quando ainda existe orçamento.

### 3.4 ExecutionOrchestrator — executor subordinado

O Orchestrator coordena uma chamada por vez. Ele não define preços, não define os critérios D1-D5 e não ativa o Provider Gate.

---

## 4. `require_authorization()` no adapter

O adapter OpenAI mantém uma chamada defensiva a `require_authorization()` durante sua inicialização, antes da leitura da API key.

Essa chamada **não é a autoridade primária do experimento**. Ela existe como defesa em profundidade contra uso direto/indevido do adapter fora do fluxo autorizado.

A autoridade ambiental continua sendo o Provider Gate consultado pelo Orchestrator.

Esta duplicação deliberada deve ser preservada como barreira defensiva enquanto não houver decisão arquitetural posterior que a remova.

**Importante:** remover essa barreira sem uma substituta equivalente não é uma otimização aceitável.

---

## 5. Observação sobre a revisão externa

Uma revisão externa afirmou que o `OpenAIAdapter` exigiria `SpendTracker` injetado. O código mesclado não implementa essa afirmação: a autoridade financeira permanece no `SpendTracker` fornecido ao `ExecutionOrchestrator`, enquanto o adapter expõe somente estimativa e cálculo de custo real.

Portanto, essa afirmação deve ser tratada como divergência de leitura da versão anterior/da revisão, não como requisito a ser introduzido retroativamente.

---

## 6. `run_benchmark()`

Não implementar `run_benchmark()` no Orchestrator nesta fase.

O contrato arquitetural permanece:

- Orchestrator: executa uma chamada serial;
- Runner/Controller futuro: determina sequência, casos, modos e progressão;
- Governança: aprova a passagem entre Fases A, B e C.

Isso evita concentrar no Orchestrator responsabilidades de execução, planejamento experimental e governança.

---

## 7. Fase A — checklist de autorização

A Fase A consiste em exatamente:

**1 caso sintético × 1 provider × 1 chamada real.**

Antes da autorização humana, todos os itens abaixo devem estar VERDES:

### Código e segurança

- [x] PR #16 mesclado.
- [x] CI verde no commit que foi mesclado.
- [x] CodeQL verde no commit que foi mesclado.
- [x] Provider Gate continua desativado para execução real.
- [x] Nenhuma API key no Git.
- [x] Benchmark permanece sintético.
- [x] Nenhuma integração no runtime de produção.
- [x] Execução serial.
- [x] Sem retry automático.

### Governança

- [ ] Provider escolhido formalmente para a Fase A.
- [ ] Modelo exato registrado.
- [ ] Endpoint exato registrado.
- [ ] Plano/conta aplicável registrado.
- [ ] Política de retenção aplicável ao endpoint/plano verificada em fonte oficial.
- [ ] Uso para treinamento/melhoria verificado.
- [ ] ZDR, se aplicável, verificado quanto a elegibilidade e configuração real.
- [ ] Ambiente de execução definido fora do runtime de produção.
- [ ] Limite de gasto da conta/projeto configurado quando disponível.
- [ ] Limite local do harness confirmado.
- [ ] Procedimento de parada confirmado.

### Dados

- [ ] Caso escolhido pertence aos 30 fixtures congelados.
- [ ] Caso contém apenas dados sintéticos.
- [ ] Nenhuma PII real será enviada.
- [ ] Resultado não será persistido no Git.
- [ ] Logs não conterão API key, headers de autenticação ou payload bruto indevido.

### Aprovação

- [ ] Autorização humana explícita para ativar a execução real da Fase A.
- [ ] `CONFIRMED` somente depois de todos os itens anteriores.

---

## 8. Evidências de privacidade verificadas em 2026-09-06

Esta seção registra apenas o que foi encontrado nas fontes oficiais consultadas nesta data. Ela **não constitui aprovação de provider**.

### OpenAI API

A OpenAI informa que, por padrão, dados da organização enviados à plataforma de API não são usados para treinar ou melhorar os modelos. A documentação de privacidade empresarial também informa que, salvo determinados endpoints/recursos, entradas e saídas da API podem ser retidas por até 30 dias para prestação do serviço e detecção de abuso; ZDR existe para endpoints elegíveis e organizações qualificadas. A elegibilidade e o endpoint exatos usados no experimento ainda precisam ser registrados antes da Fase A.

Fontes oficiais consultadas:

- https://openai.com/pt-BR/business-data/
- https://openai.com/pt-BR/enterprise-privacy/
- https://openai.com/pt-BR/index/offering-zero-data-retention-for-frontier-models/

### Anthropic API

A Anthropic informa que, para usuários da API, entradas e saídas são automaticamente excluídas do backend em até 30 dias, salvo exceções como serviços com retenção mais longa, acordos diferentes (incluindo ZDR), exigências legais ou necessidades relacionadas à Política de Uso. A Anthropic também informa que acordos de ZDR dependem de elegibilidade e aprovação por organização. Modelos classificados pela Anthropic como Covered Models possuem regras especiais de retenção/revisão que precisam ser consideradas caso o modelo selecionado se enquadre nessa categoria.

Fontes oficiais consultadas:

- https://privacy.claude.com/pt/articles/7996866-por-quanto-tempo-voce-armazena-os-dados-da-minha-organizacao
- https://privacy.claude.com/pt/articles/8956058-tenho-um-acordo-de-retencao-zero-de-dados-com-a-anthropic-a-quais-produtos-ele-se-aplica
- https://privacy.claude.com/en/articles/15425996-data-retention-practices-for-covered-models

### Google Gemini API / Vertex AI

Para a Gemini API com faturamento, a documentação atual informa que os logs de chamadas podem ter retenção padrão máxima de 55 dias e que o registro de chamadas é separado dos logs mantidos apenas para monitoramento de abuso. A documentação também informa que, por padrão, prompts e respostas nos logs não são usados para melhoria/desenvolvimento de produto quando o logging está disponível para projetos com faturamento, mas há mecanismos de contribuição voluntária que podem mudar o tratamento.

Para Vertex AI, a documentação oficial informa restrição de treinamento: o Google não usará os dados para treinar ou ajustar modelos sem permissão ou instrução prévia do cliente, aplicável aos modelos gerenciados na Vertex AI.

**Decisão ainda pendente:** qual superfície será usada no benchmark: Gemini API ou Vertex AI.

Fontes oficiais consultadas:

- https://ai.google.dev/gemini-api/docs/logs-policy
- https://cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention

---

## 9. O que ainda não está fechado

Mesmo com as fontes oficiais consultadas, a Fase A continua bloqueada porque ainda falta transformar documentação geral em configuração experimental concreta:

1. escolher formalmente o provider da Fase A;
2. registrar modelo e endpoint exatos;
3. registrar plano/conta aplicável;
4. verificar a configuração efetiva de retenção/ZDR da conta escolhida;
5. configurar limites externos de gasto disponíveis;
6. definir o ambiente do harness;
7. preparar a chave fora do repositório;
8. revisar o caso sintético exato;
9. obter autorização humana explícita;
10. somente então ativar `CONFIRMED` e realizar uma única chamada.

---

## 10. Regra de parada da Fase A

Após a única chamada real, o experimento deve parar mesmo que:

- a resposta seja boa;
- o custo seja baixo;
- a latência seja aceitável;
- o Provider Gate permaneça saudável;
- não ocorra nenhuma falha de segurança.

O resultado precisa ser analisado antes de qualquer progressão para Fase B.

A Fase B continua condicionada a nova aprovação humana.

---

## 11. Proibição explícita

Até que a Seção 7 esteja integralmente marcada como concluída por decisão humana:

- não ativar `ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED`;
- não adicionar API keys ao repositório;
- não executar chamadas reais;
- não executar o benchmark de 270 chamadas;
- não integrar provider real ao runtime de produção.
