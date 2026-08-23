# Provider Gate Sandbox

Este diretório é reservado ao experimento controlado de providers. Não deve ser importado por `backend/app/main.py` nem executado pelo CI de produção.

Estrutura planejada:

- `openai_adapter.py`
- `anthropic_adapter.py`
- `google_adapter.py`
- `run_pure.py`
- `run_framework.py`
- `run_structured.py`
- `scoring.py`
- `latency.py`
- `token_usage.py`
- `cost_report.py`

A implementação dos adapters reais só começa após o fechamento das decisões de governança e orçamento do Provider Gate.
