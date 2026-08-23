# Privacidade

O MVP segue minimização por padrão.

Não há conta, login, histórico ou banco de dados de usuários. Conteúdo bruto não deve ser persistido nem registrado em logs.

A API de análise recebe dados via `POST` no corpo da requisição. Não use query string nem path para transportar texto, URLs ou outros dados sensíveis.

Antes de processamento externo futuro, texto e URL passam por minimização. Dependendo do provider escolhido, dados minimizados poderão ser processados por terceiros. O provider só será definido após o `PROVIDER.md` ser aprovado.

## Limites da infraestrutura
Nosso código não registra o conteúdo das análises. O provedor de hospedagem pode manter logs técnicos de infraestrutura conforme suas próprias políticas. Não envie dados sensíveis na URL.

A política pública não promete que nenhum dado jamais sai da infraestrutura; ela descreve honestamente o fluxo do provider selecionado.
