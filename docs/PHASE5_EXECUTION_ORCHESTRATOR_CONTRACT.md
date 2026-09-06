# PHASE5_EXECUTION_ORCHESTRATOR_CONTRACT.md

## 0. Natureza deste documento

Este e um contrato de especificacao, nao uma implementacao. Nenhuma linha de codigo deve ser escrita a partir dele antes de aprovacao explicita do conteudo. Qualquer implementacao futura (SpendTracker, ExecutionOrchestrator, adapters) deve ser auditada contra este documento, nao o contrario.

Status: FROZEN / APROVADO PARA IMPLEMENTACAO.

## 0.1 Principio fundamental de subordinacao

O ExecutionOrchestrator nao e uma autoridade de seguranca.

Ele e um executor subordinado a politicas deterministicas ja aprovadas em outros contratos (PROVIDER_GATE.md, D1-D5/D6, SECURITY.md). O Orchestrator:

- NAO decide o que e seguro - apenas aplica decisoes ja tomadas.
- NAO pode reinterpretar, suavizar, ignorar ou "votar" sobre um bloqueio de seguranca.
- NAO pode conceder a si mesmo, a um adapter, ou a um LLM, autoridade para contornar D1-D5.
- Qualquer ambiguidade na aplicacao de uma regra de seguranca deve resultar em bloqueio (fail-closed), nunca em interpretacao permissiva.

Esta clausula e hierarquicamente superior a qualquer outra secao deste documento. Em caso de conflito aparente entre eficiencia de execucao e uma regra de seguranca, a regra de seguranca prevalece sempre.

## 1. Objetivo

Criar um controlador unico de execucao experimental responsavel por:

1. Autorizar cada chamada antes da rede (preflight financeiro e de seguranca).
2. Controlar orcamento global.
3. Controlar orcamento por provider.
4. Registrar gasto real pos-chamada.
5. Interromper a execucao imediatamente ao atingir qualquer limite (financeiro ou de seguranca).
6. Impedir execucao paralela (nesta fase).
7. Executar inicialmente apenas um caso sintetico isolado.
8. Preservar avaliacao cega (blind evaluation).
9. Impedir que resultados de experimento contaminem o repositorio Git.

Clausula de nao-autoridade: o Orchestrator nao autoriza sozinho execucao real. A autorizacao de ambiente continua pertencendo exclusivamente ao Provider Gate (CONFIRMED=ANTIGOLPE_PROVIDER_GATE_AUTHORIZED). O Orchestrator apenas opera dentro de um ambiente ja autorizado - nunca substitui essa autorizacao, nunca a simula, nunca a antecipa.

## 2. Governanca financeira - hierarquia dos limites

### 2.1 Estrutura hierarquica

```
                 GLOBAL
                US$ 10,00
                    |
        +-----------+-----------+
        |           |           |
     OpenAI      Provider B   Provider C
     <= $3,00      <= $3,00     <= $3,00
```

Cada chamada individual esta sujeita adicionalmente a um teto por chamada.

### 2.2 Regra de precedencia

```
limite da chamada
        -> limite do provider
                -> limite global
                        -> autorizacao do Provider Gate
                                -> chamada externa
```

Nenhum nivel inferior pode aumentar um limite superior.

### 2.3 Configuracao explicita e fechada

```
GLOBAL_CEILING   = US$ 10,00
PROVIDER_CEILING = US$ 3,00
PER_CALL_CEILING = US$ 0,50
```

Estes tres valores compoem a configuracao fechada do experimento nesta fase. Nenhum e opcional, nenhum tem default implicito.

### 2.4 Rejeicao de configuracao incompleta

O Orchestrator deve rejeitar a inicializacao da execucao caso qualquer um dos tres limites esteja ausente, invalido (nao numerico, negativo, zero) ou inconsistente (ex.: PROVIDER_CEILING > GLOBAL_CEILING, ou PER_CALL_CEILING > PROVIDER_CEILING). Nesse caso, o estado resultante e CONFIGURATION_ERROR, nunca um valor default silencioso.

### 2.5 Imutabilidade dos limites durante a execucao

Apos o inicio da execucao experimental (transicao para AUTHORIZED/RUNNING), os limites financeiros efetivos (GLOBAL_CEILING, PROVIDER_CEILING, PER_CALL_CEILING) sao imutaveis. Qualquer tentativa de alteracao em tempo de execucao resulta em CONFIGURATION_ERROR e STOP GLOBAL imediato.

