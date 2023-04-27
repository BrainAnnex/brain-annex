import pytest
from neoaccess import NeoAccess


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    yield neo_obj



def test_debug(db):
    result = db._debug_local()
    assert result == "remote"
