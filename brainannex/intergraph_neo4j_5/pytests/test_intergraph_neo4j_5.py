####  WARNING : the Neo4j database identified by the environment variables below, will get erased!!!

"""
IMPORTANT - to run the pytests in this file, the following ENVIRONMENT VARIABLES must first be set:
                1. NEO4J_HOST
                2. NEO4J_USER
                3. NEO4J_PASSWORD

            For example, if using PyCharm, follow the main menu to: Run > Edit Configurations
            and then, in the template for pytest, set Environment Variable to something like:
                    NEO4J_HOST=bolt://<your IP address>:7687;NEO4J_USER=neo4j;NEO4J_PASSWORD=<your Neo4j password>
"""

import pytest
from brainannex.intergraph_neo4j_5.intergraph_neo4j_5 import InterGraph
from utilities.comparisons import compare_unordered_lists, compare_recordsets
from datetime import datetime, date
import os
import neo4j.time



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    # MAKE SURE TO FIRST SET THE ENVIRONMENT VARIABLES, prior to run the pytests in this file!
    neo_obj = InterGraph(debug=False)     # Change the debug option to True if desired
    yield neo_obj





#################  METHODS from the Parent Class NeoAccessCore  #################

###  ~ INIT ~

def test_constructor():
    # Note: if database isn't running, the error output includes the line:
    """
        Exception: CHECK IF NEO4J IS RUNNING! While instantiating the NeoAccess object,
        failed to create the driver: Unable to retrieve routing information
    """

    # MAKE SURE TO FIRST SET THE ENVIRONMENT VARIABLES
    url = os.environ.get("NEO4J_HOST")

    credentials_name = os.environ.get("NEO4J_USER")
    credentials_pass = os.environ.get("NEO4J_PASSWORD")

    credentials_as_tuple = (credentials_name, credentials_pass)
    credentials_as_list = [credentials_name, credentials_pass]


    # One way of instantiating the class
    obj1 = InterGraph(url, debug=False)       # Rely on default username/pass

    assert obj1.debug is False
    assert obj1.version() == "5.28.1"    # Test the version of the Neo4j driver (this ought to match the value in requirements.txt)


    # Another way of instantiating the class
    obj2 = InterGraph(url, credentials_as_tuple, debug=False) # Explicitly pass the credentials
    assert obj2.driver is not None


    # Yet another way of instantiating the class
    obj3 = InterGraph(url, credentials_as_list, debug=False) # Explicitly pass the credentials
    assert obj3.driver is not None


    with pytest.raises(Exception):
        assert InterGraph(url, "bad_credentials", debug=False)    # This ought to raise an Exception



def test_connect(db):
    db.connect()
    assert db.driver is not None



def test_version(db):
    assert type (db.version()) == str
    assert db.version() != ""




###  ~ RUNNING GENERIC QUERIES ~

def test_query(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    q = "CREATE (:car {make:'Toyota', color:'white'})"   # Create a node without returning it
    result = db.query(q)
    assert result == []

    q = "CREATE (n:car {make:'VW', color:$color, year:2021}) RETURN n"   # Create a node and return it; use data binding
    result = db.query(q, {"color": "red"})
    assert result == [{'n': {'color': 'red', 'make': 'VW', 'year': 2021}}]

    q = "MATCH (x) RETURN x"
    result = db.query(q)
    expected = [{'x': {'color': 'white', 'make': 'Toyota'}},
                {'x': {'color': 'red', 'year': 2021, 'make': 'VW'}}]
    assert compare_recordsets(result, expected)

    q = '''CREATE (b:boat {number_masts: 2, year:2003}),
                  (c:car {color: "blue"})
           RETURN b, c
        '''   # Create and return multiple nodes
    result = db.query(q)
    assert result == [{'b': {'number_masts': 2, 'year': 2003},
                       'c': {'color': 'blue'}}]

    q = "MATCH (c:car {make:'Toyota'}) RETURN c"
    result = db.query(q)
    assert result == [{'c': {'color': 'white', 'make': 'Toyota'}}]

    q = "MATCH (c:car) RETURN c.color, c.year AS year_made"
    result = db.query(q)
    expected = [{'c.color': 'white', 'year_made': None},
                {'c.color': 'red', 'year_made': 2021},
                {'c.color': 'blue', 'year_made': None}]
    assert compare_recordsets(result, expected)

    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 3}]

    q = '''MATCH (c:car {make:'Toyota', color:'white'}) 
           MERGE (c)-[r:bought_by {price:7500}]->(p:person {name:'Julian'})
           RETURN r
        '''
    result = db.query(q)
    assert result == [{'r': ({}, 'bought_by', {})}]