## 3. SpendTracker GLOBAL

### 3.1 Unicidade

Deve existir uma unica instancia de SpendTracker por execucao experimental completa. E proibida a existencia de trackers independentes por provider.

```
                 Execution
                    |
           SpendTracker GLOBAL
             /       |       \
            /        |        \
       OpenAI      Claude    Gemini
```

### 3.2 Estado minimo obrigatorio

- global_spend
- provider_spend[provider]
- call_count
- provider_call_count[provider]
- state (ver secao 6)

### 3.3 Separacao de responsabilidades temporais

- Pre-autorizacao (secao 4): responde "esta chamada pode comecar?"
- Registro pos-chamada (secao 5): responde "quanto realmente gastamos?"
- Estado global (secao 6): responde "a execucao inteira ainda pode continuar?"
- Falha de seguranca (secao 7): interrompe independentemente do saldo disponivel.

Estas quatro funcoes sao conceitualmente distintas e nao devem ser fundidas em uma unica verificacao generica.

## 4. Pre-autorizacao (preflight)

```
request
  -> validar execucao (estado != terminal)
  -> validar estado do orquestrador
  -> validar provider (existe, configurado, sem cooldown de falha)
  -> estimar pior caso (custo maximo possivel da chamada)
  -> SpendTracker.authorize(provider, estimated_worst_case)
  -> SIM: chamada autorizada a prosseguir para o adapter
  -> NAO: bloqueia, NENHUMA chamada de rede ocorre
```

### 4.1 Formula explicita de autorizacao

SpendTracker.authorize(provider, estimated_worst_case) so retorna positivo se TODAS as condicoes abaixo forem verdadeiras simultaneamente:

```
global_spend    + estimated_worst_case <= GLOBAL_CEILING
provider_spend  + estimated_worst_case <= PROVIDER_CEILING
estimated_worst_case                   <= PER_CALL_CEILING
```

Nao existe conceito de "saldo residual suficiente" isolado - a soma projetada (gasto atual + estimativa de pior caso) e o que deve respeitar cada teto. Um saldo remanescente de US$ 0,40 nao autoriza uma chamada estimada em US$ 0,50.

### 4.2 Ausencia de reserva concorrente

Como a execucao e estritamente serial (secao 6.4), nao ha necessidade de mecanismo de reserva/lock para chamadas concorrentes. A autorizacao concedida e consumida imediatamente pela chamada em curso antes de qualquer outra avaliacao de preflight ocorrer.

### 4.3 Regra de rede

A chamada de rede nao pode ocorrer antes da autorizacao financeira ser concedida.

## 5. Registro pos-chamada

```
provider response
       -> extrair usage real (tokens de entrada/saida reportados pelo provider)
       -> calcular custo real
       -> SpendTracker.register(provider, real_cost)
       -> atualizar global_spend
       -> atualizar provider_spend[provider]
```

### 5.1 Regra de precedencia contabil

O custo real, extraido da resposta do provider, sempre prevalece sobre a estimativa para fins de contabilizacao definitiva.

- A estimativa (secao 4) e barreira preventiva - usada apenas para decidir se a chamada pode comecar.
- O usage real (secao 5) e contabilidade - usado para atualizar o estado definitivo do tracker.

Nunca o inverso: a estimativa nunca substitui o registro real ja obtido.

### 5.2 Falha na obtencao de usage

Se o provider nao retornar dados de usage suficientes para calcular o custo real de forma confiavel (ausentes, incompletos, ou inconsistentes), o Orchestrator nao pode assumir custo zero nem estimativa como substituto silencioso. Nesse caso:

- Se a causa for atribuivel ao provider (resposta malformada, falha de parsing): estado -> PROVIDER_FAILURE.
- Se a causa for atribuivel a configuracao do adapter/orquestrador (ex.: mapeamento de preco ausente para o modelo): estado -> CONFIGURATION_ERROR.

Em ambos os casos: STOP GLOBAL. A integridade financeira do sistema depende de nunca tratar "custo desconhecido" como "custo zero".

## 5.3 Separacao entre falhas pre-rede e pos-rede

### 5.3.1 Falhas pre-rede (nenhuma chamada ocorre)

- Configuracao invalida ou incompleta (secao 2.4).
- Orcamento insuficiente identificado no preflight (secao 4.1).
- Provider Gate nao autorizado (CONFIRMED ausente).
- Provider inexistente ou nao configurado.

