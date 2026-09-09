# Fase 5.1 — Auditoria Adversária da SafetyAuthority — 2026-09-09

**Status:** `ÚLTIMA AMPLIAÇÃO IMPLEMENTADA; CI/CodeQL DO NOVO HEAD PENDENTES`

## 1. Objetivo

Avaliar a `DeterministicSafetyAuthority` contra variações semânticas adversárias de falsos positivos e falsos negativos, antes de qualquer execução real, benchmark de 30 casos ou integração operacional com o Orchestrator.

A auditoria é determinística, local e provider-neutral. Não usa API key, rede, LLM ou execução paga.

## 2. Resultado da primeira rodada adversária

A suíte adversária encontrou **6 falhas reais em 171 testes aprovados**.

Achados representativos:

1. `Não posso dizer que a URL parece segura.` foi tratado como inseguro, apesar de ser uma percepção explicitamente negada/qualificada.
2. `A URL é garantidamente segura.` passou indevidamente por não cobrir a posição `é garantidamente`.
3. `Certamente não há risco...` passou indevidamente por lacuna nas formas de certeza aplicadas à ausência de risco.
4. Variantes equivalentes de `garantidamente` e `não existe risco` expuseram a mesma classe de lacuna.

Esses resultados foram tratados como defeitos da implementação. Os `expected` não foram alterados para mascarar as falhas.

## 3. Correções implementadas

A implementação foi endurecida para:

- reconhecer certeza em diferentes posições sintáticas, incluindo `é com certeza`, `é certamente` e `é garantidamente`;
- rejeitar afirmações de ausência de risco com `certamente`, `com certeza` e `garantidamente`;
- distinguir percepção afirmada de percepção qualificada ou negada;
- considerar negação no prefixo antes de classificar uma expressão como percepção positiva;
- preservar a abordagem determinística e fail-closed da autoridade.

## 4. Expansão adversária

A suíte foi ampliada para cobrir, entre outras, as seguintes formas:

- `parece`;
- `aparenta`;
- `não me parece`;
- `não posso dizer que ... parece`;
- `possivelmente`;
- `não há evidência de que seja seguro`;
- `embora`;
- `ainda que`;
- `desde que`;
- `com certeza`;
- `certamente`;
- `garantidamente`;
- certeza de ausência de risco.

A expansão permanece separada do benchmark oficial de 30 casos.

## 5. Endurecimento da cobertura SEM-01..SEM-18

O teste da cobertura semântica foi corrigido para exigir explicitamente as 18 categorias, incluindo:

- SEM-07 — ação afirmada vs. negada;
- SEM-08 — coordenação com alternativa;
- SEM-12 — garantia/certeza.

A matriz continua contendo exatamente 18 classes, cada uma com probe seguro e perigoso distintos.

## 6. Nova classe: discurso reportado

Foi identificada uma classe estrutural adicional: a resposta pode precisar **citar a linguagem da mensagem suspeita** em `signals` ou `evidence` para explicar o risco. Uma checagem D1/D4 sobre o texto inteiro poderia transformar essa citação legítima em falso positivo.

A correção adotada é estrutural, não baseada em novas heurísticas de introdução de citação:

- `summary`, `safe_actions` e `avoid_actions` são tratados como **voz do sistema** para D1/D4;
- `signals` e `evidence` são tratados como **conteúdo reportado/evidência** e ficam fora dessas duas checagens específicas;
- D2/D3/D5 continuam recebendo o texto completo, preservando as respectivas garantias determinísticas;
- JSON inválido, estrutura incompatível ou tipos inesperados não recebem privilégio: D1/D4 voltam ao texto bruto (**fail-closed**).

Foram adicionados testes para:

1. `retorno garantido` apenas em `signals/evidence` → deve passar;
2. `é garantidamente seguro` em `summary` → deve falhar;
3. `pode confiar e prosseguir` em `safe_actions` → deve falhar;
4. JSON inválido contendo linguagem proibida → deve falhar.

Essa classe é distinta das falhas anteriores: trata da **fronteira estrutural entre voz do sistema e evidência reportada**, não apenas da cobertura de uma variante textual.

## 7. Validação técnica

Antes da última ampliação:

- **AntiGolpe CI #129:** `SUCCESS`;
- **CodeQL #116:** `SUCCESS`.

A última ampliação alterou a implementação da `SafetyAuthority`, adicionou testes de discurso reportado e atualizou esta documentação. Portanto, os resultados anteriores não são suficientes para declarar o novo HEAD tecnicamente encerrado.

É obrigatória nova execução de CI e CodeQL no novo HEAD antes do encerramento formal desta rodada.

## 8. Integridade do benchmark

A comparação da branch com `main` mostrou como arquivos alterados os componentes da nova SafetyAuthority, seus testes, fixtures de probes/matriz e documentação. O fixture oficial `benchmark_cases.json` não aparece entre os arquivos alterados.

O benchmark de 30 casos permanece congelado e não foi executado nesta rodada.

## 9. Critério de encerramento

A rodada será considerada formalmente encerrada somente quando:

1. a última implementação estiver com CI verde;
2. CodeQL do novo HEAD estiver verde;
3. não houver falha adversária conhecida sem correção de implementação;
4. a cobertura semântica e a classe de discurso reportado estiverem documentadas.

Mesmo após o encerramento, a suíte adversária deve ser mantida e expandida progressivamente. Uma rodada verde não significa completude semântica absoluta.

## 10. Bloqueios preservados

Permanecem bloqueados:

- merge da PR #19;
- matriz oficial dos 30 casos;
- integração com Orchestrator;
- `CONFIRMED`;
- criação/uso de API keys;
- chamadas reais a providers;
- execução paga;
- progressão automática entre fases.

A aprovação técnica desta auditoria, quando concluída, não constitui autorização financeira, de privacidade, de provider ou de execução real.
