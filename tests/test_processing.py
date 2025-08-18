from opcal_mlt import processing
def test_smooth_returns_input():
    assert processing.smooth([1,2,3]) == [1,2,3]
