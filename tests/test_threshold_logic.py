from aura.app.config import decision_threshold

def test_threshold_high():
    prob = decision_threshold + 0.01
    assert prob >= decision_threshold

def test_threshold_low():
    prob = decision_threshold - 0.01
    assert prob < decision_threshold