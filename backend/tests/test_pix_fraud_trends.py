from backend.tools.pix_fraud_trends import BCB_ENDPOINT


def test_bcb_odata_query_is_percent_encoded():
    assert "$format=json" not in BCB_ENDPOINT
    assert "$orderby=AnoMes desc" not in BCB_ENDPOINT
    assert "%24format=json" in BCB_ENDPOINT
    assert "%24orderby=AnoMes+desc" in BCB_ENDPOINT
