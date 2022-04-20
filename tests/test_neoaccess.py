####  WARNING : the database will get erased!!!


import pytest
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.neo_access.neo_access import CypherUtils as CypherUtils
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
import os
import pandas as pd


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(verbose=True, debug=True)
    yield neo_obj


###  ~ INIT ~

def test_construction():
    # Note: if database isn't running, the error output includes the line:
    """
    Exception: CHECK IF NEO4J IS RUNNING! While instantiating the NeoAccess object, failed to create the driver: Unable to retrieve routing information
    """
    url = os.environ.get("NEO4J_HOST")

    credentials_name = os.environ.get("NEO4J_USER")
    credentials_pass = os.environ.get("NEO4J_PASSWORD")     # MAKE SURE TO SET ENVIRONMENT VARIABLE ACCORDINGLY!

    credentials_as_tuple = (credentials_name, credentials_pass)
    credentials_as_list = [credentials_name, credentials_pass]


    # One way of instantiating the class
    obj1 = neo_access.NeoAccess(url, verbose=False)       # Rely on default username/pass

    assert obj1.verbose is False
    assert obj1.version() == "4.2.1"    # Test the version of the Neo4j driver


    # Another way of instantiating the class
    obj2 = neo_access.NeoAccess(url, credentials_as_tuple, verbose=False) # Explicitly pass the credentials
    assert obj2.driver is not None


    # Yet another way of instantiating the class
    obj3 = neo_access.NeoAccess(url, credentials_as_list, verbose=False) # Explicitly pass the credentials
    assert obj3.driver is not None


    with pytest.raises(Exception):
        assert neo_access.NeoAccess(url, "bad_credentials", verbose=False)    # This ought to raise an Exception




###  ~ RUNNING GENERIC QUERIES ~

def test_query(db):
    db.empty_dbase()
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



def test_query_extended(db):
    db.empty_dbase()

    # Create and return 1st node
    q = "CREATE (n:car {make:'Toyota', color:'white'}) RETURN n"
    result = db.query_extended(q, flatten=True)
    white_car_id = result[0]['neo4j_id']
    assert type(white_car_id) == int
    assert result == [{'color': 'white', 'make': 'Toyota', 'neo4j_labels': ['car'], 'neo4j_id': white_car_id}]

    q = "MATCH (x) RETURN x"
    result = db.query_extended(q, flatten=True)
    assert result == [{'color': 'white', 'make': 'Toyota', 'neo4j_labels': ['car'], 'neo4j_id': white_car_id}]

    # Create and return 2 more nodes at once
    q = '''CREATE (b:boat {number_masts: 2, year:2003}),
                  (c:car {color: "blue"})
           RETURN b, c
        '''
    result = db.query_extended(q, flatten=True)
    for node_dict in result:
        if node_dict['neo4j_labels'] == ['boat']:
            boat_id = node_dict['neo4j_id']
        else:
            blue_car_id = node_dict['neo4j_id']

    assert result == [{'number_masts': 2, 'year': 2003, 'neo4j_labels': ['boat'], 'neo4j_id': boat_id},
                      {'color': 'blue', 'neo4j_labels': ['car'], 'neo4j_id': blue_car_id}]

    # Retrieve all 3 nodes at once
    q = "MATCH (x) RETURN x"
    result = db.query_extended(q, flatten=True)
    expected = [{'color': 'white', 'make': 'Toyota', 'neo4j_labels': ['car'], 'neo4j_id': white_car_id},
                {'number_masts': 2, 'year': 2003, 'neo4j_labels': ['boat'], 'neo4j_id': boat_id},
                {'color': 'blue', 'neo4j_labels': ['car'], 'neo4j_id': blue_car_id}]
    assert compare_recordsets(result, expected)

    q = "MATCH (b:boat), (c:car) RETURN b, c"
    result = db.query_extended(q, flatten=True)
    expected = [{'number_masts': 2, 'year': 2003, 'neo4j_id': boat_id, 'neo4j_labels': ['boat']},
                {'color': 'white', 'make': 'Toyota', 'neo4j_id': white_car_id, 'neo4j_labels': ['car']},
                {'number_masts': 2, 'year': 2003, 'neo4j_id': boat_id, 'neo4j_labels': ['boat']},
                {'color': 'blue', 'neo4j_id': blue_car_id, 'neo4j_labels': ['car']}]
    assert compare_recordsets(result, expected)

    result = db.query_extended(q, flatten=False)    # Same as above, but without flattening
    assert len(result) == 2
    expected_0 = [{'number_masts': 2, 'year': 2003, 'neo4j_id': boat_id, 'neo4j_labels': ['boat']},
                  {'color': 'white', 'make': 'Toyota', 'neo4j_id': white_car_id, 'neo4j_labels': ['car']}
                 ]
    expected_1 = [{'number_masts': 2, 'year': 2003, 'neo4j_id': boat_id, 'neo4j_labels': ['boat']},
                  {'color': 'blue', 'neo4j_id': blue_car_id, 'neo4j_labels': ['car']}
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
    #   [{'price': 7500, 'neo4j_id': 1, 'neo4j_start_node': <Node id=11 labels=frozenset() properties={}>, 'neo4j_end_node': <Node id=14 labels=frozenset() properties={}>, 'neo4j_type': 'bought_by'}]

    # Side tour to get the Neo4j id of the "person" name created in the process
    look_up_person = "MATCH (p:person {name:'Julian'}) RETURN p"
    person_result = db.query_extended(look_up_person, flatten=True)
    person_id = person_result[0]['neo4j_id']

    assert len(result) == 1
    rel_data = result[0]
    assert rel_data['neo4j_type'] == 'bought_by'
    assert rel_data['price'] == 7500
    assert type(rel_data['neo4j_id']) == int
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
            assert item == {'color': 'white', 'make': 'Toyota', 'neo4j_id': white_car_id, 'neo4j_labels': ['car']}
        elif item.get('name') == 'Julian':     # It's the person node
            assert item == {'name': 'Julian', 'neo4j_id': person_id, 'neo4j_labels': ['person']}
        else:                                   # It's the relationship
            assert item['neo4j_type'] == 'bought_by'
            assert item['price'] == 7500
            assert type(item['neo4j_id']) == int
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




###  ~ RETRIEVE DATA ~

def test_get_single_field(db):
    db.empty_dbase()
    # Create 2 nodes
    db.query('''CREATE (:`my label`:`color` {`field A`: 123, `field B`: 'test'}), 
                       (:`my label`:`make`  {                `field B`: 'more test', `field C`: 3.14})
             ''')

    result = db.get_single_field(labels="my label", field_name="field A")
    assert compare_unordered_lists(result, [123, None])

    result = db.get_single_field(labels="my label", field_name="field B")
    assert compare_unordered_lists(result, ['test', 'more test'])

    result = db.get_single_field(labels="make", field_name="field C")
    assert compare_unordered_lists(result, [3.14])

    result = db.get_single_field(labels="", field_name="field C")      # No labels specified
    assert compare_unordered_lists(result, [None, 3.14])



def test_get_record_by_primary_key(db):
    db.empty_dbase()

    node_id_Valerie = db.create_node("person", {'SSN': 123, 'name': 'Valerie', 'gender': 'F'})
    db.create_node("person", {'SSN': 456, 'name': 'Therese', 'gender': 'F'})


    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=123) \
           == {'SSN': 123, 'name': 'Valerie', 'gender': 'F'}
    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=123, return_nodeid=True) \
           == {'SSN': 123, 'name': 'Valerie', 'gender': 'F', 'neo4j_id': node_id_Valerie}

    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=456) \
           == {'SSN': 456, 'name': 'Therese', 'gender': 'F'}


    db.create_node("person", {'SSN': 456, 'name': 'Therese clone', 'gender': 'F'})  # Irregular situation with 2 records sharing what
                                                                                    # was meant to be a primary key
    with pytest.raises(Exception):
        db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=456)


    # Now, try to find records that don't exist
    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=99999) is None   # Not found
    assert db.get_record_by_primary_key("wrong_label", primary_key_name="SSN", primary_key_value=123) is None   # Not found
    assert db.get_record_by_primary_key("person", primary_key_name="bad_key", primary_key_value=123) is None   # Not found



