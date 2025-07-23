import pytest
from aura.app.config import validate_one, validate_ui_payload, InputError

def test_grade_ok():
    assert validate_one("grade", "b") == "B"

def test_grade_bad():
    with pytest.raises(InputError):
        validate_one("grade", "Z")

def test_term_ok():
    assert validate_one("term", "36") == 36
    assert validate_one("term", "60 months") == 60

def test_term_bad():
    with pytest.raises(InputError):
        validate_one("term", "72")

def test_dti_negative():
    with pytest.raises(InputError):
        validate_one("dti", -1)

def test_fico_bounds():
    with pytest.raises(InputError):
        validate_one("fico_mid", 100)
    with pytest.raises(InputError):
        validate_one("fico_mid", 900)

def test_payload_full(valid_payload):
    cleaned = validate_ui_payload(valid_payload, require_all=True)
    assert cleaned == valid_payload