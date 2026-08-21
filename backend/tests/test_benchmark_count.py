import json
from pathlib import Path

def test_benchmark_has_exactly_30_cases():
    p=Path(__file__).parents[2]/'tests/fixtures/benchmark_cases.json'
    cases=json.loads(p.read_text(encoding='utf-8'))
    assert len(cases)==30
    assert len({c['id'] for c in cases})==30