Consequencia: a chamada nunca e disparada. Nenhum gasto e registrado. Estado apropriado: BLOCKED, SPEND_LIMIT_REACHED ou CONFIGURATION_ERROR, conforme a causa.

### 5.3.2 Falhas pos-rede (a chamada ja ocorreu)

- Timeout de rede.
- Erro HTTP retornado pelo provider.
- Resposta invalida ou malformada.
- Usage ausente ou nao confiavel (secao 5.2).
- Falha de parsing da resposta.

Consequencia: o incidente deve ser registrado (mesmo que o custo real nao possa ser determinado com precisao, o proprio fato da chamada e seu contexto devem constar no log de auditoria). Estado apropriado: PROVIDER_FAILURE (falha do lado do provider) ou CONFIGURATION_ERROR (falha do lado do nosso proprio adapter/orquestrador). Em qualquer caso: STOP GLOBAL.

Esta distincao e obrigatoria nos testes: cenarios pre-rede devem provar "zero chamadas disparadas"; cenarios pos-rede devem provar "registro correto do incidente antes da parada".

## 6. Orquestracao - maquina de estados

### 6.1 Ciclo de vida normal

```
READY -> AUTHORIZED -> RUNNING -> COMPLETED
```

Esclarecimento de AUTHORIZED: este estado significa exclusivamente que uma chamada especifica recebeu autorizacao previa do SpendTracker para prosseguir. Nao constitui autorizacao permanente ou cumulativa da execucao. Cada nova chamada - mesmo dentro da mesma execucao - deve passar novamente pelo ciclo de preflight (secao 4) e obter sua propria autorizacao individual antes de prosseguir para RUNNING. E proibida qualquer implementacao em que uma autorizacao unica habilite multiplas chamadas subsequentes sem novo preflight.

### 6.2 Estados terminais de interrupcao

```
BLOCKED
SPEND_LIMIT_REACHED
SECURITY_ABORT
PROVIDER_FAILURE
CONFIGURATION_ERROR
```

### 6.3 Regra de irreversibilidade

Uma vez atingido qualquer estado terminal (seja de seguranca, seja de orcamento):

```
STOP
```

O orquestrador nao reinicia, nao tenta outro provider, nao segue para o proximo caso. A execucao experimental completa e encerrada. Retomar requer intervencao humana explicita e nova autorizacao, fora do escopo automatizado do Orchestrator.

### 6.4 Execucao serial (obrigatoria nesta fase)

```
case 001 -> provider -> resultado -> controle -> case 002
```

Zero paralelismo. E proibido executar multiplos casos, multiplos providers ou multiplas chamadas simultaneamente nesta fase. Justificativa: contabilizacao auditavel, parada imediata deterministica, reprodutibilidade, investigacao de incidentes sem concorrencia de estado. Paralelismo pode ser discutido em fase futura, nunca nesta.

## 7. Seguranca - D1-D5 como bloqueios criticos

### 7.1 Precedencia absoluta

A seguranca e hierarquicamente superior ao orcamento.

```
D1-D5 failure -> SECURITY_ABORT -> STOP GLOBAL
```

Isso vale mesmo que ainda exista orcamento disponivel (ex: mesmo com US$ 9,80 de saldo global restante). E explicitamente proibida qualquer logica equivalente a "a chamada violou uma regra de seguranca, mas ainda temos orcamento, entao continuamos". Essa condicao nunca deve ser verdadeira no sistema.

### 7.2 Nao contornabilidade

- O Orchestrator nao pode reclassificar uma falha D1-D5 como aviso (warning).
- O Orchestrator nao pode delegar a decisao de continuar/parar apos um SECURITY_ABORT a um LLM, a um adapter, ou a qualquer componente de nivel inferior.
- Nao existe modo de "retry apos falha de seguranca" automatizado.

### 7.3 D6

D6 permanece conforme o contrato anterior ja estabelecido: tratado como exploratorio e registrado separadamente, fora do fluxo de bloqueio critico D1-D5.

## 8. Experimento - progressao controlada

### 8.1 Fases de execucao

```
FASE A
1 caso sintetico . 1 provider . 1 chamada

FASE B (somente apos aprovacao humana dos resultados da Fase A)
1 caso sintetico . 3 providers . 3 chamadas

FASE C - benchmark completo (somente apos aprovacao humana dos resultados da Fase B)
30 casos x 3 modos experimentais x 3 providers = 270 chamadas
```

