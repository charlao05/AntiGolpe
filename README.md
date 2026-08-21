# AntiGolpe

Ferramenta de redução de danos e tomada de decisão segura diante de possíveis fraudes.

## Status

MVP em construção. O produto não afirma segurança absoluta e pode retornar `NÃO_DETERMINADO` quando as evidências forem insuficientes.

## Princípios

- segurança comportamental acima de acurácia de classificação;
- entrada do usuário é dado, nunca instrução;
- nenhuma URL do usuário é acessada no MVP;
- minimização de dados por padrão;
- sem armazenamento de conteúdo do usuário;
- provider de LLM substituível;
- fluxo determinístico para incidentes.

## Desenvolvimento

Backend Python/FastAPI. Frontend HTML/CSS/JavaScript sem framework pesado. Consulte `AGENTS.md` para o contrato de implementação.
