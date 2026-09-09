# Fase 5.1 — Auditoria Adversária da SafetyAuthority — 2026-09-09

**Status:** `RODADA ADVERSÁRIA CONCLUÍDA NO COMMIT VALIDADO; ÚLTIMA AMPLIAÇÃO AGUARDANDO CI`

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

O teste da cobertura semântica foi também corrigido para exigir explicitamente as 18 categorias, incluindo:

- SEM-07 — ação afirmada vs. negada;
- SEM-08 — coordenação com alternativa;
- SEM-12 — garantia/certeza.

A matriz continua contendo exatamente 18 classes, cada uma com probe seguro e perigoso distintos.

## 6. Validação técnica

No commit anterior à última ampliação da suíte:

- **AntiGolpe CI #129:** `SUCCESS`;
- **CodeQL #116:** `SUCCESS`.

A última ampliação adicionou apenas endurecimento dos testes adversários e da validação explícita das 18 categorias. Ela requer nova execução de CI antes de ser considerada tecnicamente encerrada.

## 7. Integridade do benchmark

A comparação da branch com `main` mostrou como arquivos alterados apenas os componentes da nova SafetyAuthority, seus testes, fixtures de probes/matriz e documentação. O fixture oficial `benchmark_cases.json` não aparece entre os arquivos alterados.

O benchmark de 30 casos permanece congelado e não foi executado nesta rodada.

## 8. Critério de encerramento

A rodada será considerada formalmente encerrada quando a última ampliação tiver CI verde e não houver falha adversária conhecida sem correção de implementação.

Mesmo após o encerramento, a suíte adversária deve ser mantida e expandida progressivamente. Uma rodada verde não significa completude semântica absoluta.

## 9. Bloqueios preservados

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