def test_exists_by_key(db):
    db.empty_dbase()
    db.create_node("person", {'SSN': 123, 'name': 'Valerie', 'gender': 'F'})
    db.create_node("person", {'SSN': 456, 'name': 'Therese', 'gender': 'F'})

    assert db.exists_by_key("person", key_name="SSN", key_value=123)
    assert db.exists_by_key("person", key_name="SSN", key_value=456)
    assert db.exists_by_key("person", key_name="name", key_value='Valerie')

    assert not db.exists_by_key("person", key_name="SSN", key_value=5555)
    assert not db.exists_by_key("person", key_name="name", key_value='Joe')
    assert not db.exists_by_key("non_existent_label", key_name="SSN", key_value=123)



def test_fetch_nodes(db):
    db.empty_dbase()

    # Create a 1st new node
    db.create_node("test_label", {'patient_id': 123, 'gender': 'M'})

    # Retrieve the record just created (using values embedded in the Cypher query)
    match = db.find(labels="test_label", subquery="n.patient_id = 123 AND n.gender = 'M'")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    # Again, retrieve the record (this time using data-binding in the Cypher query, and values passed as a separate dictionary)
    match = db.find(labels="test_label",
                    subquery=( "n.patient_id = $patient_id AND n.gender = $gender",
                                       {"patient_id": 123, "gender": "M"}
                                     )
                    )
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Retrieve ALL records with the label "test_label", by using no clause or an empty clause
    match = db.find(labels="test_label")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    match = db.find(labels="test_label", subquery="           ")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Create a 2nd new node, using a BLANK in an attribute key
    db.create_node("my 2nd label", {'age': 21, 'gender': 'F', 'client id': 123})

    # Retrieve the record just created (using values embedded in the Cypher query)
    match = db.find(labels="my 2nd label", subquery="n.`client id` = 123")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (in a different way, using a Cypher subquery with its own data binding)
    match = db.find(labels="my 2nd label", subquery=("n.age = $age AND n.gender = $gender",
                                                     {"age": 21, "gender": "F"}
                                                    ))
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

     # Retrieve ALL records with the label "my 2nd label"
    match = db.find(labels="my 2nd label")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Same as above, but using a blank subquery
    match = db.find(labels="my 2nd label", subquery="           ")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (using a dictionary of properties)
    match = db.find(labels="my 2nd label", properties={"age": 21, "gender": "F"})
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'client id': 123, 'gender': 'F', 'age': 21}]


    # Add a 2nd new node
    db.create_node("my 2nd label", {'age': 30, 'gender': 'M', 'client id': 999})

    # Retrieve records using a clause
    match = db.find(labels="my 2nd label", subquery="n.age > 22")
    retrieved_records = db.fetch_nodes(match)
    assert retrieved_records == [{'gender': 'M', 'client id': 999, 'age': 30}]

    # Retrieve nodes REGARDLESS of label (and also retrieve the labels)
    match = db.find(properties={"gender": "M"})       # Locate all males, across all node labels
    retrieved_records = db.fetch_nodes(match, return_labels=True)
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30}]
    assert compare_recordsets(retrieved_records, expected_records)

    # Retrieve ALL nodes in the database (and also retrieve the labels)
    match = db.find()
    retrieved_records = db.fetch_nodes(match, return_labels=True)
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 123, 'gender': 'F', 'age': 21}]
    assert compare_recordsets(retrieved_records, expected_records)

    # Re-use of same key names in subquery data-binding and in properties dictionaries is ok, because the keys in
    #   properties dictionaries get internally changed
    match = db.find(labels="my 2nd label", subquery=("n.age > $age" , {"age": 22}), properties={"age": 30})
    retrieved_records = db.fetch_nodes(match)
    # Note: internally, the final Cypher query is: "MATCH (n :`my 2nd label` {`age`: $n_par_1}) WHERE (n.age > $age) RETURN n"
    #                           with data binding: {'age': 22, 'n_par_1': 30}
    # The joint requirement (age > 22 and age = 30) lead to the following record:
    expected_records = [{'gender': 'M', 'client id': 999, 'age': 30}]
    assert compare_recordsets(retrieved_records, expected_records)

    # A conflict arises only if we happen to use a key name that clashes with an internal name, such as "n_par_1";
    # an Exception is expected is such a case
    with pytest.raises(Exception):
        match = db.find(labels="my 2nd label", subquery=("n.age > $n_par_1" , {"n_par_1": 22}), properties={"age": 30})
        assert db.fetch_nodes(match)

    # If we really wanted to use a key called "n_par_1" in our subquery dictionary, we
    #       can simply alter the dummy name internally used, from the default "n" to something else
    match = db.find(dummy_node_name="person", labels="my 2nd label", subquery=("person.age > $n_par_1" , {"n_par_1": 22}), properties={"age": 30})
    # All good now, because internally the Cypher query is "MATCH (person :`my 2nd label` {`age`: $person_par_1}) WHERE (person.age > $n_par_1) RETURN person"
    #                                    with data binding {'n_par_1': 22, 'person_par_1': 30}
    retrieved_records = db.fetch_nodes(match)
    assert compare_recordsets(retrieved_records, expected_records)


    # Now, do a clean start, and investigate a list of nodes that differ in attributes (i.e. nodes that have different lists of keys)

    db.empty_dbase()

    # Create a first node, with attributes 'age' and 'gender'
    db.create_node("patient", {'age': 16, 'gender': 'F'})

    # Create a second node, with attributes 'weight' and 'gender' (notice the PARTIAL overlap in attributes with the previous node)
    db.create_node("patient", {'weight': 155, 'gender': 'M'})

    # Retrieve combined records created: note how different records have different keys
    match = db.find(labels="patient")
    retrieved_records = db.fetch_nodes(match)
    expected = [{'gender': 'F', 'age': 16},
                {'gender': 'M', 'weight': 155}]
    assert compare_recordsets(retrieved_records, expected)

    # Add a node with no attributes
    empty_record_id = db.create_node("patient")
    retrieved_records = db.fetch_nodes(match)
    expected = [{'gender': 'F', 'age': 16},
                {'gender': 'M', 'weight': 155},
                {}]
    assert compare_recordsets(retrieved_records, expected)

    match = db.find(labels="patient", properties={"age": 16})
    retrieved_single_record = db.fetch_nodes(match, single_row=True)
    assert retrieved_single_record == {'gender': 'F', 'age': 16}

    match = db.find(labels="patient", properties={"age": 11})
    retrieved_single_record = db.fetch_nodes(match, single_row=True)
    assert retrieved_single_record == None      # No record found

    match = db.find(labels="patient", neo_id=empty_record_id)
    retrieved_single_record = db.fetch_nodes(match, single_row=True)
    assert retrieved_single_record == {}        # Record with no attributes found