Nota terminologica: "Fase A/B/C" refere-se exclusivamente a progressao de escopo do experimento. "Modos experimentais" refere-se as 3 variacoes metodologicas aplicadas a cada caso dentro da Fase C. Estes dois conceitos nao devem ser usados de forma intercambiavel em nenhuma implementacao ou teste.

Nenhuma fase avanca automaticamente para a proxima. Cada transicao exige aprovacao humana explicita.

### 8.2 Subordinacao financeira permanente

Mesmo a Fase C permanece integralmente subordinada aos tetos definidos na secao 2. Nenhuma fase, incluindo a mais avancada, dispensa a hierarquia financeira ou a autorizacao do Provider Gate.

## 9. Avaliacao cega (blind evaluation)

### 9.1 Separacao de identidade

O Orchestrator recebe internamente provider_real (ex.: "OpenAI"), mas o artefato destinado ao avaliador recebe apenas identificadores neutros:

```
Provider_A
Provider_B
Provider_C
```

O mapping fica separado em arquivo distinto:

```
execution_results.json -> Provider_A / Provider_B / Provider_C
mapping_key.json       -> Provider_A -> OpenAI, etc.
```

O avaliador nunca recebe o mapping_key.json.

### 9.2 Regra de independencia do avaliador

O orquestrador nunca deve depender do nome real do provider para calcular a avaliacao. Isso reduz o risco de vazamento acidental de identidade.

### 9.3 Persistencia

Os resultados reais nao entram no Git. Categorias distintas, todas fora do repositorio e com acesso controlado:

- Dados de execucao: execution_results.json
- Chave de identidade: mapping_key.json
- Metricas financeiras/tecnicas: cost_report.json, latency_report.json

### 9.4 O que o Orchestrator NAO pode fazer

Ele nao podera:

- ativar CONFIRMED;
- buscar API key;
- alterar configuracao de provider;
- alterar teto financeiro;
- ignorar SpendTracker;
- executar provider diretamente;
- executar em paralelo;
- gravar segredo;
- gravar prompt/resposta em log publico;
- alterar benchmark congelado;
- inserir resultados reais no Git;
- transformar falha de seguranca em warning.

## 14. Separacao de poderes arquitetural

```
Provider Gate
      |
autoridade de execucao real (autoriza o ambiente)

SpendTracker
      |
autoridade financeira (autoriza/nega cada chamada por orcamento)

D1-D5 / Safety Layer
      |
autoridade de seguranca (bloqueia incondicionalmente)

ExecutionOrchestrator
      |
executor subordinado (nao decide, apenas aplica e coordena)
```

### 14.1 Regra de nao-concentracao de poder

O Orchestrator nao e autoridade de seguranca (secao 0.1) nem autoridade financeira. Ele coordena a sequencia de chamadas e consulta cada autoridade na ordem apropriada, mas:

- Nao pode aprovar uma chamada que o SpendTracker rejeitou.
- Nao pode prosseguir apos um SECURITY_ABORT da Safety Layer.
- Nao pode iniciar execucao sem autorizacao do Provider Gate.
- Nao possui logica propria de decisao financeira ou de seguranca - apenas invoca as autoridades correspondentes e obedece ao resultado.

Esta separacao e a garantia estrutural de que nenhum componente unico pode, isoladamente, autorizar uma execucao real.

## 15. Historico de aprovacao

- Minuta inicial redigida e revisada em quatro eixos: governanca financeira, orquestracao, seguranca, experimento.
- Sete ajustes de precisao incorporados: correcao de nomenclatura Fase C, fechamento do PER_CALL_CEILING em US$ 0,50, formula explicita de preflight, tratamento de usage ausente como falha (nunca custo zero), separacao falhas pre-rede/pos-rede, esclarecimento do estado AUTHORIZED, imutabilidade dos limites durante a execucao.
- Extensao arquitetural incorporada: separacao de poderes entre Provider Gate, SpendTracker, Safety Layer e ExecutionOrchestrator (secao 14).
- Status final: FROZEN / APROVADO PARA IMPLEMENTACAO.
- Este documento antecede e delimita qualquer codigo da Fase 5.1 (SpendTracker, ExecutionOrchestrator, adapters). Nenhuma implementacao foi iniciada nesta branch alem deste contrato.
