import pytest
from neoaccess import GraphAccess


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=True)
    yield neo_obj



def test_get_single_record_by_key(db):
    result = db.get_record_by_primary_key("CLASS", primary_key_name ="name", primary_key_value ="Short live courses")
    print(result)



def test_exists_by_key(db):
    result = db.exists_by_key("CLASS", key_name="name", key_value="Site Link")
    print(result)
    assert result == True