def test_get_nodes(db):
    db.empty_dbase()

    # Create a 1st new node
    db.create_node("test_label", {'patient_id': 123, 'gender': 'M'})

    # Retrieve the record just created (using values embedded in the Cypher query)
    retrieved_records = db.get_nodes(labels="test_label", cypher_clause="n.patient_id = 123 AND n.gender = 'M'")
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    # Retrieve the record just created (using data-binding in the Cypher query, and values passed as a separate dictionary)
    retrieved_records = db.get_nodes(labels="test_label",
                                     cypher_clause="n.patient_id = $patient_id AND n.gender = $gender",
                                     cypher_dict={"patient_id": 123, "gender": "M"})
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Retrieve ALL records with the label "test_label", by using no clause, or an empty clause
    retrieved_records = db.get_nodes(labels="test_label")
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    retrieved_records = db.get_nodes(labels="test_label",
                                     cypher_clause="           ")
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Create a 2nd new node, using a BLANK in an attribute key
    db.create_node("my 2nd label", {'age': 21, 'gender': 'F', 'client id': 123})

    # Retrieve the record just created (using values embedded in the Cypher query)
    retrieved_records = db.get_nodes("my 2nd label", cypher_clause="n.`client id` = 123")
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (another method, with data-binding in Cypher query, and values passed as a separate dictionary)
    retrieved_records = db.get_nodes("my 2nd label",
                                     cypher_clause="n.age = $age AND n.gender = $gender",
                                     cypher_dict={"age": 21, "gender": "F"})
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve ALL records with the label "my 2nd label"
    retrieved_records = db.get_nodes("my 2nd label")
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Same as above, but using a blank clause
    retrieved_records = db.get_nodes("my 2nd label", cypher_clause="           ")
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (using a dictionary of properties)
    retrieved_records = db.get_nodes("my 2nd label", properties_condition={"age": 21, "gender": "F"})
    assert retrieved_records == [{'client id': 123, 'gender': 'F', 'age': 21}]


    # Add a 2nd new node
    db.create_node("my 2nd label", {'age': 30, 'gender': 'M', 'client id': 999})

    # Retrieve records using a clause
    retrieved_records = db.get_nodes("my 2nd label", cypher_clause="n.age > 22")
    assert retrieved_records == [{'gender': 'M', 'client id': 999, 'age': 30}]


    # Retrieve nodes REGARDLESS of label (and also retrieve the labels)
    retrieved_records = db.get_nodes("",
                                     properties_condition={"gender": "M"},
                                     return_labels=True)       # Locate all males, across all node labels
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30}]
    assert compare_recordsets(retrieved_records, expected_records)


    # Retrieve ALL nodes in the database (and also retrieve the labels)
    retrieved_records = db.get_nodes("", return_labels=True)
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 123, 'gender': 'F', 'age': 21}]
    assert compare_recordsets(retrieved_records, expected_records)


    # Pass conflicting arguments; an Exception is expected
    with pytest.raises(Exception):
        assert neo_access.NeoAccess(db.fetch_nodes_by_label("my 2nd label", verbose=False,
                                                            cypher_clause="n.age > $age",
                                                            cypher_dict={"age": 22},
                                                            properties_condition={"age": 30}))


    # Now, do a clean start, an investigate a list of nodes that differ in attributes (i.e. nodes that have different lists of keys)


    db.empty_dbase()

    # Create a first node, with attributes 'age' and 'gender'
    db.create_node("patient", {'age': 16, 'gender': 'F'})

    # Create a second node, with attributes 'weight' and 'gender' (notice the PARTIAL overlap in attributes with the previous node)
    db.create_node("patient", {'weight': 155, 'gender': 'M'})

    # Retrieve combined records created: note how different records have different keys
    retrieved_records = db.get_nodes(labels="patient")
    expected = [{'gender': 'F', 'age': 16},
                {'gender': 'M', 'weight': 155}]
    assert compare_recordsets(retrieved_records, expected)



def test_get_df(db):
    db.empty_dbase()

    # Create and load a test Pandas dataframe with 2 columns and 2 rows
    df_original = pd.DataFrame({"patient_id": [1, 2], "name": ["Jack", "Jill"]})
    db.load_pandas(df_original, label="A")

    df_new = db.get_df("A")

    # Sort the columns and then sort the rows, in order to disregard both row and column order (TODO: turn into utility)
    df_original_sorted = df_original.sort_index(axis=1)
    df_original_sorted = df_original_sorted.sort_values(by=df_original_sorted.columns.tolist()).reset_index(drop=True)

    df_new_sorted = df_new.sort_index(axis=1)
    df_new_sorted = df_new_sorted.sort_values(by=df_new_sorted.columns.tolist()).reset_index(drop=True)

    assert df_original_sorted.equals(df_new_sorted)



def test_is_valid_match_structure(db):
    pass


def test_find(db):
    assert db.find() == {"node": "(n  )", "where": "", "data_binding": {}, "dummy_node_name": "n"}

    assert db.find(dummy_node_name="client") == {"node": "(client  )",
                                                 "where": "",
                                                 "data_binding": {},
                                                 "dummy_node_name": "client"}

    assert db.find(labels="person") == {"node": "(n :`person` )", "where": "", "data_binding": {}, "dummy_node_name": "n"}

    assert db.find(labels=["car", "surplus inventory"]) == {"node": "(n :`car`:`surplus inventory` )",
                                                            "where": "", "data_binding": {}, "dummy_node_name": "n"}
    assert db.find(labels=("car", "surplus inventory")) == {"node": "(n :`car`:`surplus inventory` )",
                                                            "where": "", "data_binding": {}, "dummy_node_name": "n"}

    assert db.find(neo_id=123, labels="person", properties={"gender": "F"}) == {"node": "(n)",
                                                                                "where": "id(n) = 123",
                                                                                "data_binding": {},
                                                                                "dummy_node_name": "n"}
    # Note: when neo_id is specified, all other conditions are ignored

    with pytest.raises(Exception):
        assert db.find(labels="person", key_name="item_id")

    with pytest.raises(Exception):
        assert db.find(labels="person", key_value=1000)

    res = db.find(labels="person", key_name="item_id", key_value=1000)
    expected_match = "(n :`person` {`item_id`: $n_par_1})"
    expected_dict = {"n_par_1": 1000}
    assert res == {"node": expected_match, "where": "", "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", key_name="item_id", key_value=1000, dummy_node_name="client")
    expected_match = "(client :`person` {`item_id`: $client_par_1})"
    expected_dict = {"client_par_1": 1000}
    assert res == {"node": expected_match, "where": "", "data_binding": expected_dict, "dummy_node_name": "client"}

    res = db.find(labels="person", properties={"gender": "F", "age": 22})
    expected_match = "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
    expected_dict = {"n_par_1": "F", "n_par_2": 22}
    assert res == {"node": expected_match, "where": "", "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", properties={"gender": "F", "age": 22}, key_name="item_id", key_value=1000)
    expected_match = "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2, `item_id`: $n_par_3})"
    expected_dict = {"n_par_1": "F", "n_par_2": 22, "n_par_3": 1000}
    assert res == {"node": expected_match, "where": "", "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", subquery="n.age < 36 OR n.income > 90000")
    expected_match = "(n :`person` )"
    expected_where = "n.age < 36 OR n.income > 90000"
    expected_dict = {}
    assert res == {"node": expected_match, "where": expected_where, "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", subquery=("n.age < $some_age", {"some_age": 36}))
    expected_match = "(n :`person` )"
    expected_where = "n.age < $some_age"
    expected_dict = {"some_age": 36}
    assert res == {"node": expected_match, "where": expected_where, "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", properties={"gender": "F", "age": 22}, subquery="n.income > 90000")
    expected_match = "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
    expected_where = "n.income > 90000"
    expected_dict = {"n_par_1": "F", "n_par_2": 22}
    assert res == {"node": expected_match, "where": expected_where, "data_binding": expected_dict, "dummy_node_name": "n"}

    res = db.find(labels="person", properties={"gender": "F", "age": 22}, subquery=["n.income > $min_income", {"min_income": 90000}])
    expected_match = "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
    expected_where = "n.income > $min_income"
    expected_dict = {"n_par_1": "F", "n_par_2": 22, "min_income": 90000}
    assert res == {"node": expected_match, "where": expected_where, "data_binding": expected_dict, "dummy_node_name": "n"}

    with pytest.raises(Exception):
        # Bad key name "n_par_1", which conflicts with an internally-used name
        assert db.find(labels="person", properties={"gender": "F"}, subquery=["n.income > $n_par_1", {"n_par_1": 90000}])



