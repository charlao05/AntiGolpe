# Phase 3 — Política de IP

Para o deployment Render/Cloudflare, a resolução do cliente segue:

1. `CF-Connecting-IP`;
2. primeiro valor de `X-Forwarded-For`;
3. endereço da conexão.

Essa política depende da topologia confiável do host e deve ser revalidada se outro proxy/CDN for colocado na frente do serviço.
