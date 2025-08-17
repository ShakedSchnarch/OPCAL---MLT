from opcal_mlt import io
def test_noop_io_exists():
    assert hasattr(io, '__dict__')