###  ~ FOLLOW LINKS ~

def test_follow_links(db):
    db.empty_dbase()

    db.create_node("book", {'title': 'The Double Helix'})
    db.create_node("book", {'title': 'Intro to Hilbert Spaces'})

    # Create new node, linked to the previous two
    db.create_node_with_relationships(labels="person", properties={"name": "Julian", "city": "Berkeley"},
                                      connections=[
                                            {"labels": "book",
                                             "key": "title", "value": "The Double Helix",
                                             "rel_name": "OWNS", "rel_dir": "OUT"},
                                            {"labels": "book",
                                             "key": "title", "value": "Intro to Hilbert Spaces",
                                             "rel_name": "OWNS", "rel_dir": "OUT"}
                                      ]
                                     )

    match = db.find(labels="person", properties={"name": "Julian", "city": "Berkeley"})

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book")
    expected = [{'title': 'The Double Helix'} , {'title': 'Intro to Hilbert Spaces'} ]
    assert compare_recordsets(links, expected)



def test_count_links(db):
    db.empty_dbase()

    db.create_node("book", {'title': 'The Double Helix'})
    db.create_node("book", {'title': 'Intro to Hilbert Spaces'})

    # Create new node, linked to the previous two
    db.create_node_with_relationships(labels="person", properties={"name": "Julian", "city": "Berkeley"},
                                      connections=[
                                            {"labels": "book",
                                             "key": "title", "value": "The Double Helix",
                                             "rel_name": "OWNS", "rel_dir": "OUT"},
                                            {"labels": "book",
                                             "key": "title", "value": "Intro to Hilbert Spaces",
                                             "rel_name": "OWNS", "rel_dir": "OUT"}
                                      ]
                                     )

    match = db.find(labels="person", properties={"name": "Julian", "city": "Berkeley"})

    number_links = db.count_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book")

    assert number_links == 2



