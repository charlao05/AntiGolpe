# Segurança

O AntiGolpe usa três camadas. A Camada 3 é 100% determinística. O MVP não visita URLs, não executa conteúdo remoto e não registra payloads.

## Controles
- validação Pydantic com campos fechados;
- sanitização de PII e URLs de entrada;
- sanitização de PII na saída antes da renderização;
- rate limiting com hash de IP e TTL lógico, usando salt configurável ou aleatório por processo;
- saída validada antes da renderização;
- nenhuma credencial no frontend;
- prevenção de prompt injection por separação entre dado e instrução;
- fallback determinístico para linguagem proibida.

## Render e proxy reverso

O Render coloca Web Services atrás de Cloudflare e de seus load balancers. Para rate limiting, o AntiGolpe usa o primeiro valor de `X-Forwarded-For` como identidade do cliente e cai para o endereço de conexão quando o cabeçalho não está presente. Essa é uma premissa específica da infraestrutura de produção e deve ser revalidada se outro proxy ou CDN for colocado à frente do serviço.

## Logs e observabilidade

A aplicação não deve registrar corpos de requisição, prompts, respostas, credenciais ou PII. O Render pode produzir logs HTTP de infraestrutura que incluem método, status, URL solicitada e identificadores de requisição conforme o plano/configuração; isso não muda a obrigação de manter os logs da aplicação sem conteúdo sensível.

## Limitações conhecidas
- A sanitização automática não identifica todas as formas de informação pessoal contextual.
- O rate limiter atual é em memória e não é compartilhado entre múltiplas instâncias do serviço.
- O provider real ainda não foi integrado; o MVP usa MockProvider.
- O sistema não verifica o conteúdo das URLs, apenas sua representação textual/estrutural.

A UX orienta o usuário a não enviar credenciais e dados altamente sensíveis.