def test_query_2(db):
    # Explore the "single_row" and "single_cell" arguments of query()

    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    q = "MATCH (n) RETURN n"    # Query to locate all nodes

    result = db.query(q, single_row=True)
    assert result is None       # No records returned

    result = db.query(q, single_cell="some_name")
    assert result is None       # No records returned


    db.query("CREATE (:car)")   # A node with no properties

    result = db.query(q, single_row=True)
    assert result == {'n': {}}      # Note how this differs from the case of no records found

    result = db.query(q, single_cell="some_name")
    assert result is None           # A record was found, but lacks a field called "some_name"

    q = "MATCH (n) RETURN n.color AS color"
    result = db.query(q, single_row=True)
    assert result == {"color": None}
    result = db.query(q, single_cell="color")
    assert result is None


    # Add a 1st boat
    db.query("CREATE (:boat {type: 'sloop'})")
    q = "MATCH (n :boat) RETURN n.type AS boat_type"
    result = db.query(q, single_row=True)
    assert result == {"boat_type": "sloop"}
    result = db.query(q, single_cell="boat_type")
    assert result == "sloop"
    result = db.query(q, single_cell="brand")
    assert result is None       # No "brand" field in the result


    # Add a 2nd boat
    db.query("CREATE (:boat {type: 'ketch'})")
    q = "MATCH (n :boat) RETURN n.type AS boat_type ORDER BY n.type"
    result = db.query(q, single_row=True)
    assert result == {"boat_type": "ketch"}
    result = db.query(q, single_cell="boat_type")
    assert result == "ketch"
    result = db.query(q, single_cell="brand")
    assert result is None       # Still no "brand" field in the result