def test_get_parents_and_children(db):
    db.empty_dbase()

    node_id = db.create_node("mid generation", {'age': 42, 'gender': 'F'})    # This will be the "central node"
    result = db.get_parents_and_children(node_id)
    assert result == ([], [])

    parent1_id = db.create_node("parent", {'age': 62, 'gender': 'M'})  # Add a first parent node
    db.link_nodes_by_ids(parent1_id, node_id, "PARENT_OF")

    result = db.get_parents_and_children(node_id)
    assert result == ([{'id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}],
                      [])

    parent2_id = db.create_node("parent", {'age': 52, 'gender': 'F'})  # Add 2nd parent
    db.link_nodes_by_ids(parent2_id, node_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    assert child_list == []
    compare_recordsets(parent_list,
                            [{'id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    child1_id = db.create_node("child", {'age': 13, 'gender': 'F'})  # Add a first child node
    db.link_nodes_by_ids(node_id, child1_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    assert child_list == [{'id': child1_id, 'labels': ['child'], 'rel': 'PARENT_OF'}]
    compare_recordsets(parent_list,
                            [{'id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    child2_id = db.create_node("child", {'age': 16, 'gender': 'F'})  # Add a 2nd child node
    db.link_nodes_by_ids(node_id, child2_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    compare_recordsets(child_list,
                            [{'id': child1_id, 'labels': ['child'], 'rel': 'PARENT_OF'},
                             {'id': child2_id, 'labels': ['child'], 'rel': 'PARENT_OF'}
                            ]
                      )
    compare_recordsets(parent_list,
                            [{'id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    # Look at the children/parents of a "grandparent"
    result = db.get_parents_and_children(parent1_id)
    assert result == ([],
                      [{'id': node_id, 'labels': ['mid generation'], 'rel': 'PARENT_OF'}]
                     )

    # Look at the children/parents of a "grandchild"
    result = db.get_parents_and_children(child2_id)
    assert result == ([{'id': node_id, 'labels': ['mid generation'], 'rel': 'PARENT_OF'}],
                      []
                     )



###  ~ CREATE NODES ~

def test_create_node(db):
    """
    MAIN FOCUS: create_node()
    Test the trio:  1) clear dbase
                    2) create multiple new nodes (MAIN FOCUS)
                    3) retrieve the newly created nodes, using retrieve_nodes_by_label_and_clause()
    """

    db.empty_dbase()

    # Create a new node.  Notice the blank in the key
    db.create_node("test_label", {'patient id': 123, 'gender': 'M'})

    # Retrieve the record just created (one method, with values embedded in the Cypher query)
    retrieved_records_A = db.get_nodes(labels="test_label",
                                       cypher_clause="n.`patient id` = 123 AND n.gender = 'M'")
    assert retrieved_records_A == [{'patient id': 123, 'gender': 'M'}]


    # Create a second new node
    db.create_node("test_label", {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'})

    # Retrieve cumulative 2 records created so far
    retrieved_records_B = db.get_nodes(labels="test_label",
                                       cypher_clause="n.`patient id` = 123 AND n.gender = 'M'")

    # The lists defining the expected dataset can be expressed in any order - and, likewise, the order of entries in dictionaries doesn't matter
    expected_record_list = [{'patient id': 123, 'gender': 'M'} , {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}]
    expected_record_list_alt_order = [{'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}  ,  {'gender': 'M', 'patient id': 123}]

    assert compare_recordsets(retrieved_records_B, expected_record_list)
    assert compare_recordsets(retrieved_records_B, expected_record_list_alt_order)  # We can test in any order :)


    # Create a 3rd node with a duplicate of the first new node
    db.create_node("test_label", {'patient id': 123, 'gender': 'M'})
    # Retrieve cumulative 3 records created so far
    retrieved_records_C = db.get_nodes("test_label",
                                       cypher_clause="n.`patient id` = 123 AND n.gender = 'M'")
    expected_record_list = [{'patient id': 123, 'gender': 'M'} ,
                            {'patient id': 123, 'gender': 'M'} ,
                            {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}]

    assert compare_recordsets(retrieved_records_C, expected_record_list)


    # Create a 4th node with no attributes, and a different label
    db.create_node("new_label", {})

    # Retrieve just this last node
    retrieved_records_D = db.get_nodes("new_label")
    expected_record_list = [{}]
    assert compare_recordsets(retrieved_records_D, expected_record_list)


    # Create a 5th node with labels
    db.create_node(["label 1", "label 2"], {'name': "double label"})
    # Look it up by one label
    retrieved_records = db.get_nodes("label 1")
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)
    # Look it up by the other label
    retrieved_records = db.get_nodes("label 2")
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)
    # Look it up by both labels
    retrieved_records = db.get_nodes(["label 1", "label 2"])
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)



def test_create_node_with_relationships(db):
    db.empty_dbase()

    # Create the prior nodes to which to link the newly-created node
    db.create_node("DEPARTMENT", {'dept_name': 'IT'})
    db.create_node(["CAR", "INVENTORY"], {'vehicle_id': 12345})

    new_id = \
        db.create_node_with_relationships(
            labels="PERSON",
            properties={"name": "Julian", "city": "Berkeley"},
            connections=[
                {"labels": "DEPARTMENT",
                 "key": "dept_name", "value": "IT",
                 "rel_name": "EMPLOYS", "rel_dir": "IN"},

                {"labels": ["CAR", "INVENTORY"],
                 "key": "vehicle_id", "value": 12345,
                 "rel_name": "OWNS", "rel_attrs": {"since": 2021} }
            ]
        )
    print("ID of the newly-created node: ", new_id)

    q = '''
    MATCH (:DEPARTMENT {dept_name:'IT'})-[:EMPLOYS]
          ->(p:PERSON {name: 'Julian', city: 'Berkeley'})
          -[:OWNS {since:2021}]->(:CAR:INVENTORY {vehicle_id: 12345}) 
          RETURN id(p) AS neo4j_id
    '''
    result = db.query(q)
    assert result[0]['neo4j_id'] == new_id

    """
    db.create_node_with_relationships(
        labels="PERSON",
        properties={"name": "Julian", "city": "Berkeley"},
        connections=[
            {"labels": "DEPARTMENT",
             "key": "dept_name", "value": "IT",
             "rel_name": "EMPLOYS", "rel_dir": "IN"}
        ]
    )

    db.create_node_with_relationships(
        labels="PERSON",
        properties={"name": "Julian", "city": "Berkeley"},
        connections=[
        ]
    )
    """
    db.empty_dbase()

    # Create a new node
    db.create_node("city", properties={'name': 'Berkeley', 'state': 'CA'})

    # Locate the node just created
    match = db.find(labels="city", key_name='name', key_value='Berkeley')
    assert match == {"node": "(n :`city` {`name`: $n_par_1})",
                     "where": "",
                     "data_binding": {"n_par_1": "Berkeley"},
                     "dummy_node_name": "n"
                    }
    result = db.fetch_nodes(match, single_row=True)
    assert result == {'name': 'Berkeley', 'state': 'CA'}

    db.delete_nodes(match)

    # Try to locate the node just deleted
    result = db.fetch_nodes(match)
    assert result == []             # No longer there



###  ~ DELETE NODES ~

def test_delete_nodes(db):
    db.empty_dbase()

    # Create 5 nodes, representing cars of various colors and prices
    df = pd.DataFrame({"color": ["white", "blue", "gray", "gray", "red"], "price": [100, 200, 300, 400, 500]})
    db.load_pandas(df, "car")

    # Add 1 airplane and a boat
    db.create_node("airplane", {"type": "747"})
    db.create_node("boat", {"brand": "Juneau"})

    # Delete the 2 gray cars
    match = db.find("car", properties={"color": "gray"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 2
    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 3}]      # 3 cars left
    q = "MATCH (c:car {color:'gray'}) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 0}]      # 0 gray cars found

    # Attempting to re-delete them will produce a zero count
    match = db.find("car", properties={"color": "gray"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 0
    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 3}]      # Still 3 cars left

    # Delete the red car
    match = db.find("car", subquery="n.color = 'red'")
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 1
    q = "MATCH (c:car) RETURN c.color AS col"
    result = db.query(q)
    assert compare_recordsets(result, [{'col': 'white'}, {'col': 'blue'}])  # white and blue cars are left

    # Attempting to delete a non-existing color will produce a zero count
    match = db.find("car", properties={"color": "pink"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 0

    # Delete all the remaining 2 cars
    match = db.find("car")
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 2

    # There's no more cars to delete
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 0

    # However, the airplane and the boat are still there
    q = "MATCH (a:airplane) RETURN count(a)"
    result = db.query(q)
    assert result == [{"count(a)": 1}]
    q = "MATCH (b:boat) RETURN count(b)"
    result = db.query(q)
    assert result == [{"count(b)": 1}]

    # Delete everything left
    match = db.find()
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 2      # The airplane and the boat
    q = "MATCH (x) RETURN count(x)"
    result = db.query(q)
    assert result == [{"count(x)": 0}]  # Nothing left



def test_delete_nodes_by_label(db):
    db.delete_nodes_by_label()
    number_nodes = len(db.get_nodes())
    assert number_nodes == 0

    db.create_node("appetizers", {'name': 'spring roll'})
    db.create_node("vegetable", {'name': 'carrot'})
    db.create_node("vegetable", {'name': 'broccoli'})
    db.create_node("fruit", {'type': 'citrus'})
    db.create_node("dessert", {'name': 'chocolate'})

    assert len(db.get_nodes()) == 5

    db.delete_nodes_by_label(delete_labels="fruit")
    assert len(db.get_nodes()) == 4

    db.delete_nodes_by_label(delete_labels=["vegetable"])
    assert len(db.get_nodes()) == 2

    db.delete_nodes_by_label(delete_labels=["dessert", "appetizers"])
    assert len(db.get_nodes()) == 0

    # Rebuild the same dataset as before
    db.create_node("appetizers", {'name': 'spring roll'})
    db.create_node("vegetable", {'name': 'carrot'})
    db.create_node("vegetable", {'name': 'broccoli'})
    db.create_node("fruit", {'type': 'citrus'})
    db.create_node("dessert", {'name': 'chocolate'})

    db.delete_nodes_by_label(keep_labels=["dessert", "vegetable", "appetizers"])
    assert len(db.get_nodes()) == 4

    db.delete_nodes_by_label(keep_labels="dessert", delete_labels="dessert")
    # Keep has priority over delete
    assert len(db.get_nodes()) == 4

    db.delete_nodes_by_label(keep_labels="dessert")
    assert len(db.get_nodes()) == 1



def test_empty_dbase(db):
    # Tests of completely clearing the database


    db.empty_dbase()
    # Verify nothing is left
    labels = db.get_labels()
    assert labels == []

    db.create_node("label_A", {})
    db.create_node("label_B", {'client_id': 123, 'gender': 'M'})

    db.empty_dbase()
    # Verify nothing is left
    labels = db.get_labels()
    assert labels == []

    # Test of removing only specific labels

    db.empty_dbase()
    # Add a few labels
    db.create_node("label_1", {'client_id': 123, 'gender': 'M'})
    db.create_node("label_2", {})
    db.create_node("label_3", {'client_id': 456, 'name': 'Julian'})
    db.create_node("label_4", {})
    # Only clear the specified labels
    db.delete_nodes_by_label(delete_labels=["label_1", "label_4"])
    # Verify that only labels not marked for deletions are left behind
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["label_2", "label_3"])

    # Test of keeping only specific labels

    db.empty_dbase()
    # Add a few labels
    db.create_node("label_1", {'client_id': 123, 'gender': 'M'})
    db.create_node("label_2", {})
    db.create_node("label_3", {'client_id': 456, 'name': 'Julian'})
    db.create_node("label_4", {})
    # Only keep the specified labels
    db.empty_dbase(keep_labels=["label_4", "label_3"])
    # Verify that only labels not marked for deletions are left behind
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["label_4", "label_3"])
    # Doubly-verify that one of the saved nodes can be read in
    recordset = db.get_nodes("label_3")
    assert compare_recordsets(recordset, [{'client_id': 456, 'name': 'Julian'}])



###  ~ MODIFY FIELDS ~

def test_set_fields(db):
    db.empty_dbase()

    # Create a new node.  Notice the blank in the key
    db.create_node("car", {'vehicle id': 123, 'price': 7500})

    # Locate the node just created, and create/update its attributes (reduce the price)
    match = db.find(labels="car", properties={'vehicle id': 123, 'price': 7500})
    db.set_fields(match=match, set_dict = {"color": "white", "price": 7000})

    # Look up the updated record
    retrieved_records = db.get_nodes("car")
    expected_record_list = [{'vehicle id': 123, 'color': 'white', 'price': 7000}]
    assert compare_recordsets(retrieved_records, expected_record_list)




###  ~ RELATIONSHIPS ~

def test_get_relationship_types(db):
    db.empty_dbase()
    rels = db.get_relationship_types()
    assert rels == []

    node1_id = db.create_node("Person", {'p_id': 1})
    node2_id = db.create_node("Person", {'p_id': 2})
    node3_id = db.create_node("Person", {'p_id': 3})
    db.link_nodes_by_ids(node1_id, node2_id, "LOVES")
    db.link_nodes_by_ids(node2_id, node3_id, "HATES")

    rels = db.get_relationship_types()
    assert set(rels) == {"LOVES", "HATES"}



def test_add_edge(db):
    db.empty_dbase()

    neo_from = db.create_node("car", {'color': 'white'})
    neo_to = db.create_node("owner", {'name': 'Julian'})

    match_from = db.find(neo_id=neo_from, dummy_node_name="from")
    match_to = db.find(neo_id=neo_to, dummy_node_name="to")

    number_added = db.add_edges(match_from, match_to, rel_name="OWNED_BY")
    assert number_added == 1

    with pytest.raises(Exception):
        # This will crash because the first 2 arguments are both using the same `dummy_node_name`
        assert db.add_edges(match_from, match_from, rel_name="THIS_WILL_CRASH")

    # The correct way to add an edge from a node to itself
    match_to_itself = db.find(neo_id=neo_from, dummy_node_name="to")    # Same as the node of origin, but different dummy_node_name`
    number_added = db.add_edges(match_from, match_to_itself, rel_name="FROM_CAR_TO_ITSELF")
    assert number_added == 1



def test_remove_edge(db):
    db.empty_dbase()

    neo_car = db.create_node("car", {'color': 'white'})
    neo_julian = db.create_node("owner", {'name': 'Julian'})

    match_car = db.find(neo_id=neo_car, dummy_node_name="from")
    match_julian = db.find(neo_id=neo_julian, dummy_node_name="to")

    number_added = db.add_edges(match_car, match_julian, rel_name="OWNED_BY")
    assert number_added == 1

    match_car = db.find(labels="car", dummy_node_name="from")
    match_julian = db.find(properties={"name": "Julian"}, dummy_node_name="to")

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 1     # Find the relationship

    with pytest.raises(Exception):
        assert db.remove_edges(match_car, match_julian, rel_name="NON_EXISTENT_RELATIONSHIP")

    with pytest.raises(Exception):
        assert db.remove_edges({"NON-sensical match object"}, match_julian, rel_name="OWNED_BY")

    # Finally, actually remove the edge
    number_removed = db.remove_edges(match_car, match_julian, rel_name="OWNED_BY")
    assert number_removed == 1

    result = db.query(find_query)
    assert result[0]["n_cars"] == 0     # The relationship is now gone

    with pytest.raises(Exception):
        # This will crash because the relationship is no longer there
        assert db.remove_edges(match_car, match_car, rel_name="OWNED_BY")

    with pytest.raises(Exception):
        # This will crash because the first 2 arguments are both using the same `dummy_node_name`
        assert db.remove_edges(match_car, match_car, rel_name="THIS_WILL_CRASH")


    # Restore the relationship...
    number_added = db.add_edges(match_car, match_julian, rel_name="OWNED_BY")
    assert number_added == 1

    # ...and add a 2nd one, with a different name, between the same nodes
    number_added = db.add_edges(match_car, match_julian, rel_name="REMEMBERED_BY")
    assert number_added == 1

    # ...and re-add the last one, but with a property (which is allowed by Neo4j, and will result in
    #       2 relationships with the same name between the same node
    add_query = '''
        MATCH (c:car), (o:owner)
        MERGE (c)-[:REMEMBERED_BY {since: 2020}]->(o)
    '''
    result = db.update_query(add_query)
    assert result == {'relationships_created': 1, 'properties_set': 1, 'returned_data': []}

    # Also, add a 3rd node, and another "OWNED_BY" relationship, this time affecting the 3rd node
    add_query = '''
        MATCH (c:car)
        MERGE (c)-[:OWNED_BY]->(o :owner {name: 'Val'})
    '''
    result = db.update_query(add_query)
    assert result == {'labels_added': 1, 'relationships_created': 1, 'nodes_created': 1, 'properties_set': 1, 'returned_data': []}

    # We now have a car with 2 owners: an "OWNED_BY" relationship to one of them,
    # and 3 relationships (incl. two with the same name "REMEMBERED_BY") to the other one

    find_query = '''
        MATCH (c:car)-[:REMEMBERED_BY]->(o:owner ) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 2     # The 2 relationships we just added

    # Remove 2 same-named relationships at once between the same 2 nodes
    number_removed = db.remove_edges(match_car, match_julian, rel_name="REMEMBERED_BY")
    assert number_removed == 2

    result = db.query(find_query)
    assert result[0]["n_cars"] == 0     # Gone

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner {name: 'Julian'}) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 1     # Still there

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner {name: 'Val'}) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 1     # Still there


    number_removed = db.remove_edges(match_car, match_julian, rel_name="OWNED_BY")
    assert number_removed == 1

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner {name: 'Julian'}) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 0     # Gone

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner {name: 'Val'}) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 1     # We didn't do anything to that relationship

    # Add a 2nd relations between the car node and the "Val" owner node
    add_query = '''
        MATCH (c:car), (o :owner {name: 'Val'})
        MERGE (c)-[:DRIVEN_BY]->(o)
        '''
    result = db.update_query(add_query)
    assert result == {'relationships_created': 1, 'returned_data': []}

    find_query = '''
        MATCH (c:car)-[r]->(o:owner {name: 'Val'}) 
        RETURN count(r) As n_relationships
    '''
    result = db.query(find_query)
    assert result[0]["n_relationships"] == 2

    # Delete both relationships at once
    match_val = db.find(key_name="name", key_value="Val", dummy_node_name="v")

    number_removed = db.remove_edges(match_car, match_val, rel_name=None)
    assert number_removed == 2

    result = db.query(find_query)
    assert result[0]["n_relationships"] == 0    # All gone


def test_remove_edge_2(db):
    # This set of test focuses on removing edges between GROUPS of nodes
    db.empty_dbase()

    # 2 cars, co-owned by 2 people
    q = '''
        CREATE  (c1 :car {color:'white'}), (c2 :car {color:'red'}), 
                (p1: person {name:'Julian'}), (p2 :person {name:'Val'})
        MERGE (c1)-[:OWNED_BY]->(p1) 
        MERGE (c1)-[:OWNED_BY]->(p2)
        MERGE (c2)-[:OWNED_BY]->(p1) 
        MERGE (c2)-[:OWNED_BY]->(p2)
    '''
    result = db.update_query(q)
    assert result == {'labels_added': 4, 'relationships_created': 4,
                      'nodes_created': 4, 'properties_set': 4, 'returned_data': []}

    match_white_car = db.find(labels="car", properties={"color": "white"}, dummy_node_name="from")  # 1-node match
    match_all_people = db.find(labels="person", dummy_node_name="to")                               # 2-node match


    find_query = '''
        MATCH (c :car {color:'white'})-[r:OWNED_BY]->(p : person) 
        RETURN count(r) As n_relationships
    '''
    result = db.query(find_query)
    assert result[0]["n_relationships"] == 2        # The white car has 2 links

    # Delete all the "OWNED_BY" relationships from the white car to any of the "person" nodes
    number_removed = db.remove_edges(match_white_car, match_all_people, rel_name="OWNED_BY")
    assert number_removed == 2

    result = db.query(find_query)
    assert result[0]["n_relationships"] == 0       # The 2 links from the white car are now gone




def test_test_reattach_node(db):
    pass    # TODO



def test_link_nodes_by_ids(db):
    db.empty_dbase()
    # Create dummy data and return node_ids
    nodeids = db.query("""
        UNWIND range(1,3) as x
        CREATE (test:Test)
        RETURN collect(id(test)) as ids
        """)[0]['ids']
    # linking first and second nodes
    test_rel_props = {'test 1':123, 'TEST2':'abc'}
    db.link_nodes_by_ids(nodeids[0], nodeids[1], 'TEST REL', test_rel_props)
    # getting the result
    result = db.query("""    
        MATCH (a)-[r:`TEST REL`]->(b), (c:Test)
        WHERE c<>a and c<>b
        RETURN [id(a), id(b), id(c)] as nodeids, r{.*} as rel_props    
        """)[0]
    #comparing with expected
    expected = {'nodeids': nodeids, 'rel_props': test_rel_props}
    assert result == expected



def test_link_nodes_on_matching_property(db):
    db.empty_dbase()
    db.create_node('A', {'client': 'GSK', 'expenses': 34000, 'duration': 3})
    db.create_node('B', {'client': 'Roche'})
    db.create_node('C', {'client': 'GSK'})
    db.create_node('B', {'client': 'GSK'})
    db.create_node('C', {'client': 'Pfizer', 'revenues': 34000})

    db.link_nodes_on_matching_property("A", "B", "client", rel="SAME_CLIENT")
    q = "MATCH(a:A)-[SAME_AGE]->(b:B) RETURN a, b"
    res = db.query(q)
    assert len(res) == 1

    record = res[0]
    assert record["a"] == {'client': 'GSK', 'expenses': 34000, 'duration': 3}
    assert record["b"] == {'client': 'GSK'}

    db.link_nodes_on_matching_property("A", "C", property1="expenses", property2="revenues", rel="MATCHED_BUDGET")
    q = "MATCH(a:A)-[MATCHED_BUDGET]->(b:B) RETURN a, b"
    res = db.query(q)
    assert len(res) == 1




###  ~ LABELS ~

def test_get_labels(db):
    """
    Create multiple new nodes, and then retrieve all the labels present in the database
    """

    db.empty_dbase()

    labels = db.get_labels()
    assert labels == []

    # Create a series of new nodes with different labels
    # and then check the cumulative list of labels added to the dbase thus far

    db.create_node("mercury", {'position': 1})
    labels = db.get_labels()
    assert labels == ["mercury"]

    db.create_node("venus", {'radius': 1234.5})
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mercury", "venus"])

    db.create_node("earth", {'mass': 9999.9 , 'radius': 1234.5})
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mercury", "earth", "venus"]) # The expected list may be
                                                                            # specified in any order

    db.create_node("mars", {})
    labels = db.get_labels()
    assert compare_unordered_lists(labels , ["mars", "earth", "mercury","venus"])



def test_get_label_properties(db):
    db.empty_dbase()
    db.query("CREATE (a1 :A {y:123}), (a2 :A {x:'hello'}), (a3 :A {`some name with blanks`:'x'}), (b :B {e:1})")
    result = db.get_label_properties(label = 'A')
    expected_result = ['some name with blanks', 'x', 'y']
    assert result == expected_result




###  ~ INDEXES ~

def test_get_indexes(db):
    db.empty_dbase()

    result = db.get_indexes()
    assert result.empty

    db.query("CREATE INDEX FOR (n:my_label) ON (n.my_property)")
    result = db.get_indexes()
    assert result.iloc[0]["labelsOrTypes"] == ["my_label"]
    assert result.iloc[0]["properties"] == ["my_property"]
    assert result.iloc[0]["type"] == "BTREE"
    assert result.iloc[0]["uniqueness"] == "NONUNIQUE"

    db.query("CREATE CONSTRAINT some_name ON (n:my_label) ASSERT n.node_id IS UNIQUE")
    result = db.get_indexes()
    new_row = dict(result.iloc[1])
    assert new_row == {"labelsOrTypes": ["my_label"],
                       "name": "some_name",
                       "properties": ["node_id"],
                       "type": "BTREE",
                       "uniqueness": "UNIQUE"
                      }



def test_create_index(db):
    db.empty_dbase()

    status = db.create_index(label="car", key="color")
    assert status == True

    result = db.get_indexes()
    assert len(result) == 1
    assert result.iloc[0]["labelsOrTypes"] == ["car"]
    assert result.iloc[0]["name"] == "car.color"
    assert result.iloc[0]["properties"] == ["color"]
    assert result.iloc[0]["type"] == "BTREE"
    assert result.iloc[0]["uniqueness"] == "NONUNIQUE"

    status = db.create_index("car", "color")    # Attempt to create again same index
    assert status == False

    status = db.create_index("car", "make")
    assert status == True

    result = db.get_indexes()
    assert len(result) == 2
    assert result.iloc[1]["labelsOrTypes"] == ["car"]
    assert result.iloc[1]["name"] == "car.make"
    assert result.iloc[1]["properties"] == ["make"]
    assert result.iloc[1]["type"] == "BTREE"
    assert result.iloc[1]["uniqueness"] == "NONUNIQUE"



def test_drop_index(db):
    db.empty_dbase()

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
    db.empty_dbase()

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
    db.empty_dbase()

    result = db.get_constraints()
    assert result.empty

    db.query("CREATE CONSTRAINT my_first_constraint ON (n:patient) ASSERT n.patient_id IS UNIQUE")
    result = db.get_constraints()
    assert len(result) == 1
    expected_list = ["name", "description", "details"]
    compare_unordered_lists(list(result.columns), expected_list)
    assert result.iloc[0]["name"] == "my_first_constraint"

    db.query("CREATE CONSTRAINT unique_model ON (n:car) ASSERT n.model IS UNIQUE")
    result = db.get_constraints()
    assert len(result) == 2
    expected_list = ["name", "description", "details"]
    compare_unordered_lists(list(result.columns), expected_list)
    assert result.iloc[1]["name"] == "unique_model"



def test_create_constraint(db):
    db.empty_dbase()

    status = db.create_constraint("patient", "patient_id", name="my_first_constraint")
    assert status == True

    result = db.get_constraints()
    assert len(result) == 1
    expected_list = ["name", "description", "details"]
    compare_unordered_lists(list(result.columns), expected_list)
    assert result.iloc[0]["name"] == "my_first_constraint"

    status = db.create_constraint("car", "registration_number")
    assert status == True

    result = db.get_constraints()
    assert len(result) == 2
    expected_list = ["name", "description", "details"]
    compare_unordered_lists(list(result.columns), expected_list)
    cname0 = result.iloc[0]["name"]
    cname1 = result.iloc[1]["name"]
    assert cname0 == "car.registration_number.UNIQUE" or cname1 == "car.registration_number.UNIQUE"

    status = db.create_constraint("car", "registration_number")   # Attempt to create a constraint that already was in place
    assert status == False
    result = db.get_constraints()
    assert len(result) == 2

    db.create_index("car", "parking_spot")

    status = db.create_constraint("car", "parking_spot")    # Attempt to create a constraint for which there was already an index
    assert status == False
    result = db.get_constraints()
    assert len(result) == 2



def test_drop_constraint(db):
    db.empty_dbase()

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
    db.empty_dbase()

    db.create_constraint("patient", "patient_id", name="constraint1")
    db.create_constraint("client", "client_id")

    result = db.get_constraints()
    assert len(result) == 2

    db.drop_all_constraints()

    result = db.get_constraints()
    assert len(result) == 0




###  ~ READ IN DATA from PANDAS ~

def test_load_pandas(db):
    db.empty_dbase()

    df = pd.DataFrame([[123]], columns = ["col1"])  # One row, one column
    db.load_pandas(df, "A")
    result = db.get_nodes("A")
    assert result == [{'col1': 123}]

    df = pd.DataFrame([[999]], columns = ["col1"])
    db.load_pandas(df, "A")
    result = db.get_nodes("A")
    expected = [{'col1': 123}, {'col1': 999}]
    assert compare_recordsets(result, expected)

    df = pd.DataFrame([[2222]], columns = ["col2"])
    db.load_pandas(df, "A")
    result = db.get_nodes("A")
    expected = [{'col1': 123}, {'col1': 999}, {'col2': 2222}]
    assert compare_recordsets(result, expected)

    df = pd.DataFrame([[3333]], columns = ["col3"])
    db.load_pandas(df, "B")
    A_nodes = db.get_nodes("A")
    expected_A = [{'col1': 123}, {'col1': 999}, {'col2': 2222}]
    assert compare_recordsets(A_nodes, expected_A)
    B_nodes = db.get_nodes("B")
    assert B_nodes == [{'col3': 3333}]

    db.load_pandas(df, "B")    # Re-add the same record
    B_nodes = db.get_nodes("B")
    assert B_nodes == [{'col3': 3333}, {'col3': 3333}]

    # Add a 2x2 dataframe
    df = pd.DataFrame({"col3": [100, 200], "name": ["Jack", "Jill"]})
    db.load_pandas(df, "A")
    A_nodes = db.get_nodes("A")
    expected = [{'col1': 123}, {'col1': 999}, {'col2': 2222}, {'col3': 100, 'name': 'Jack'}, {'col3': 200, 'name': 'Jill'}]
    assert compare_recordsets(A_nodes, expected)

    # Change the column names during import
    df = pd.DataFrame({"alternate_name": [1000]})
    db.load_pandas(df, "B", rename={"alternate_name": "col3"})     # Map "alternate_name" into "col3"
    B_nodes = db.get_nodes("B")
    expected_B = [{'col3': 3333}, {'col3': 3333}, {'col3': 1000}]
    assert compare_recordsets(B_nodes, expected_B)

    # Test primary_key with merge
    df = pd.DataFrame({"patient_id": [100, 200], "name": ["Jack", "Jill"]})
    db.load_pandas(df, "X")
    X_nodes = db.get_nodes("X")
    expected_X = [{'patient_id': 100, 'name': 'Jack', }, {'patient_id': 200, 'name': 'Jill'}]
    assert compare_recordsets(X_nodes, expected_X)





###  ~ JSON IMPORT/EXPORT ~

# =>  SEE test_neoaccess_json.py




###  ~ DEBUGGING SUPPORT ~

def test_debug_print(db):
    pass    # TODO





#####################   For the "CypherUtils" class   #################

def test_prepare_labels():
    lbl = ""
    assert CypherUtils.prepare_labels(lbl) == ""

    lbl = "client"
    assert CypherUtils.prepare_labels(lbl) == ":`client`"

    lbl = ["car", "car manufacturer"]
    assert CypherUtils.prepare_labels(lbl) == ":`car`:`car manufacturer`"



def test_prepare_where():
    assert CypherUtils.prepare_where("") == ""
    assert CypherUtils.prepare_where("      ") == ""
    assert CypherUtils.prepare_where([]) == ""
    assert CypherUtils.prepare_where([""]) == ""
    assert CypherUtils.prepare_where(("  ", "")) == ""

    wh = "n.name = 'Julian'"
    assert CypherUtils.prepare_where(wh) == "WHERE (n.name = 'Julian')"

    wh = ["n.name = 'Julian'"]
    assert CypherUtils.prepare_where(wh) == "WHERE (n.name = 'Julian')"

    wh = ("p.key1 = 123", "   ",  "p.key2 = 456")
    assert CypherUtils.prepare_where(wh) == "WHERE (p.key1 = 123 AND p.key2 = 456)"

    with pytest.raises(Exception):
        assert CypherUtils.prepare_where(123)    # Not a string, nor tuple, nor list



def test_dict_to_cypher():
    d = {'since': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d) == ('{`since`: $par_1, `code`: $par_2}', {'par_1': 2003, 'par_2': 'xyz'})

    d = {'year first met': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d) == ('{`year first met`: $par_1, `code`: $par_2}', {'par_1': 2003, 'par_2': 'xyz'})

    d = {'year first met': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d, prefix="val_") == ('{`year first met`: $val_1, `code`: $val_2}', {'val_1': 2003, 'val_2': 'xyz'})

    d = {'cost': 65.99, 'code': 'the "red" button'}
    assert CypherUtils.dict_to_cypher(d) == ('{`cost`: $par_1, `code`: $par_2}', {'par_1': 65.99, 'par_2': 'the "red" button'})

    d = {'phrase': "it's ready!"}
    assert CypherUtils.dict_to_cypher(d) == ('{`phrase`: $par_1}', {'par_1': "it's ready!"})

    d = {'phrase': '''it's "ready"!'''}
    assert CypherUtils.dict_to_cypher(d) == ('{`phrase`: $par_1}', {'par_1': 'it\'s "ready"!'})

    d = None
    assert CypherUtils.dict_to_cypher(d) == ("", {})

    d = {}
    assert CypherUtils.dict_to_cypher(d) == ("", {})
