# Segurança

O AntiGolpe usa três camadas. A Camada 3 é determinística. O MVP não visita URLs, não executa conteúdo remoto e não registra payloads.

## Controles
- validação Pydantic com campos fechados;
- sanitização de PII e URLs;
- rate limiting com hash de IP e TTL lógico;
- saída validada antes da renderização;
- nenhuma credencial no frontend;
- prevenção de prompt injection por separação entre dado e instrução;
- fallback determinístico para linguagem proibida.

## Limitação conhecida
A sanitização automática não identifica todas as formas de informação pessoal contextual. A UX orienta o usuário a não enviar credenciais e dados altamente sensíveis.
