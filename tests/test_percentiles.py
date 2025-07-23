from aura.models import predict as p

def test_percentile_edges(dummy_percentiles_df):
 
    assert p.percentile_lookup(0, "acc_open_past_24mths") == 0.0

    assert p.percentile_lookup(50, "acc_open_past_24mths") == 1.0

def test_engineered_mapping(dummy_percentiles_df):
    val = p.percentile_lookup(700**2, "fico_mid_sq")
    assert 0.0 <= val <= 1.0