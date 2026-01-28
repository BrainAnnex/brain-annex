import pytest
from brainannex import GraphAccess
from app_libraries.data_manager import DataManager



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    host = ""       # TODO: set/unset as needed
    password = ""             # TODO: set/unset as needed

    db = GraphAccess(host=host, credentials=("neo4j", password))
    DataManager.set_database(db)
    yield db



def test_foo(db):

    result = DataManager.visit_node_neighborhood(node_internal_id=853, known_neighbors=[13, 23488, 1967, 1])

    print("NODES:")
    for n in result["nodes"]:
        print(n)

    print("EDGES:")
    for e in result["edges"]:
        print(e)