def test_query_extended(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create and return 1st node
    q = "CREATE (n:car {make:'Toyota', color:'white'}) RETURN n"
    result = db.query_extended(q, flatten=True)
    white_car_id = result[0]['internal_id']
    assert type(white_car_id) == int
    assert result == [{'color': 'white', 'make': 'Toyota', 'node_labels': ['car'], 'internal_id': white_car_id}]

    q = "MATCH (x) RETURN x"
    result = db.query_extended(q, flatten=True)
    assert result == [{'color': 'white', 'make': 'Toyota', 'node_labels': ['car'], 'internal_id': white_car_id}]

    # Create and return 2 more nodes at once
    q = '''CREATE (b:boat {number_masts: 2, year:2003}),
                  (c:car {color: "blue"})
           RETURN b, c
        '''
    result = db.query_extended(q, flatten=True)
    for node_dict in result:
        if node_dict['node_labels'] == ['boat']:
            boat_id = node_dict['internal_id']
        else:
            blue_car_id = node_dict['internal_id']

    assert result == [{'number_masts': 2, 'year': 2003, 'node_labels': ['boat'], 'internal_id': boat_id},
                      {'color': 'blue', 'node_labels': ['car'], 'internal_id': blue_car_id}]

    # Retrieve all 3 nodes at once
    q = "MATCH (x) RETURN x"
    result = db.query_extended(q, flatten=True)
    expected = [{'color': 'white', 'make': 'Toyota', 'node_labels': ['car'], 'internal_id': white_car_id},
                {'number_masts': 2, 'year': 2003, 'node_labels': ['boat'], 'internal_id': boat_id},
                {'color': 'blue', 'node_labels': ['car'], 'internal_id': blue_car_id}]
    assert compare_recordsets(result, expected)

    q = "MATCH (b:boat), (c:car) RETURN b, c"
    result = db.query_extended(q, flatten=True)
    expected = [{'number_masts': 2, 'year': 2003, 'internal_id': boat_id, 'node_labels': ['boat']},
                {'color': 'white', 'make': 'Toyota', 'internal_id': white_car_id, 'node_labels': ['car']},
                {'number_masts': 2, 'year': 2003, 'internal_id': boat_id, 'node_labels': ['boat']},
                {'color': 'blue', 'internal_id': blue_car_id, 'node_labels': ['car']}]
    assert compare_recordsets(result, expected)

    result = db.query_extended(q, flatten=False)    # Same as above, but without flattening
    assert len(result) == 2
    expected_0 = [{'number_masts': 2, 'year': 2003, 'internal_id': boat_id, 'node_labels': ['boat']},
                  {'color': 'white', 'make': 'Toyota', 'internal_id': white_car_id, 'node_labels': ['car']}
                 ]
    expected_1 = [{'number_masts': 2, 'year': 2003, 'internal_id': boat_id, 'node_labels': ['boat']},
                  {'color': 'blue', 'internal_id': blue_car_id, 'node_labels': ['car']}
                 ]

    if compare_recordsets(result[0], expected_0):           # If the list elements at the top level are in the same order
        assert compare_recordsets(result[1], expected_1)
    else:                                                   # If the list elements at the top level are in reverse order
        assert compare_recordsets(result[0], expected_1)
        assert compare_recordsets(result[1], expected_0)


    # Create and retrieve a new relationship, with attributes
    q = '''MATCH (c:car {make:'Toyota', color:'white'}) 
           MERGE (c)-[r:bought_by {price:7500}]->(p:person {name:'Julian'})
           RETURN r
        '''
    result = db.query_extended(q, flatten=True)
    # EXAMPLE of result:
    #   [{'price': 7500, 'internal_id': 1, 'neo4j_start_node': <Node id=11 labels=frozenset() properties={}>, 'neo4j_end_node': <Node id=14 labels=frozenset() properties={}>, 'neo4j_type': 'bought_by'}]

    # Side tour to get the Neo4j id of the "person" name created in the process
    look_up_person = "MATCH (p:person {name:'Julian'}) RETURN p"
    person_result = db.query_extended(look_up_person, flatten=True)
    person_id = person_result[0]['internal_id']

    assert len(result) == 1
    rel_data = result[0]
    assert rel_data['neo4j_type'] == 'bought_by'
    assert rel_data['price'] == 7500
    assert type(rel_data['internal_id']) == int
    assert rel_data['neo4j_start_node'].id == white_car_id
    assert rel_data['neo4j_end_node'].id == person_id

    # A query that returns both nodes and relationships
    q = '''MATCH (c:car {make:'Toyota'}) 
                 -[r:bought_by]->(p:person {name:'Julian'})
           RETURN c, r, p
        '''
    result = db.query_extended(q, flatten=True)
    assert len(result) == 3     # It returns a car, a person, and a relationship

    for item in result:
        if item.get('color') == 'white':    # It's the car node
            assert item == {'color': 'white', 'make': 'Toyota', 'internal_id': white_car_id, 'node_labels': ['car']}
        elif item.get('name') == 'Julian':     # It's the person node
            assert item == {'name': 'Julian', 'internal_id': person_id, 'node_labels': ['person']}
        else:                                   # It's the relationship
            assert item['neo4j_type'] == 'bought_by'
            assert item['price'] == 7500
            assert type(item['internal_id']) == int
            assert item['neo4j_start_node'].id == white_car_id
            assert item['neo4j_end_node'].id == person_id


    # Queries that return values rather than Graph Data Types such as nodes and relationships
    q = "MATCH (c:car) RETURN c.color, c.year AS year_made"
    result = db.query(q)
    expected = [{'c.color': 'white', 'year_made': None},
                {'c.color': 'blue', 'year_made': None}]
    assert compare_recordsets(result, expected)

    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 2}]



def test_update_query(db):
    pass    # TODO



