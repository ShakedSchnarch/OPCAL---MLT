from opcal_mlt import labeling
def test_apply_rules_empty():
    assert labeling.apply_rules([1,2,3], {}) == {}
