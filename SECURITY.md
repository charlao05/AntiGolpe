# Segurança

O AntiGolpe usa três camadas. A Camada 3 é 100% determinística. O MVP não visita URLs, não executa conteúdo remoto e não registra payloads.

## Controles
- validação Pydantic com campos fechados;
- sanitização de PII e URLs de entrada;
- sanitização de PII na saída antes da renderização;
- rate limiting com hash de IP e TTL lógico, usando salt configurável ou aleatório por processo;
- resolução de IP compatível com a topologia Render/Cloudflare: `CF-Connecting-IP`, fallback para o primeiro valor de `X-Forwarded-For`, depois IP da conexão;
- saída validada antes da renderização;
- nenhuma credencial no frontend;
- prevenção de prompt injection por separação entre dado e instrução;
- fallback determinístico para linguagem proibida.

## Premissas de infraestrutura
A resolução do IP do cliente depende da topologia confiável do ambiente Render/Cloudflare. Se outro proxy ou CDN for colocado à frente do serviço, essa cadeia deve ser revalidada antes do deploy.

A API de análise usa `POST /api/analyze` com payload no corpo da requisição. Não usar query string para transportar texto, URLs ou outros dados sensíveis.

## Limitações conhecidas
- A sanitização automática não identifica todas as formas de informação pessoal contextual.
- O rate limiter atual é em memória e não é compartilhado entre múltiplas instâncias do serviço.
- O provider real ainda não foi integrado; o MVP usa MockProvider.
- O sistema não verifica o conteúdo das URLs, apenas sua representação textual/estrutural.

A UX orienta o usuário a não enviar credenciais e dados altamente sensíveis.