def test_empty_dbase(db):
    # Tests of completely clearing the database

    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    # Verify nothing is left
    labels = db.get_labels()
    assert labels == []

    db.query("CREATE (:label_A)")
    db.query("CREATE (:label_B {client_id: 123, gender: 'M'})")

    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    # Verify nothing is left
    labels = db.get_labels()
    assert labels == []

    # Test of removing only specific labels

    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    # Add a few labels
    db.query("CREATE (:label_1 {client_id: 123, gender: 'M'})")
    db.query("CREATE (:label_2)")
    db.query("CREATE (:label_3 {client_id: 456, name: 'Julian'})")
    db.query("CREATE (:label_4)")
    # Only clear the specified labels
    db.delete_nodes_by_label(delete_labels=["label_1", "label_4"])
    # Verify that only labels not marked for deletions are left behind
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["label_2", "label_3"])

    # Test of keeping only specific labels

    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    # Add a few labels
    db.query("CREATE (:label_1 {client_id: 123, gender: 'M'})")
    db.query("CREATE (:label_2)")
    db.query("CREATE (:label_3 {client_id: 456, name: 'Julian'})")
    db.query("CREATE (:label_4)")
    # Only keep the specified labels
    db.empty_dbase(keep_labels=["label_4", "label_3"])
    # Verify that only labels not marked for deletions are left behind
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["label_4", "label_3"])
    # Doubly-verify that one of the saved nodes can be read in
    q = "MATCH (n :label_3) RETURN n"
    result = db.query(q)
    print(result)
    record = result[0]["n"]
    assert record == {'client_id': 456, 'name': 'Julian'}





###############   ~ LABELS ~   ###############

def test_get_labels(db):
    """
    Create multiple new nodes, and then retrieve all the labels present in the database
    """

    db.empty_dbase(keep_labels=None)

    labels = db.get_labels()
    assert labels == []

    # Create a series of new nodes with different labels
    # and then check the cumulative list of labels added to the dbase thus far

    q = "CREATE (:mercury {position: 1})"
    db.query(q)
    labels = db.get_labels()
    assert labels == ["mercury"]

    q = "CREATE (:venus {radius: 1234.5})"
    db.query(q)
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mercury", "venus"]) # The expected list may be
                                                                  # specified in any order

    q = "CREATE (:earth {mass: 9999.9 , radius: 1234.5})"
    db.query(q)
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mercury", "earth", "venus"])

    q = "CREATE (:mars)"
    db.query(q)
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mars", "earth", "mercury","venus"])

    q = "CREATE (:jupiter:planet)"
    db.query(q)
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mars", "earth", "mercury","venus", "jupiter", "planet"])



def test_delete_nodes_by_label(db):
    db.delete_nodes_by_label()
    result = db.query("MATCH (n) RETURN n")   # Everything in the dbase
    number_nodes = len(result)
    assert number_nodes == 0

    db.query("CREATE (:appetizers {name: 'spring roll'})")
    db.query("CREATE (:vegetable {name: 'carrot'})")
    db.query("CREATE (:vegetable {name: 'broccoli'})")
    db.query("CREATE (:fruit {type: 'citrus'})")
    db.query("CREATE (:dessert {name: 'chocolate'})")

    assert len(db.query("MATCH (n) RETURN n")) == 5

    db.delete_nodes_by_label(delete_labels="fruit")
    assert len(db.query("MATCH (n) RETURN n")) == 4

    db.delete_nodes_by_label(delete_labels=["vegetable"])
    assert len(db.query("MATCH (n) RETURN n")) == 2

    db.delete_nodes_by_label(delete_labels=["dessert", "appetizers"])
    assert len(db.query("MATCH (n) RETURN n")) == 0

    # Rebuild the same dataset as before
    db.query("CREATE (:appetizers {name: 'spring roll'})")
    db.query("CREATE (:vegetable {name: 'carrot'})")
    db.query("CREATE (:vegetable {name: 'broccoli'})")
    db.query("CREATE (:fruit {type: 'citrus'})")
    db.query("CREATE (:dessert {name: 'chocolate'})")

    db.delete_nodes_by_label(keep_labels=["dessert", "vegetable", "appetizers"])
    assert len(db.query("MATCH (n) RETURN n")) == 4

    db.delete_nodes_by_label(keep_labels="dessert", delete_labels="dessert")
    # Keep has priority over delete
    assert len(db.query("MATCH (n) RETURN n")) == 4

    db.delete_nodes_by_label(keep_labels="dessert")
    assert len(db.query("MATCH (n) RETURN n")) == 1



