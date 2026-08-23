from backend.tests.provider_gate.latency import LatencySample


def test_latency_sample_serializes_as_metadata_only():
    assert LatencySample(12.5).as_dict() == {"elapsed_ms": 12.5}
