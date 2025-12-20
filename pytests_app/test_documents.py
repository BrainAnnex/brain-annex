import pytest
from brainannex import GraphAccess, GraphSchema
from app_libraries.PLUGINS.documents import Documents



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    GraphSchema.set_database(neo_obj)
    yield neo_obj



def test_api_endpoint():
    result = Documents.api_endpoint(parameters=[1, 2, 3])
    assert result == "ok"