def test_bulk_delete_by_label(db):
    #TODO
    pass




def test_get_label_properties(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    db.query("CREATE (a1 :A {y:123}), (a2 :A {x:'hello'}), (a3 :A {`some name with blanks`:'x'}), (b :B {e:1})")
    result = db.get_label_properties(label = 'A')
    expected_result = ['some name with blanks', 'x', 'y']
    assert result == expected_result





############   ~ INDEXES ~    ############


def test_get_indexes(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    result = db.get_indexes()
    assert result.empty

    # Directly create an index
    db.query("CREATE INDEX FOR (n:my_label) ON (n.my_property)")
    result = db.get_indexes()
    assert result.iloc[0]["labelsOrTypes"] == ["my_label"]
    assert result.iloc[0]["properties"] == ["my_property"]
    assert result.iloc[0]["entityType"] == "NODE"

    # Indirectly create a 2nd index
    db.query("CREATE CONSTRAINT some_name IF NOT EXISTS FOR (n:my_label) REQUIRE n.node_id IS UNIQUE")
    result = db.get_indexes()

    # The earlier index is still there
    assert result.iloc[0]["labelsOrTypes"] == ["my_label"]
    assert result.iloc[0]["properties"] == ["my_property"]
    assert result.iloc[0]["entityType"] == "NODE"

    # The new index
    assert result.iloc[1]["name"] == "some_name"
    assert result.iloc[1]["labelsOrTypes"] == ["my_label"]
    assert result.iloc[1]["properties"] == ["node_id"]
    assert result.iloc[1]["entityType"] == "NODE"



def test_create_index(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    status = db.create_index(label="car", key="color")
    assert status == True

    result = db.get_indexes()
    assert len(result) == 1
    assert result.iloc[0]["labelsOrTypes"] == ["car"]
    assert result.iloc[0]["name"] == "car.color"
    assert result.iloc[0]["properties"] == ["color"]


    status = db.create_index("car", "color")    # Attempt to create again same index
    assert status == False

    status = db.create_index("car", "make")
    assert status == True

    result = db.get_indexes()
    assert len(result) == 2
    assert result.iloc[1]["labelsOrTypes"] == ["car"]
    assert result.iloc[1]["name"] == "car.make"
    assert result.iloc[1]["properties"] == ["make"]



def test_drop_index(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    db.create_index("car", "color")
    db.create_index("car", "make")
    db.create_index("vehicle", "year")
    db.create_index("vehicle", "factory")

    index_df = db.get_indexes()
    assert len(index_df) == 4

    status = db.drop_index("car.make")
    assert status == True
    index_df = db.get_indexes()
    assert len(index_df) == 3

    status = db.drop_index("car.make")  # Attempt to take out an index that is not present
    assert status == False
    index_df = db.get_indexes()
    assert len(index_df) == 3


def test_drop_all_indexes(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    db.create_index("car", "color")
    db.create_index("car", "make")
    db.create_index("vehicle", "year")

    index_df = db.get_indexes()
    assert len(index_df) == 3

    db.drop_all_indexes()

    index_df = db.get_indexes()
    assert len(index_df) == 0




###  ~ CONSTRAINTS ~

def test_get_constraints(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    result = db.get_constraints()
    assert result.empty

    expected_cols = ['name', 'type', 'labelsOrTypes', 'properties', 'entityType', 'ownedIndex']

    # Add a constraint
    db.query("CREATE CONSTRAINT my_first_constraint IF NOT EXISTS FOR (n:patient) REQUIRE n.patient_id IS UNIQUE")
    result = db.get_constraints()
    assert len(result) == 1

    assert compare_unordered_lists(list(result.columns), expected_cols)
    assert result.iloc[0]["name"] == "my_first_constraint"
    assert result.iloc[0]["type"] == "UNIQUENESS"
    assert result.iloc[0]["labelsOrTypes"] == ["patient"]
    assert result.iloc[0]["entityType"] == "NODE"
    assert result.iloc[0]["ownedIndex"] == "my_first_constraint"


    # Add a 2nd constraint
    db.query("CREATE CONSTRAINT unique_model IF NOT EXISTS FOR (n:car) REQUIRE n.model IS UNIQUE")
    result = db.get_constraints()
    assert len(result) == 2

    assert compare_unordered_lists(list(result.columns), expected_cols)
    # From the earlier constraint
    assert result.iloc[0]["name"] == "my_first_constraint"
    assert result.iloc[0]["type"] == "UNIQUENESS"
    assert result.iloc[0]["labelsOrTypes"] == ["patient"]
    assert result.iloc[0]["properties"] == ["patient_id"]
    assert result.iloc[0]["entityType"] == "NODE"
    assert result.iloc[0]["ownedIndex"] == "my_first_constraint"

    # From the new constraint
    assert result.iloc[1]["name"] == "unique_model"
    assert result.iloc[1]["type"] == "UNIQUENESS"
    assert result.iloc[1]["labelsOrTypes"] == ["car"]
    assert result.iloc[1]["properties"] == ["model"]
    assert result.iloc[1]["entityType"] == "NODE"
    assert result.iloc[1]["ownedIndex"] == "unique_model"



def test_create_constraint(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create a 1st constraint
    status = db.create_constraint("patient", "patient_id", name="my_first_constraint")
    assert status == True

    result = db.get_constraints()
    assert len(result) == 1
    assert result.iloc[0]["name"] == "my_first_constraint"
    assert result.iloc[0]["type"] == "UNIQUENESS"
    assert result.iloc[0]["labelsOrTypes"] == ["patient"]
    assert result.iloc[0]["properties"] == ["patient_id"]
    assert result.iloc[0]["entityType"] == "NODE"
    assert result.iloc[0]["ownedIndex"] == "my_first_constraint"


    # Create a 2nd constraint
    status = db.create_constraint("car", "registration_number")
    assert status == True

    result = db.get_constraints()
    assert len(result) == 2

    cname0 = result.iloc[0]["name"]
    cname1 = result.iloc[1]["name"]
    # The order isn't guaranteed
    assert compare_unordered_lists([cname0, cname1],
                                   ["my_first_constraint", "car.registration_number.UNIQUE"])


    # Attempt to create a constraint that already was in place
    status = db.create_constraint("car", "registration_number")

    assert status == False
    result = db.get_constraints()
    assert len(result) == 2


    # Attempt to create a constraint for which there was already an index
    db.create_index("car", "parking_spot")

    status = db.create_constraint("car", "parking_spot")
    assert status == False
    result = db.get_constraints()
    assert len(result) == 2



def test_drop_constraint(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    db.create_constraint("patient", "patient_id", name="constraint1")
    db.create_constraint("client", "client_id")

    result = db.get_constraints()
    assert len(result) == 2

    status = db.drop_constraint("constraint1")
    assert status == True
    result = db.get_constraints()
    assert len(result) == 1

    status = db.drop_constraint("constraint1")  # Attempt to remove a constraint that doesn't exist
    assert status == False
    result = db.get_constraints()
    assert len(result) == 1

    status = db.drop_constraint("client.client_id.UNIQUE")  # Using the name automatically assigned by create_constraint()
    assert status == True
    result = db.get_constraints()
    assert len(result) == 0



def test_drop_all_constraints(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    db.create_constraint("patient", "patient_id", name="constraint1")
    db.create_constraint("client", "client_id")

    result = db.get_constraints()
    assert len(result) == 2

    db.drop_all_constraints()

    result = db.get_constraints()
    assert len(result) == 0



###  ~ DEBUGGING SUPPORT ~

def test_debug_print(db):
    pass    # TODO