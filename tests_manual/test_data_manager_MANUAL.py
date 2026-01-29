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



def test_extract_node_neighborhood(db):

    result = DataManager.extract_node_neighborhood(node_internal_id=535,
                                                   known_neighbors=['2', '24176', '72817', '24052', '24053', '24054', '72698', '24060', '24061', '24062', '24063'],
                                                  max_neighbors=10)

    #result = DataManager.extract_node_neighborhood(node_internal_id=2, known_neighbors=[],
    #                                               max_neighbors=10)

    print("NODES:")
    for n in result["nodes"]:
        print(n)

    print("EDGES:")
    for e in result["edges"]:
        print(e)
