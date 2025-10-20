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
from brainannex import neoaccess as neo_access
from utilities.comparisons import compare_unordered_lists, compare_recordsets
from datetime import datetime, date
import pandas as pd
import numpy as np
import neo4j.time



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    # MAKE SURE TO FIRST SET THE ENVIRONMENT VARIABLES, prior to run the pytests in this file!
    neo_obj = neo_access.NeoAccess(debug=False)     # Change the debug option to True if desired
    yield neo_obj




###  ~ RETRIEVE DATA ~

def test_get_single_field(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create 2 nodes
    db.query('''CREATE (:`my label`:`color` {`field A`: 123, `field B`: 'test'}), 
                       (:`my label`:`make`  {                `field B`: 'more test', `field C`: 3.14})
             ''')

    match = db.match(labels="my label")

    result = db.get_single_field(match=match, field_name="field A")
    assert compare_unordered_lists(result, [123, None])

    result = db.get_single_field(match=match, field_name="field B")
    assert compare_unordered_lists(result, ['test', 'more test'])

    match = db.match(labels="make")

    result = db.get_single_field(match=match, field_name="field C")
    assert compare_unordered_lists(result, [3.14])

    match = db.match(labels="")      # No labels specified
    result = db.get_single_field(match=match, field_name="field C")
    assert compare_unordered_lists(result, [None, 3.14])



def test_get_record_by_primary_key(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    node_id_Valerie = db.create_node("person", {'SSN': 123, 'name': 'Valerie', 'gender': 'F'})
    db.create_node("person", {'SSN': 456, 'name': 'Therese', 'gender': 'F'})


    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=123) \
           == {'SSN': 123, 'name': 'Valerie', 'gender': 'F'}
    assert db.get_record_by_primary_key("person", primary_key_name="SSN", primary_key_value=123, return_internal_id=True) \
           == {'SSN': 123, 'name': 'Valerie', 'gender': 'F', 'internal_id': node_id_Valerie}

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

    assert not db.exists_by_key("person", key_name="SSN", key_value=123)    # Cannot exist, because we just emptied the database

    db.create_node("person", {'SSN': 123, 'name': 'Valerie', 'gender': 'F'})
    db.create_node("person", {'SSN': 456, 'name': 'Therese', 'gender': 'F'})

    assert db.exists_by_key("person", key_name="SSN", key_value=123)
    assert db.exists_by_key("person", key_name="SSN", key_value=456)
    assert db.exists_by_key("person", key_name="name", key_value='Valerie')

    assert not db.exists_by_key("person", key_name="SSN", key_value=5555)
    assert not db.exists_by_key("person", key_name="name", key_value='Joe')
    assert not db.exists_by_key("non_existent_label", key_name="SSN", key_value=123)



def test_exists_by_internal_id(db):
    db.empty_dbase()

    assert not db.exists_by_internal_id(internal_id = 8888)     # Cannot exist, because we just emptied the database

    Valerie_ID = db.create_node("person", {'SSN': 123, 'name': 'Valerie', 'gender': 'F'})
    assert db.exists_by_internal_id(Valerie_ID)
    assert not db.exists_by_internal_id(Valerie_ID+1)


    Therese_ID = db.create_node("person", {'SSN': 456, 'name': 'Therese', 'gender': 'F'})
    assert db.exists_by_internal_id(Therese_ID)

    assert not db.exists_by_internal_id(Valerie_ID + Therese_ID + 1)    # Using an internal ID that could not possibly exist



def test_get_nodes(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create a 1st new node
    db.create_node("test_label", {'patient_id': 123, 'gender': 'M'})

    # Retrieve the record just created (using values embedded in the Cypher query)
    match = db.match(labels="test_label", clause="n.patient_id = 123 AND n.gender = 'M'")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    # Again, retrieve the record (this time using data-binding in the Cypher query, and values passed as a separate dictionary)
    match = db.match(labels="test_label",
                     clause=( "n.patient_id = $patient_id AND n.gender = $gender",
                               {"patient_id": 123, "gender": "M"}
                            )
                    )
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Retrieve ALL records with the label "test_label", by using no clause or an empty clause
    match = db.match(labels="test_label")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]

    match = db.match(labels="test_label", clause="           ")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'patient_id': 123, 'gender': 'M'}]


    # Create a 2nd new node, using a BLANK in an attribute key
    db.create_node("my 2nd label", {'age': 21, 'gender': 'F', 'client id': 123})

    # Retrieve the record just created (using values embedded in the Cypher query)
    match = db.match(labels="my 2nd label", clause="n.`client id` = 123")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (in a different way, using a Cypher subquery with its own data binding)
    match = db.match(labels="my 2nd label", clause=("n.age = $age AND n.gender = $gender",
                                                     {"age": 21, "gender": "F"}
                                                     ))
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve ALL records with the label "my 2nd label"
    match = db.match(labels="my 2nd label")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Same as above, but using a blank subquery
    match = db.match(labels="my 2nd label", clause="           ")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'age': 21, 'gender': 'F', 'client id': 123}]

    # Retrieve the record just created (using a dictionary of properties)
    match = db.match(labels="my 2nd label", properties={"age": 21, "gender": "F"})
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'client id': 123, 'gender': 'F', 'age': 21}]


    # Add a 2nd new node
    db.create_node("my 2nd label", {'age': 30, 'gender': 'M', 'client id': 999})

    # Retrieve records using a clause
    match = db.match(labels="my 2nd label", clause="n.age > 22")
    retrieved_records = db.get_nodes(match)
    assert retrieved_records == [{'gender': 'M', 'client id': 999, 'age': 30}]

    # Retrieve nodes REGARDLESS of label (and also retrieve the labels)
    match = db.match(properties={"gender": "M"})       # Locate all males, across all node labels
    retrieved_records = db.get_nodes(match, return_labels=True)
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30}]
    assert compare_recordsets(retrieved_records, expected_records)

    # Retrieve ALL nodes in the database (and also retrieve the labels)
    match = db.match()
    retrieved_records = db.get_nodes(match, return_labels=True)
    expected_records = [{'neo4j_labels': ['test_label'], 'gender': 'M', 'patient_id': 123},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 999, 'gender': 'M', 'age': 30},
                        {'neo4j_labels': ['my 2nd label'], 'client id': 123, 'gender': 'F', 'age': 21}]
    assert compare_recordsets(retrieved_records, expected_records)

    # Re-use of same key names in subquery data-binding and in properties dictionaries is ok, because the keys in
    #   properties dictionaries get internally changed
    match = db.match(labels="my 2nd label", clause=("n.age > $age" , {"age": 22}), properties={"age": 30})
    retrieved_records = db.get_nodes(match)
    # Note: internally, the final Cypher query is: "MATCH (n :`my 2nd label` {`age`: $n_par_1}) WHERE (n.age > $age) RETURN n"
    #                           with data binding: {'age': 22, 'n_par_1': 30}
    # The joint requirement (age > 22 and age = 30) lead to the following record:
    expected_records = [{'gender': 'M', 'client id': 999, 'age': 30}]
    assert compare_recordsets(retrieved_records, expected_records)

    # A conflict arises only if we happen to use a key name that clashes with an internal name, such as "n_par_1";
    # an Exception is expected is such a case
    with pytest.raises(Exception):
        match = db.match(labels="my 2nd label", clause=("n.age > $n_par_1" , {"n_par_1": 22}), properties={"age": 30})
        assert db.get_nodes(match)

    # If we really wanted to use a key called "n_par_1" in our subquery dictionary, we
    #       can simply alter the dummy name internally used, from the default "n" to something else
    match = db.match(dummy_node_name="person", labels="my 2nd label",
                     clause=("person.age > $n_par_1" , {"n_par_1": 22}), properties={"age": 30})

    # All good now, because internally the Cypher query is:
    #           "MATCH (person :`my 2nd label` {`age`: $person_par_1}) WHERE (person.age > $n_par_1) RETURN person"
    #           with data binding {'n_par_1': 22, 'person_par_1': 30}
    retrieved_records = db.get_nodes(match)
    assert compare_recordsets(retrieved_records, expected_records)


    # Now, do a clean start, and investigate a list of nodes that differ in attributes (i.e. nodes that have different lists of keys)

    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create a first node, with attributes 'age' and 'gender'
    db.create_node("patient", {'age': 16, 'gender': 'F'})

    # Create a second node, with attributes 'weight' and 'gender' (notice the PARTIAL overlap in attributes with the previous node)
    db.create_node("patient", {'weight': 155, 'gender': 'M'})

    # Retrieve combined records created: note how different records have different keys
    match = db.match(labels="patient")
    retrieved_records = db.get_nodes(match)
    expected = [{'gender': 'F', 'age': 16},
                {'gender': 'M', 'weight': 155}]
    assert compare_recordsets(retrieved_records, expected)

    # Add a node with no attributes
    empty_record_id = db.create_node("patient")
    retrieved_records = db.get_nodes(match)
    expected = [{'gender': 'F', 'age': 16},
                {'gender': 'M', 'weight': 155},
                {}]
    assert compare_recordsets(retrieved_records, expected)

    match = db.match(labels="patient", properties={"age": 16})
    retrieved_single_record = db.get_nodes(match, single_row=True)
    assert retrieved_single_record == {'gender': 'F', 'age': 16}

    match = db.match(labels="patient", properties={"age": 11})
    retrieved_single_record = db.get_nodes(match, single_row=True)
    assert retrieved_single_record is None      # No record found

    match = db.match(labels="patient", internal_id=empty_record_id)
    retrieved_single_record = db.get_nodes(match, single_row=True)
    assert retrieved_single_record == {}        # Record with no attributes found



def test_get_df(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create and load a test Pandas dataframe with 2 columns and 2 rows
    df_original = pd.DataFrame({"patient_id": [1, 2], "name": ["Jack", "Jill"]})
    db.load_pandas(df_original, labels="A")

    match = db.match(labels="A")
    df_new = db.get_df(match=match)

    # Sort the columns and then sort the rows, in order to disregard both row and column order (TODO: turn into utility)
    df_original_sorted = df_original.sort_index(axis=1)
    df_original_sorted = df_original_sorted.sort_values(by=df_original_sorted.columns.tolist()).reset_index(drop=True)

    df_new_sorted = df_new.sort_index(axis=1)
    df_new_sorted = df_new_sorted.sort_values(by=df_new_sorted.columns.tolist()).reset_index(drop=True)

    assert df_original_sorted.equals(df_new_sorted)



def test_get_node_labels(db):
    db.empty_dbase()

    my_book = db.create_node("book", {'title': 'The Double Helix'})
    result = db.get_node_labels(my_book)
    assert result == ["book"]

    my_vehicle = db.create_node(["car", "vehicle"])
    result = db.get_node_labels(my_vehicle)
    assert result == ["car", "vehicle"]

    label_less = db.create_node(labels=None, properties={'title': 'I lost my labels'})
    result = db.get_node_labels(label_less)
    assert result == []



def test_standardize_recordset(db):
    db.empty_dbase()

    # Use a date as a field value
    car_1 = db.create_node(labels="Car", properties={"color": "red", "make": "Honda",
                                             "bought_on": neo4j.time.Date(2019, 6, 1),
                                             "certified": neo4j.time.DateTime(2019, 1, 31, 18, 59, 35)
                                             })
    q = "MATCH (n) RETURN n"
    dataset = db.query(q)

    result = db.standardize_recordset(dataset)

    assert result == [{'color': 'red', 'make': 'Honda',
                       'bought_on': '2019/06/01', 'certified': '2019/01/31'}]


    car_2 = db.create_node(labels="Car", properties={"color": "blue", "make": "Toyota",
                                             "bought_on": neo4j.time.Date(2025, 10, 4),
                                             "certified": neo4j.time.DateTime(2003, 7, 15, 18, 59, 35)
                                             })

    q = "MATCH (n) WHERE n.color='blue' RETURN n, id(n) AS internal_id"
    dataset = db.query(q)
    result = db.standardize_recordset(dataset)

    assert result == [{'color': 'blue', 'make': 'Toyota',
                       'bought_on': '2025/10/04', 'certified': '2003/07/15', 'internal_id': car_2}]


    q = "MATCH (n) RETURN n, id(n) AS internal_id ORDER BY n.make"
    dataset = db.query(q)

    result = db.standardize_recordset(dataset)

    assert result == [{'color': 'red', 'make': 'Honda',
                       'bought_on': '2019/06/01', 'certified': '2019/01/31', 'internal_id': car_1},
                      {'color': 'blue', 'make': 'Toyota',
                       'bought_on': '2025/10/04', 'certified': '2003/07/15', 'internal_id': car_2}]


    q = "MATCH (n) RETURN n, id(n) AS internal_id, labels(n) AS node_labels ORDER BY n.make"
    dataset = db.query(q)

    result = db.standardize_recordset(dataset)

    assert result == [{'color': 'red', 'make': 'Honda',
                       'bought_on': '2019/06/01', 'certified': '2019/01/31', 'internal_id': car_1, 'node_labels': ['Car']},
                      {'color': 'blue', 'make': 'Toyota',
                       'bought_on': '2025/10/04', 'certified': '2003/07/15', 'internal_id': car_2, 'node_labels': ['Car']}]





###  ~ FOLLOW LINKS ~

def test_follow_links(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    book_1 = db.create_node("book", {'title': 'The Double Helix'})
    book_2 = db.create_node("book", {'title': 'Intro to Hilbert Spaces'})

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

    match = db.match(labels="person", properties={"name": "Julian", "city": "Berkeley"})

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=False)
    expected = [{'title': 'The Double Helix'} , {'title': 'Intro to Hilbert Spaces'}]
    assert compare_recordsets(links, expected)

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=False, limit=1)
    assert (links == [{'title': 'The Double Helix'}]) or (links == [{'title': 'Intro to Hilbert Spaces'}])

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=True)
    expected = [{'title': 'The Double Helix', 'internal_id': book_1} , {'title': 'Intro to Hilbert Spaces', 'internal_id': book_2}]
    assert compare_recordsets(links, expected)

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=False, include_labels=True)
    expected = [{'title': 'The Double Helix', 'node_labels': ['book']} , {'title': 'Intro to Hilbert Spaces', 'node_labels': ['book']}]
    assert compare_recordsets(links, expected)

    links = db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=True, include_labels=True)
    expected = [ {'title': 'The Double Helix', 'internal_id': book_1, 'node_labels': ['book']} ,
                 {'title': 'Intro to Hilbert Spaces', 'internal_id': book_2, 'node_labels': ['book']}]
    assert compare_recordsets(links, expected)

    with pytest.raises(Exception):
        db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=False, limit="not integer!")

    with pytest.raises(Exception):
        db.follow_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book", include_id=False, limit=0)   # Bad limit



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

    match = db.match(labels="person", properties={"name": "Julian", "city": "Berkeley"})

    number_links = db.count_links(match, rel_name="OWNS", rel_dir="OUT", neighbor_labels="book")

    assert number_links == 2



def test_get_parents_and_children(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    node_id = db.create_node("mid generation", {'age': 42, 'gender': 'F'})    # This will be the "central node"
    result = db.get_parents_and_children(node_id)
    assert result == ([], [])

    parent1_id = db.create_node("parent", {'age': 62, 'gender': 'M'})  # Add a first parent node
    db.link_nodes_by_ids(parent1_id, node_id, "PARENT_OF")

    result = db.get_parents_and_children(node_id)
    assert result == ([{'internal_id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}],
                      [])

    parent2_id = db.create_node("parent", {'age': 52, 'gender': 'F'})  # Add 2nd parent
    db.link_nodes_by_ids(parent2_id, node_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    assert child_list == []
    compare_recordsets(parent_list,
                            [{'internal_id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'internal_id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    child1_id = db.create_node("child", {'age': 13, 'gender': 'F'})  # Add a first child node
    db.link_nodes_by_ids(node_id, child1_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    assert child_list == [{'internal_id': child1_id, 'labels': ['child'], 'rel': 'PARENT_OF'}]
    compare_recordsets(parent_list,
                            [{'internal_id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'internal_id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    child2_id = db.create_node("child", {'age': 16, 'gender': 'F'})  # Add a 2nd child node
    db.link_nodes_by_ids(node_id, child2_id, "PARENT_OF")

    (parent_list, child_list) = db.get_parents_and_children(node_id)
    compare_recordsets(child_list,
                            [{'internal_id': child1_id, 'labels': ['child'], 'rel': 'PARENT_OF'},
                             {'internal_id': child2_id, 'labels': ['child'], 'rel': 'PARENT_OF'}
                            ]
                      )
    compare_recordsets(parent_list,
                            [{'internal_id': parent1_id, 'labels': ['parent'], 'rel': 'PARENT_OF'},
                             {'internal_id': parent2_id, 'labels': ['parent'], 'rel': 'PARENT_OF'}
                            ]
                      )

    # Look at the children/parents of a "grandparent"
    result = db.get_parents_and_children(parent1_id)
    assert result == ([],
                      [{'internal_id': node_id, 'labels': ['mid generation'], 'rel': 'PARENT_OF'}]
                     )

    # Look at the children/parents of a "grandchild"
    result = db.get_parents_and_children(child2_id)
    assert result == ([{'internal_id': node_id, 'labels': ['mid generation'], 'rel': 'PARENT_OF'}],
                      []
                     )



def test_get_siblings(db):
    db.empty_dbase()

    # Create "French" and "German" nodes, as subcategory of "Language"
    q = '''
        CREATE (c1 :Categories {name: "French"})-[:subcategory_of]->(p :Categories {name: "Language"})<-[:subcategory_of]-
               (c2 :Categories {name: "German"})
        RETURN id(c1) AS french_id, id(c2) AS german_id, id(p) AS language_id
        '''
    create_result = db.query(q, single_row=True)

    (french_id, german_id, language_id) = list( map(create_result.get, ["french_id", "german_id", "language_id"]) )


    # Get all the sibling categories of a given language

    with pytest.raises(Exception):
        db.get_siblings(internal_id=french_id, rel_name=666, rel_dir="OUT") # rel_name isn't a string

    with pytest.raises(Exception):
        db.get_siblings(internal_id=[1, 2, 3], rel_name="subcategory_of", rel_dir="OUT")    # Bad ID

    with pytest.raises(Exception):
        db.get_siblings(internal_id=french_id, rel_name="subcategory_of", rel_dir="Is it IN or OUT")

    # The single sibling of "French" is "German"
    result = db.get_siblings(internal_id=french_id, rel_name="subcategory_of", rel_dir="OUT")
    assert result == [{'name': 'German', 'internal_id': german_id, 'neo4j_labels': ['Categories']}]

    # Conversely, the single sibling of "German" is "French"
    result = db.get_siblings(internal_id=german_id, rel_name="subcategory_of", rel_dir="OUT")
    assert result == [{'name': 'French', 'internal_id': french_id, 'neo4j_labels': ['Categories']}]

    # But attempting to follow the links in the opposite directions will yield no results
    result = db.get_siblings(internal_id=german_id, rel_name="subcategory_of", rel_dir="IN")    # "wrong" direction
    assert result == []

    # Add a 3rd language category, "Italian", as a subcategory of the "Language" node
    italian_id = db.create_attached_node(labels="Categories", properties={"name": "Italian"},
                                         attached_to=language_id, rel_name="subcategory_of")

    # Now, "French" will have 2 siblings instead of 1
    result = db.get_siblings(internal_id=french_id, rel_name="subcategory_of", rel_dir="OUT")
    expected = [{'name': 'Italian', 'internal_id': italian_id, 'neo4j_labels': ['Categories']},
                {'name': 'German', 'internal_id': german_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)

    # "Italian" will also have 2 siblings
    result = db.get_siblings(internal_id=italian_id, rel_name="subcategory_of", rel_dir="OUT")
    expected = [{'name': 'French', 'internal_id': french_id, 'neo4j_labels': ['Categories']},
                {'name': 'German', 'internal_id': german_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)

    # Add a node that is a "parent" of "French" and "Italian" thru a different relationship
    db.create_attached_node(labels="Language Family", properties={"name": "Romance"},
                            attached_to=[french_id, italian_id], rel_name="contains")

    # Now, "French" will also have a sibling thru the "contains" relationship
    result = db.get_siblings(internal_id=french_id, rel_name="contains", rel_dir="IN")
    expected = [{'name': 'Italian', 'internal_id': italian_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)

    # Likewise for the "Italian" node
    result = db.get_siblings(internal_id=italian_id, rel_name="contains", rel_dir="IN")
    expected = [{'name': 'French', 'internal_id': french_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)

    # "Italian" still has 2 siblings thru the other relationship "subcategory_of"
    result = db.get_siblings(internal_id=italian_id, rel_name="subcategory_of", rel_dir="OUT")
    expected = [{'name': 'French', 'internal_id': french_id, 'neo4j_labels': ['Categories']},
                {'name': 'German', 'internal_id': german_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)

    # Add an unattached node
    brazilian_id = db.create_node(labels="Categories", properties={"name": "Brazilian"})
    result = db.get_siblings(internal_id=brazilian_id, rel_name="subcategory_of", rel_dir="OUT")
    assert result == []     # No siblings

    # After connecting the "Brazilian" node to the "Language" node, it has 3 siblings
    db.add_links_fast(match_from=brazilian_id, match_to=language_id, rel_name="subcategory_of")
    result = db.get_siblings(internal_id=brazilian_id, rel_name="subcategory_of", rel_dir="OUT")
    expected = [{'name': 'French', 'internal_id': french_id, 'neo4j_labels': ['Categories']},
                {'name': 'German', 'internal_id': german_id, 'neo4j_labels': ['Categories']},
                {'name': 'Italian', 'internal_id': italian_id, 'neo4j_labels': ['Categories']}]
    assert compare_recordsets(result, expected)



def test_get_link_summary(db):
    db.empty_dbase()

    # 1st node
    car_id = db.create_node(labels="Car")

    assert db.get_link_summary(car_id) == {"in": [], "out": []}


    # 2nd node
    person_id = db.create_attached_node(labels="Person",
                        attached_to=car_id, rel_name="OWNS", rel_dir="OUT")

    assert db.get_link_summary(person_id) == {"in": [], "out": [("OWNS", 1)]}

    assert db.get_link_summary(car_id) == {"in": [("OWNS", 1)], "out": []}


    # 3rd node
    db.create_attached_node(labels="Color",
                            attached_to=car_id, rel_name="HAS_COLOR", rel_dir="IN")

    assert db.get_link_summary(person_id) == {"in": [], "out": [("OWNS", 1)]}

    assert db.get_link_summary(car_id) == {"in": [("OWNS", 1)], "out": [("HAS_COLOR", 1)]}

    #TODO: additional tests





###  ~ CREATE NODES ~

def test_create_node(db):
    """
    Test the trio:  1) clear dbase
                    2) create multiple new nodes (MAIN FOCUS)
                    3) retrieve the newly created nodes, using retrieve_nodes_by_label_and_clause()
    """

    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create a new node.  Notice the blank in the key
    db.create_node("test_label", {'patient id': 123, 'gender': 'M'})

    # Retrieve the record just created (one method, with values embedded in the Cypher query)
    match = db.match(labels="test_label", clause="n.`patient id` = 123 AND n.gender = 'M'")

    retrieved_records_A = db.get_nodes(match)
    assert retrieved_records_A == [{'patient id': 123, 'gender': 'M'}]


    # Create a second new node
    db.create_node("test_label", {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'})

    # Retrieve cumulative 2 records created so far
    retrieved_records_B = db.get_nodes(match)

    # The lists defining the expected dataset can be expressed in any order - and, likewise, the order of entries in dictionaries doesn't matter
    expected_record_list = [{'patient id': 123, 'gender': 'M'} , {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}]
    expected_record_list_alt_order = [{'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}  ,  {'gender': 'M', 'patient id': 123}]

    assert compare_recordsets(retrieved_records_B, expected_record_list)
    assert compare_recordsets(retrieved_records_B, expected_record_list_alt_order)  # We can test in any order :)


    # Create a 3rd node with a duplicate of the first new node
    db.create_node("test_label", {'patient id': 123, 'gender': 'M'})
    # Retrieve cumulative 3 records created so far
    retrieved_records_C = db.get_nodes(match)
    expected_record_list = [{'patient id': 123, 'gender': 'M'} ,
                            {'patient id': 123, 'gender': 'M'} ,
                            {'patient id': 123, 'gender': 'M', 'condition_id': 'happy'}]

    assert compare_recordsets(retrieved_records_C, expected_record_list)


    # Create a 4th node with no attributes, and a different label
    db.create_node("new_label", {})

    # Retrieve just this last node
    match = db.match(labels="new_label")
    retrieved_records_D = db.get_nodes(match)
    expected_record_list = [{}]
    assert compare_recordsets(retrieved_records_D, expected_record_list)


    # Create a 5th node with labels
    db.create_node(["label 1", "label 2"], {'name': "double label"})
    # Look it up by one label
    match = db.match(labels="label 1")
    retrieved_records = db.get_nodes(match)
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)
    # Look it up by the other label
    match = db.match(labels="label 2")
    retrieved_records = db.get_nodes(match)
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)
    # Look it up by both labels
    match = db.match(labels=["label 1", "label 2"])
    retrieved_records = db.get_nodes(match)
    expected_record_list = [{'name': "double label"}]
    assert compare_recordsets(retrieved_records, expected_record_list)



def test_create_node_with_relationships(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

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
          RETURN id(p) AS internal_id
    '''
    result = db.query(q)
    assert result[0]['internal_id'] == new_id



def test_create_attached_node(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    with pytest.raises(Exception):
        # Attempting to link to non-existing nodes
        db.create_attached_node(labels="COMPANY", attached_to=[123, 456], rel_name="EMPLOYS")

    node_jack = db.create_node("PERSON", {"name": "Jack"})
    node_jill = db.create_node("PERSON", {"name": "Jill"})
    node_mary = db.create_node("PERSON", {"name": "Mary"})

    with pytest.raises(Exception):
        # Missing rel_name
        db.create_attached_node(labels="COMPANY", attached_to=[node_jack, node_jill, node_mary])


    # Create a new Company node and attach it to "Jack"
    new_node = db.create_attached_node(labels="COMPANY", attached_to=node_jack, rel_name="EMPLOYS")

    q = f'''
        MATCH (c:COMPANY)-[:EMPLOYS]->(p:PERSON {{name: "Jack"}})
        WHERE id(c) = {new_node}
        RETURN count(c) AS company_count, count(p) AS person_count
        '''
    result = db.query(q, single_row=True)
    assert result == {'company_count': 1, 'person_count': 1}


    # Attach the already-created Company node to the 2 other people it employs ("Jill" and "Mary")
    new_node_2 = db.create_attached_node(labels="COMPANY", attached_to=[node_jill, node_mary], rel_name="EMPLOYS", merge=True)
    assert new_node_2 == new_node   # No new nodes created, because of the merge=True (and the already existing company node)

    q = f'''
        MATCH path=(c:COMPANY)-[:EMPLOYS]->(p:PERSON)
        WHERE id(c) = {new_node_2} AND p.name IN ["Jack", "Jill", "Mary"]
        RETURN count(path) AS number_paths       
        '''
    result = db.query(q, single_cell="number_paths")
    assert result == 3


    # Attach a NEW company node to "Jill" and "Mary" (merge=False option forces a new node creation, even though a match already exists)
    new_node_3 = db.create_attached_node(labels="COMPANY", attached_to=[node_jill, node_mary], rel_name="EMPLOYS", merge=False)
    assert new_node_3 != new_node   # New node created, because of the merge=False (and the already existing company node)

    q = f'''
        MATCH path=(c:COMPANY)-[:EMPLOYS]->(p:PERSON)
        WHERE id(c) = {new_node_3} AND p.name IN ["Jack", "Jill", "Mary"]
        RETURN count(path) AS number_paths       
        '''
    result = db.query(q, single_cell="number_paths")
    assert result == 2      # Only "Jill" and "Mary", because it's a new Company node, not the original one


    # Attach a NEW company node to all 3 people; it will be a new node because it has different attributes
    new_node_4 = db.create_attached_node(labels="COMPANY", properties={"name": "Acme Gadgets", "city": "Berkeley"},
                                         attached_to=[node_jill, node_mary], rel_name="EMPLOYS", merge=True)
    assert new_node_4 != new_node_3     # It's a new node, in spite of merge=True, because it has different attributes
                                        # than the original Company node

    q = f'''
        MATCH path=(c:COMPANY {{name: "Acme Gadgets", city: "Berkeley"}})-[:EMPLOYS]->(p:PERSON)
        WHERE id(c) = {new_node_4} AND p.name IN ["Jack", "Jill", "Mary"]
        RETURN count(path) AS number_paths       
        '''
    result = db.query(q, single_cell="number_paths")
    assert result == 2      # Only "Jill" and "Mary", because it's a new Company node, not the original one


    # TODO: test pathological scenarios where existing link-to nodes are mentioned multiple times



def test_create_node_with_links(db):

    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    with pytest.raises(Exception):
        db.create_node_with_links(labels="A", properties="Not a dictionary")

    with pytest.raises(Exception):
        db.create_node_with_links(labels="A", links=666)    # links isn't a list/None

    with pytest.raises(Exception):
        db.create_node_with_links(labels="A", links=[{"internal_id": 9999, "rel_name": "GHOST"}])   # Linking to non-existing node

    # Create a first node, with no links
    car_id = db.create_node_with_links(labels = ["CAR", "INVENTORY"],
                                       properties = {'vehicle_id': 12345})
    # Verify it
    match = db.match(internal_id=car_id, labels=["CAR", "INVENTORY"])
    lookup = db.get_nodes(match)
    assert lookup == [{'vehicle_id': 12345}]

    # Create a 2nd node, also with no links
    dept_id = db.create_node_with_links(labels = "DEPARTMENT",
                                        properties = {'dept name': 'IT'},
                                        links = [])
    # Verify it
    match = db.match(internal_id=dept_id, labels = "DEPARTMENT")
    lookup = db.get_nodes(match)
    assert lookup == [{'dept name': 'IT'}]


    # Create a new node linked to the 2 ones just created
    new_id = \
        db.create_node_with_links(
            labels="PERSON",
            properties={"name": "Julian", "city": "Berkeley"},
            links=[
                {"internal_id": dept_id,
                 "rel_name": "EMPLOYS",
                 "rel_dir": "IN"},

                {"internal_id": car_id,
                 "rel_name": "OWNS",
                 "rel_attrs": {"since": 2021} }
            ]
        )
    #print("ID of the newly-created node: ", new_id)

    q = '''
    MATCH (:DEPARTMENT {`dept name`:'IT'})-[:EMPLOYS]
          ->(p:PERSON {name: 'Julian', city: 'Berkeley'})
          -[:OWNS {since:2021}]->(:CAR:INVENTORY {vehicle_id: 12345}) 
          RETURN id(p) AS internal_id
    '''
    result = db.query(q)
    assert result[0]['internal_id'] == new_id


    # Attempt to create another new node with 2 identical links to the SAME existing node
    with pytest.raises(Exception):
        db.create_node_with_links(
            labels="PERSON",
            properties={"name": "Val", "city": "San Francisco"},
            links=[
                {"internal_id": car_id,
                 "rel_name": "DRIVES"},

                {"internal_id": car_id,
                 "rel_name": "DRIVES"}
            ]
        )

    # In spite of the Exception, above, a new node was indeed created
    match = db.match(labels = "PERSON", properties={"name": "Val"})
    lookup = db.get_nodes(match)
    assert lookup == [{"name": "Val", "city": "San Francisco"}]


    db.create_node_with_links(labels="ADDRESS",
                            properties={'state': 'CA', 'city': None},
                            links=[])
    match = db.match(labels = "ADDRESS", properties={"state": "CA"})
    lookup = db.get_nodes(match)
    assert lookup == [{"state": "CA"}]



def test_assemble_query_for_linking(db):
    with pytest.raises(Exception):
        db._assemble_query_for_linking(None)
        db._assemble_query_for_linking("I'm not a list :(")
        db._assemble_query_for_linking([])

        db._assemble_query_for_linking([{}])
        db._assemble_query_for_linking([{'rel_name': 'OWNS'}])

        db._assemble_query_for_linking([{'internal_id': 'do I look like a number??'}])
        db._assemble_query_for_linking([{'internal_id': 123}])


    result = db._assemble_query_for_linking([{"internal_id": 123, "rel_name": "LIVES IN"}])
    assert result == ('MATCH (ex0)', 'WHERE id(ex0) = 123', 'MERGE (n)-[:`LIVES IN` ]->(ex0)', {})

    result = db._assemble_query_for_linking([{"internal_id": 456, "rel_name": "EMPLOYS", "rel_dir": "IN"}])
    assert result == ('MATCH (ex0)', 'WHERE id(ex0) = 456', 'MERGE (n)<-[:`EMPLOYS` ]-(ex0)', {})

    result = db._assemble_query_for_linking([{"internal_id": 789, "rel_name": "OWNS", "rel_attrs": {"since": 2022}}])
    assert result == ('MATCH (ex0)', 'WHERE id(ex0) = 789', 'MERGE (n)-[:`OWNS` {`since`: $EDGE0_1}]->(ex0)', {'EDGE0_1': 2022})


    result = db._assemble_query_for_linking([{"internal_id": 123, "rel_name": "LIVES IN"} ,
                                             {"internal_id": 456, "rel_name": "EMPLOYS", "rel_dir": "IN"}])
    assert result == ('MATCH (ex0), (ex1)',
                      'WHERE id(ex0) = 123 AND id(ex1) = 456',
                      'MERGE (n)-[:`LIVES IN` ]->(ex0)\nMERGE (n)<-[:`EMPLOYS` ]-(ex1)',
                      {}
                     )


    result = db._assemble_query_for_linking(
                        [
                            {"internal_id": 123, "rel_name": "LIVES IN"},
                            {"internal_id": 456, "rel_name": "EMPLOYS", "rel_dir": "IN"},
                            {"internal_id": 789, "rel_name": "IS OWNED BY", "rel_dir": "IN", "rel_attrs": {"since": 2022, "tax rate": "X 23"}}
                        ])
    assert result == (
                        'MATCH (ex0), (ex1), (ex2)',
                        'WHERE id(ex0) = 123 AND id(ex1) = 456 AND id(ex2) = 789',
                        'MERGE (n)-[:`LIVES IN` ]->(ex0)\nMERGE (n)<-[:`EMPLOYS` ]-(ex1)\nMERGE (n)<-[:`IS OWNED BY` {`since`: $EDGE2_1, `tax rate`: $EDGE2_2}]-(ex2)',
                        {'EDGE2_1': 2022, 'EDGE2_2': "X 23"}
                      )




###  ~ DELETE NODES ~

def test_delete_nodes(db):
    db.empty_dbase()

    # Create 5 nodes, representing cars of various colors and prices
    df = pd.DataFrame({"color": ["white", "blue", "gray", "gray", "red"], "price": [100, 200, 300, 400, 500]})
    db.load_pandas(df, labels="car")

    # Add 1 airplane and a boat
    db.create_node("airplane", {"type": "747"})
    db.create_node("boat", {"brand": "Juneau"})

    # Delete the 2 gray cars
    match = db.match(labels="car", properties={"color": "gray"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 2
    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 3}]      # 3 cars left
    q = "MATCH (c:car {color:'gray'}) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 0}]      # 0 gray cars found

    # Attempting to re-delete them will produce a zero count
    match = db.match(labels="car", properties={"color": "gray"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 0
    q = "MATCH (c:car) RETURN count(c)"
    result = db.query(q)
    assert result == [{"count(c)": 3}]      # Still 3 cars left

    # Delete the red car
    match = db.match(labels="car", clause="n.color = 'red'")
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 1
    q = "MATCH (c:car) RETURN c.color AS col"
    result = db.query(q)
    assert compare_recordsets(result, [{'col': 'white'}, {'col': 'blue'}])  # white and blue cars are left

    # Attempting to delete a non-existing color will produce a zero count
    match = db.match(labels="car", properties={"color": "pink"})
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 0

    # Delete all the remaining 2 cars
    match = db.match(labels="car")
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
    match = db.match()
    number_deleted = db.delete_nodes(match)
    assert number_deleted == 2      # The airplane and the boat
    q = "MATCH (x) RETURN count(x)"
    result = db.query(q)
    assert result == [{"count(x)": 0}]  # Nothing left



def test_delete_nodes_by_label(db):
    db.delete_nodes_by_label()
    match = db.match()   # Everything in the dbase
    number_nodes = len(db.get_nodes(match))
    assert number_nodes == 0

    db.create_node("appetizers", {'name': 'spring roll'})
    db.create_node("vegetable", {'name': 'carrot'})
    db.create_node("vegetable", {'name': 'broccoli'})
    db.create_node("fruit", {'type': 'citrus'})
    db.create_node("dessert", {'name': 'chocolate'})

    assert len(db.get_nodes(match)) == 5

    db.delete_nodes_by_label(delete_labels="fruit")
    assert len(db.get_nodes(match)) == 4

    db.delete_nodes_by_label(delete_labels=["vegetable"])
    assert len(db.get_nodes(match)) == 2

    db.delete_nodes_by_label(delete_labels=["dessert", "appetizers"])
    assert len(db.get_nodes(match)) == 0

    # Rebuild the same dataset as before
    db.create_node("appetizers", {'name': 'spring roll'})
    db.create_node("vegetable", {'name': 'carrot'})
    db.create_node("vegetable", {'name': 'broccoli'})
    db.create_node("fruit", {'type': 'citrus'})
    db.create_node("dessert", {'name': 'chocolate'})

    db.delete_nodes_by_label(keep_labels=["dessert", "vegetable", "appetizers"])
    assert len(db.get_nodes(match)) == 4

    db.delete_nodes_by_label(keep_labels="dessert", delete_labels="dessert")
    # Keep has priority over delete
    assert len(db.get_nodes(match)) == 4

    db.delete_nodes_by_label(keep_labels="dessert")
    assert len(db.get_nodes(match)) == 1





###  ~ MODIFY FIELDS ~

def test_set_fields(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Create a new node.  Notice the blank in the key 'vehicle id'
    car_id = db.create_node("car", {'vehicle id': 123, 'price': 7500})

    # Locate the node just created, and create/update its attributes (add color plus make, and reduce the price)
    match = db.match(labels="car")
    n_set = db.set_fields(match=match, set_dict={"color": "white", "make": "Toyota", "price": 7000})
    assert n_set == 3

    # Look up the updated record
    match = db.match(labels="car")
    retrieved_records = db.get_nodes(match)
    expected_record_list = [{'vehicle id': 123, 'color': 'white', 'make': 'Toyota', 'price': 7000}]
    assert compare_recordsets(retrieved_records, expected_record_list)

    # Locate the node by a property and change the color attribute
    n_set = db.set_fields(match={'vehicle id': 123}, set_dict={"color": "   blue    "})  # Extra blanks will get stripped
    assert n_set == 1
    retrieved_records = db.get_nodes(car_id)
    expected_record_list = [{'vehicle id': 123, 'color': 'blue', 'make': 'Toyota', 'price': 7000}]
    assert compare_recordsets(retrieved_records, expected_record_list)

    # Locate the node by internal id and clear its "color" attribute
    n_set = db.set_fields(match=car_id, set_dict={"color": ""}, drop_blanks=False)
    assert n_set == 1
    retrieved_records = db.get_nodes(car_id)
    expected_record_list = [{'vehicle id': 123, 'color': '', 'make': 'Toyota', 'price': 7000}]    # 'color' property still there, but blank value
    assert compare_recordsets(retrieved_records, expected_record_list)

    # Locate the node by internal id and eliminate its "make" attribute
    n_set = db.set_fields(match=car_id, set_dict={"make": ""}, drop_blanks=True)
    assert n_set == 1
    retrieved_records = db.get_nodes(car_id)
    expected_record_list = [{'vehicle id': 123, 'color': '', 'price': 7000}]    # 'make' property is completely gone
    assert compare_recordsets(retrieved_records, expected_record_list)

    # Locate the node by internal id and eliminate its "price" attribute
    n_set = db.set_fields(match=car_id, set_dict={"price": None}, drop_blanks=False)
    assert n_set == 1
    retrieved_records = db.get_nodes(car_id)
    expected_record_list = [{'vehicle id': 123, 'color': ''}]    # 'price' property is completely gone
    assert compare_recordsets(retrieved_records, expected_record_list)

    # Locate the node by internal id and eliminate its "vehicle id" attribute to the SAME value it already has
    n_set = db.set_fields(match=car_id, set_dict={"vehicle id": 123})
    assert n_set == 1       # 1 property set - even if to the same value it already had
    retrieved_records = db.get_nodes(car_id)
    expected_record_list = [{'vehicle id': 123, 'color': ''}]    # No change
    assert compare_recordsets(retrieved_records, expected_record_list)





###  ~ RELATIONSHIPS ~

def test_get_relationship_types(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)
    rels = db.get_relationship_types()
    assert rels == []

    node1_id = db.create_node("Person", {'p_id': 1})
    node2_id = db.create_node("Person", {'p_id': 2})
    node3_id = db.create_node("Person", {'p_id': 3})
    db.link_nodes_by_ids(node1_id, node2_id, "LOVES")
    db.link_nodes_by_ids(node2_id, node3_id, "HATES")

    rels = db.get_relationship_types()
    assert set(rels) == {"LOVES", "HATES"}



def test_add_links(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_from = db.create_node("car", {'color': 'white'})
    neo_to = db.create_node("owner", {'name': 'Julian'})

    number_added = db.add_links(match_from=neo_from, match_to=neo_to, rel_name="OWNED_BY")
    assert number_added == 1

    q = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) AS number_cars, count(o) AS number_owners
        '''
    result = db.query(q, single_row=True)
    assert result == {'number_cars': 1, 'number_owners': 1}


    # Start over again
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_from = db.create_node("car", {'color': 'white'})
    neo_to = db.create_node("owner", {'name': 'Julian'})

    match_from = db.match(internal_id=neo_from) # , dummy_node_name="from"
    match_to = db.match(internal_id=neo_to)     # , dummy_node_name="to"

    number_added = db.add_links(match_from, match_to, rel_name="OWNED_BY")
    assert number_added == 1

    q = '''MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) AS number_cars, count(o) AS number_owners'''
    result = db.query(q, single_row=True)
    assert result == {'number_cars': 1, 'number_owners': 1}


    # Start over again
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_from = db.create_node("car", {'color': 'white'})
    neo_to = db.create_node("owner", {'name': 'Julian'})

    match_from = db.match(internal_id=neo_from)

    # Mix-and-match a match structure and an internal Neo ID
    number_added = db.add_links(match_from=match_from, match_to=neo_to, rel_name="OWNED_BY")
    assert number_added == 1

    q = '''MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) AS number_cars, count(o) AS number_owners'''
    result = db.query(q, single_row=True)
    assert result == {'number_cars': 1, 'number_owners': 1}


    # Make a link from the "car" node to itself
    assert db.add_links(match_from, match_from, rel_name="FROM CAR TO ITSELF") # Note the blanks in the name
    assert number_added == 1

    q = '''MATCH (c:car)-[:`FROM CAR TO ITSELF`]->(c) 
        RETURN count(c) AS number_cars'''
    result = db.query(q, single_row=True)
    assert result == {'number_cars': 1}



def test_add_links_fast(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_from = db.create_node("car", {'color': 'white'})
    neo_to = db.create_node("owner", {'name': 'Julian'})

    number_added = db.add_links_fast(match_from=neo_from, match_to=neo_to, rel_name="OWNED_BY")
    assert number_added == 1

    q = '''MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) AS number_cars, count(o) AS number_owners'''
    result = db.query(q, single_row=True)

    assert result == {'number_cars': 1, 'number_owners': 1}


    # Make a link from the "car" node to itself
    assert db.add_links_fast(neo_from, neo_from, rel_name="FROM CAR TO ITSELF") # Note the blanks in the name
    assert number_added == 1

    q = '''MATCH (c:car)-[:`FROM CAR TO ITSELF`]->(c) 
        RETURN count(c) AS number_cars'''
    result = db.query(q, single_row=True)
    assert result == {'number_cars': 1}



def test_remove_edges(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_car = db.create_node("car", {'color': 'white'})
    neo_julian = db.create_node("owner", {'name': 'Julian'})

    number_added = db.add_links(neo_car, neo_julian, rel_name="OWNED_BY")
    assert number_added == 1

    match_car = db.match(labels="car", dummy_node_name="from")
    match_julian = db.match(properties={"name": "Julian"}, dummy_node_name="to")

    find_query = '''
        MATCH (c:car)-[:OWNED_BY]->(o:owner) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 1     # Find the relationship

    with pytest.raises(Exception):
        assert db.remove_links(match_car, match_julian, rel_name="NON_EXISTENT_RELATIONSHIP")

    with pytest.raises(Exception):
        assert db.remove_links({"NON-sensical match object"}, match_julian, rel_name="OWNED_BY")

    # Finally, actually remove the edge
    number_removed = db.remove_links(match_car, match_julian, rel_name="OWNED_BY")
    assert number_removed == 1

    result = db.query(find_query)
    assert result[0]["n_cars"] == 0     # The relationship is now gone

    with pytest.raises(Exception):
        # This will crash because the relationship is no longer there
        assert db.remove_links(match_car, match_car, rel_name="OWNED_BY")

    with pytest.raises(Exception):
        # This will crash because the first 2 arguments are both using the same `dummy_node_name`
        assert db.remove_links(match_car, match_car, rel_name="THIS_WILL_CRASH")


    # Restore the relationship...
    number_added = db.add_links(match_car, match_julian, rel_name="OWNED_BY")
    assert number_added == 1

    # ...and add a 2nd one, with a different name, between the same nodes
    number_added = db.add_links(match_car, match_julian, rel_name="REMEMBERED_BY")
    assert number_added == 1

    # ...and re-add the last one, but with a property (which is allowed by Neo4j, and will result in
    #       2 relationships with the same name between the same node
    add_query = '''
        MATCH (c:car), (o:owner)
        MERGE (c)-[:REMEMBERED_BY {since: 2020}]->(o)
    '''
    result = db.update_query(add_query)
    assert result == {'_contains_updates': True, 'relationships_created': 1, 'properties_set': 1, 'returned_data': []}
    # Note: '_contains_updates': True  was added in version 4.4 of Neo4j

    # Also, add a 3rd node, and another "OWNED_BY" relationship, this time affecting the 3rd node
    add_query = '''
        MATCH (c:car)
        MERGE (c)-[:OWNED_BY]->(o :owner {name: 'Val'})
    '''
    result = db.update_query(add_query)
    assert result == {'_contains_updates': True, 'labels_added': 1, 'relationships_created': 1, 'nodes_created': 1,
                      'properties_set': 1, 'returned_data': []}
    # Note: '_contains_updates': True  was added in version 4.4 of Neo4j

    # We now have a car with 2 owners: an "OWNED_BY" relationship to one of them,
    # and 3 relationships (incl. two with the same name "REMEMBERED_BY") to the other one

    find_query = '''
        MATCH (c:car)-[:REMEMBERED_BY]->(o:owner ) 
        RETURN count(c) As n_cars
    '''
    result = db.query(find_query)
    assert result[0]["n_cars"] == 2     # The 2 relationships we just added

    # Remove 2 same-named relationships at once between the same 2 nodes
    number_removed = db.remove_links(match_car, match_julian, rel_name="REMEMBERED_BY")
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


    number_removed = db.remove_links(match_car, match_julian, rel_name="OWNED_BY")
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
    assert result == {'_contains_updates': True, 'relationships_created': 1, 'returned_data': []}
    # Note: '_contains_updates': True  was added in version 4.4 of Neo4j

    find_query = '''
        MATCH (c:car)-[r]->(o:owner {name: 'Val'}) 
        RETURN count(r) As n_relationships
    '''
    result = db.query(find_query)
    assert result[0]["n_relationships"] == 2

    # Delete both relationships at once
    match_val = db.match(key_name="name", key_value="Val", dummy_node_name="v")

    number_removed = db.remove_links(match_car, match_val, rel_name=None)
    assert number_removed == 2

    result = db.query(find_query)
    assert result[0]["n_relationships"] == 0    # All gone



def test_remove_edges_2(db):
    # This set of test focuses on removing edges between GROUPS of nodes
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

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
    assert result == {'_contains_updates': True, 'labels_added': 4, 'relationships_created': 4,
                      'nodes_created': 4, 'properties_set': 4, 'returned_data': []}
    # Note: '_contains_updates': True  was added in version 4.4 of Neo4j

    match_white_car = db.match(labels="car", properties={"color": "white"}, dummy_node_name="from")  # 1-node match
    match_all_people = db.match(labels="person", dummy_node_name="to")                               # 2-node match


    find_query = '''
        MATCH (c :car {color:'white'})-[r:OWNED_BY]->(p : person) 
        RETURN count(r) As n_relationships
    '''
    result = db.query(find_query)
    assert result[0]["n_relationships"] == 2        # The white car has 2 links

    # Delete all the "OWNED_BY" relationships from the white car to any of the "person" nodes
    number_removed = db.remove_links(match_white_car, match_all_people, rel_name="OWNED_BY")
    assert number_removed == 2

    result = db.query(find_query)
    assert result[0]["n_relationships"] == 0       # The 2 links from the white car are now gone



def test_edges_exists(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_car = db.create_node("car", {'color': 'white'})
    neo_julian = db.create_node("owner", {'name': 'Julian'})

    assert not db.links_exist(neo_car, neo_julian, rel_name="OWNED_BY")    # No relationship exists yet

    db.add_links(neo_car, neo_julian, rel_name="OWNED_BY")
    assert db.links_exist(neo_car, neo_julian, rel_name="OWNED_BY")        # By now, it exists
    assert not db.links_exist(neo_julian, neo_car, rel_name="OWNED_BY")    # But not in the reverse direction
    assert not db.links_exist(neo_car, neo_julian, rel_name="DRIVEN BY")   # Nor by a different name

    db.add_links(neo_car, neo_julian, rel_name="DRIVEN BY")
    assert db.links_exist(neo_car, neo_julian, rel_name="DRIVEN BY")       # Now it exists

    db.remove_links(neo_car, neo_julian, rel_name="DRIVEN BY")
    assert not db.links_exist(neo_car, neo_julian, rel_name="DRIVEN BY")   # Now it's gone

    neo_sailboat = db.create_node("sailboat", {'type': 'sloop', 'color': 'white'})
    db.add_links(neo_julian, neo_sailboat, rel_name="SAILS")
    assert db.links_exist(neo_julian, neo_sailboat, rel_name="SAILS")

    match_vehicle = db.match(properties={'color': 'white'})                 # To select both car and boat
    assert db.links_exist(neo_julian, match_vehicle, rel_name="SAILS")

    assert not db.links_exist(neo_car, neo_car, rel_name="SELF_DRIVES")     # A relationship from a node to itself
    db.add_links(neo_car, neo_car, rel_name="SELF_DRIVES")
    assert db.links_exist(neo_car, neo_car, rel_name="SELF_DRIVES")



def test_number_of_links(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    neo_car = db.create_node("car", {'color': 'white'})
    neo_julian = db.create_node("owner", {'name': 'Julian'})

    assert db.number_of_links(neo_car, neo_julian, rel_name="OWNED_BY") == 0    # No relationship exists yet

    db.add_links(neo_car, neo_julian, rel_name="OWNED_BY")
    assert db.number_of_links(neo_car, neo_julian, rel_name="OWNED_BY") == 1    # By now, it exists
    assert db.number_of_links(neo_julian, neo_car, rel_name="OWNED_BY") == 0    # But not in the reverse direction
    assert db.number_of_links(neo_car, neo_julian, rel_name="DRIVEN BY") == 0   # Nor by a different name

    db.add_links(neo_car, neo_julian, rel_name="DRIVEN BY")
    assert db.number_of_links(neo_car, neo_julian, rel_name="DRIVEN BY") == 1   # Now it exists with this other name

    db.remove_links(neo_car, neo_julian, rel_name="DRIVEN BY")
    assert db.number_of_links(neo_car, neo_julian, rel_name="DRIVEN BY") == 0   # Now it's gone

    neo_sailboat = db.create_node("sailboat", {'type': 'sloop', 'color': 'white'})
    db.add_links(neo_julian, neo_sailboat, rel_name="SAILS")
    assert db.number_of_links(neo_julian, neo_sailboat, rel_name="SAILS") == 1  # It finds the just-added link

    match_vehicle = db.match(properties={'color': 'white'})                      # To select both car and boat
    assert db.number_of_links(neo_julian, match_vehicle, rel_name="SAILS") == 1

    assert db.number_of_links(neo_car, neo_car, rel_name="SELF_DRIVES") == 0    # A relationship from a node to itself
    db.add_links(neo_car, neo_car, rel_name="SELF_DRIVES")
    assert db.number_of_links(neo_car, neo_car, rel_name="SELF_DRIVES") == 1    # Find the link to itself

    db.add_links(neo_sailboat, neo_julian, rel_name="OWNED_BY")
    assert db.number_of_links(match_vehicle, neo_julian, rel_name="OWNED_BY") == 2  # 2 vehicles owned by Julian



def test_get_node_internal_id(db):
    db.empty_dbase()

    match_all = db.match()              # Meaning "match everything"

    with pytest.raises(Exception):
        db.get_node_internal_id(match_all)  # No nodes yet exist

    # Add a 1st node
    adam_id = db.create_node(labels="Person", properties={"name": "Adam"})
    internal_id = db.get_node_internal_id(match_all)     # Finds all nodes (there's only 1 in the database)
    assert internal_id == adam_id

    # Add a 2nd node
    eve_id = db.create_node(labels="Person", properties={"name": "Eve"})

    with pytest.raises(Exception):
        db.get_node_internal_id(match_all)          # It finds 2 nodes - a non-unique result

    match_adam = db.match(properties={"name": "Adam"})
    internal_id = db.get_node_internal_id(match_adam)     # Finds the "Adam" node
    assert internal_id == adam_id

    match_eve = db.match(internal_id=eve_id)
    internal_id = db.get_node_internal_id(match_eve)     # Finds the "Eve" node
    assert internal_id == eve_id

    assert db.delete_nodes(match_adam) == 1         # Now only "Eve" will be left
    internal_id = db.get_node_internal_id(match_all)     # Finds the "Eve" node, because it's now the only one
    assert internal_id == eve_id



def test_reattach_node(db):
    db.empty_dbase()

    jack = db.create_node("Person", {"name": "Jack"})
    jill = db.create_attached_node("Person", properties={"name": "Jill"},
                            attached_to=jack, rel_name="MARRIED_TO", rel_dir="IN")
    mary = db.create_node("Person", {"name": "Mary"})

    with pytest.raises(Exception):
        db.reattach_node(node=jack, old_attachment=jill, new_attachment=mary, rel_name="UNKNOWN_RELATIONSHIP")   # No such relationship present

    with pytest.raises(Exception):
        db.reattach_node(node=jack, old_attachment=mary, new_attachment=jill, rel_name="MARRIED_TO")    # There's no link from jack to mary

    with pytest.raises(Exception):
        db.reattach_node(node=jill, old_attachment=jack, new_attachment=mary, rel_name="MARRIED_TO")    # here's no link FROM jill TO jack (wrong direction)

    bogus_internal_id = mary + 1     # (Since we first emptied the database, there will be no nod with such an ID
    with pytest.raises(Exception):
        db.reattach_node(node=jack, old_attachment=jill, new_attachment=bogus_internal_id, rel_name="MARRIED_TO")

    # jack finally shakes off jill and marries mary
    db.reattach_node(node=jack, old_attachment=jill, new_attachment=mary, rel_name="MARRIED_TO")

    q = '''
    MATCH (n1:Person)-[:MARRIED_TO]->(n2:Person) RETURN id(n1) AS ID_FROM, id(n2) AS ID_TO
    '''
    result = db.query(q)
    assert len(result) == 1
    assert result[0] == {"ID_FROM": jack, "ID_TO": mary}

    # Let's eliminate the "jill" node
    db.delete_nodes(jill)

    # jack cannot go back to jill, because she's gone!
    with pytest.raises(Exception):
        db.reattach_node(node=jack, old_attachment=mary, new_attachment=jill, rel_name="MARRIED_TO")

    # Let's re-introduce a "jill" node
    jill_2 = db.create_node("Person", {"name": "Jill"})

    # Now the indecisive jack can go back to jill (the new node with internal ID stored in jill_2)
    db.reattach_node(node=jack, old_attachment=mary, new_attachment=jill_2, rel_name="MARRIED_TO")

    q = '''
    MATCH (n1:Person)-[:MARRIED_TO]->(n2:Person) RETURN id(n1) AS ID_FROM, id(n2) AS ID_TO
    '''
    result = db.query(q)
    assert len(result) == 1
    assert result[0] == {"ID_FROM": jack, "ID_TO": jill_2}



def test_link_nodes_by_ids(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)
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
    db.empty_dbase(drop_indexes=True, drop_constraints=True)
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





######   ~ READ IN DATA from PANDAS ~  ######

def test_load_pandas_1(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Start with a single imported node
    df = pd.DataFrame([[123]], columns = ["col1"])  # One row, one column
    db.load_pandas(df, labels="A", ignore_nan=False)
    match_A = db.match(labels="A")  # To pull all nodes with a label "A"
    result = db.get_nodes(match_A)
    assert result == [{'col1': 123}]

    # Append a new single node
    df = pd.DataFrame([[999]], columns = ["col1"])
    db.load_pandas(df, labels="A", ignore_nan=True)
    result = db.get_nodes(match_A)
    expected = [{'col1': 123}, {'col1': 999}]
    assert compare_recordsets(result, expected)

    # Append a new single node
    df = pd.DataFrame([[2222]], columns = ["col2"])
    db.load_pandas(df, labels="A")
    result = db.get_nodes(match_A)
    expected = [{'col1': 123}, {'col1': 999}, {'col2': 2222}]
    assert compare_recordsets(result, expected)

    # Append a new single node
    df = pd.DataFrame([[3333]], columns = ["col3"])
    db.load_pandas(df, labels="B")
    A_nodes = db.get_nodes(match_A)
    expected_A = [{'col1': 123}, {'col1': 999}, {'col2': 2222}]
    assert compare_recordsets(A_nodes, expected_A)
    match_B = db.match(labels="B")  # To pull all nodes with a label "B"
    B_nodes = db.get_nodes(match_B)
    assert B_nodes == [{'col3': 3333}]


    db.load_pandas(df, labels="B", merge_primary_key=None)    # Re-add the same identical record
    B_nodes = db.get_nodes(match_B)
    assert B_nodes == [{'col3': 3333}, {'col3': 3333}]

    # Add a 2x2 dataframe
    df = pd.DataFrame({"col3": [100, 200], "name": ["Jack", "Jill"]})
    db.load_pandas(df, labels="A")
    A_nodes = db.get_nodes(match_A)
    expected = [{'col1': 123}, {'col1': 999}, {'col2': 2222}, {'col3': 100, 'name': 'Jack'}, {'col3': 200, 'name': 'Jill'}]
    assert compare_recordsets(A_nodes, expected)

    # Change the column names during import
    df = pd.DataFrame({"alternate_name": [1000]})
    db.load_pandas(df, labels="B", rename={"alternate_name": "col3"})     # Map "alternate_name" into "col3"
    B_nodes = db.get_nodes(match_B)
    expected_B = [{'col3': 3333}, {'col3': 3333}, {'col3': 1000}]
    assert compare_recordsets(B_nodes, expected_B)

    # Add 2 more records, with double labels
    df = pd.DataFrame({"patient_id": [100, 200], "name": ["Jack", "Jill"]})
    db.load_pandas(df, labels=["X", "Y"])
    match_X_Y = db.match(labels=["X", "Y"])
    X_Y_nodes = db.get_nodes(match_X_Y)
    expected_X_Y = [{'patient_id': 100, 'name': 'Jack'}, {'patient_id': 200, 'name': 'Jill'}]
    assert compare_recordsets(X_Y_nodes, expected_X_Y)


def test_load_pandas_2(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Add 3 records
    df = pd.DataFrame({"scientist_id": [10, 20, 30], "name": ["Julian", "Jack", "Jill"], "location": ["CA", "NY", "DC"]})
    id_list = db.load_pandas(df, labels="scientist", merge_primary_key=None)

    q = f'''
        MATCH (n :scientist) 
        WHERE id(n) IN {id_list}
        RETURN n
        '''
    res = db.query(q, single_column="n")
    expected = [{'name': 'Julian', 'location': 'CA', 'scientist_id': 10},
                {'name': 'Jack', 'location': 'NY', 'scientist_id': 20},
                {'name': 'Jill', 'location': 'DC', 'scientist_id': 30}]
    assert compare_recordsets(res, expected)

    # Update the "Julian" node, indexed by scientist_id (we'll modify the "name" of that node, and add a "specialty" field;
    # notice that the "location" field doesn't get altered)
    df = pd.DataFrame({"scientist_id": [10], "name": ["Julian W"], "specialty": ["Systems Biology"]})
    db.load_pandas(df, labels="scientist", merge_primary_key="scientist_id", merge_overwrite=False)
    q = "MATCH (n :scientist) RETURN n"
    res = db.query(q, single_column="n")
    expected = [{'specialty': 'Systems Biology', 'name': 'Julian W', 'location': 'CA', 'scientist_id': 10},
                {'name': 'Jack', 'location': 'NY', 'scientist_id': 20},
                {'name': 'Jill', 'location': 'DC', 'scientist_id': 30}]
    assert compare_recordsets(res, expected)

    # This time, completely replace the "Julian" node, indexed by scientist_id.
    # Notice how all the previous fields that aren't being set now, are gone ("specialty" and "location")
    df = pd.DataFrame({"scientist_id": [10], "name": ["Jules"]})
    db.load_pandas(df, labels="scientist", merge_primary_key="scientist_id", merge_overwrite=True)
    q = "MATCH (n :scientist) RETURN n"
    res = db.query(q, single_column="n")
    expected = [{'name': 'Jules', 'scientist_id': 10},
                {'name': 'Jack', 'location': 'NY', 'scientist_id': 20},
                {'name': 'Jill', 'location': 'DC', 'scientist_id': 30}]
    assert compare_recordsets(res, expected)


    # Verify that a database Index got created as a result of using merge_primary_key
    all_indexes = db.get_indexes()
    assert len(all_indexes) == 1
    # Investigate the 0-th (only) index
    assert all_indexes["name"][0] == 'scientist.scientist_id'
    assert all_indexes["labelsOrTypes"][0] == ['scientist']
    assert all_indexes["properties"][0] == ['scientist_id']


    # More tests of merge with primary_key
    df = pd.DataFrame({"patient_id": [100, 200], "name": ["Adam", "Eve"], "age": [21, 19]})
    db.load_pandas(df, labels="X")
    match_X = db.match(labels=["X"])
    X_nodes = db.get_nodes(match_X)
    expected = [{'patient_id': 100, 'name': 'Adam', 'age': 21}, {'patient_id': 200, 'name': 'Eve', 'age': 19}]
    assert compare_recordsets(X_nodes, expected)

    df = pd.DataFrame({"patient_id": [300, 200], "name": ["Remy", "Eve again"]})
    db.load_pandas(df, labels="X", merge_primary_key="patient_id", merge_overwrite=False)
    X_nodes = db.get_nodes(match_X)
    expected = [{'patient_id': 100, 'name': 'Adam', 'age': 21},
                {'patient_id': 300, 'name': 'Remy'},
                {'patient_id': 200, 'name': 'Eve again', 'age': 19}]    # Notice that Eve's name got changed, but her age
                                                                        #       was undisturbed b/c of merge_overwrite=False
    assert compare_recordsets(X_nodes, expected)

    df = pd.DataFrame({"patient_id": [300, 200], "name": ["Remy", "Eve YET again"]})
    db.load_pandas(df, labels="X", merge_primary_key="patient_id", merge_overwrite=True)
    X_nodes = db.get_nodes(match_X)
    expected = [{'patient_id': 100, 'name': 'Adam', 'age': 21},
                {'patient_id': 300, 'name': 'Remy'},
                {'patient_id': 200, 'name': 'Eve YET again'}]    # Notice that Eve's name got changed, and her age got dropped
    assert compare_recordsets(X_nodes, expected)

    # Verify that another database Index got created as a result of again using merge_primary_key
    all_indexes = db.get_indexes()
    assert len(all_indexes) == 2

    # There's no guarantee about the order of the Indices
    index_0 = list(all_indexes.iloc[0][["name", "labelsOrTypes", "properties"]])    # Selected cols from 0-th row
    index_1 = list(all_indexes.iloc[1][["name", "labelsOrTypes", "properties"]])    # Selected cols from 1st row
    expected_A = ['scientist.scientist_id', ['scientist'], ['scientist_id']]  # The old index
    expected_B = ['X.patient_id', ['X'], ['patient_id']]                      # The newly-added index

    assert (index_0 == expected_A) or (index_0 == expected_B)
    if index_0 == expected_A:
        assert index_1 == expected_B
    else:
        assert index_1 == expected_A



def test_load_pandas_3(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # First group on nodes to import
    ages = np.array([13, 25, 19, 99])
    series_1 = pd.Series(ages)    # A series with no name; during the import, "value" will be used
    id_list = db.load_pandas(series_1, labels="age")

    q = f'''
        MATCH (n :age) 
        WHERE id(n) IN {id_list}
        RETURN n
        '''
    res = db.query(q, single_column="n")
    expected = [{'value': 13}, {'value': 25}, {'value': 19}, {'value': 99}]
    assert compare_recordsets(res, expected)


    # More nodes to import
    prices = np.array([145, 512, 811])
    series_2 = pd.Series(prices, name="Discounted Price")   # This series has a bane
    id_list_2 = db.load_pandas(series_2, labels="store prices")

    # First, check that the old nodes are still there
    res = db.query(q, single_column="n")
    expected = [{'value': 13}, {'value': 25}, {'value': 19}, {'value': 99}]
    assert compare_recordsets(res, expected)
    # Now, look for the new nodes
    q = f'''
        MATCH (n :`store prices`) 
        WHERE id(n) IN {id_list_2}
        RETURN n
        '''
    res = db.query(q, single_column="n")
    expected = [{'Discounted Price': 145}, {'Discounted Price': 512}, {'Discounted Price': 811}]
    assert compare_recordsets(res, expected)


def test_load_pandas_4(db):
    # Test numeric columns
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # First group on nodes to import, with option to ignore NaN's
    df = pd.DataFrame({"name": ["pot", "pan", "microwave"], "price": [12, np.nan, 55]})
    db.load_pandas(df, labels="inventory", ignore_nan=True)

    imported_records = db.get_nodes(db.match(labels="inventory"))
    expected = [{'price': 12.0, 'name': 'pot'}, {'name': 'pan'}, {'price': 55.0, 'name': 'microwave'}]
    assert compare_recordsets(imported_records, expected)


    # Re-import the same dataframe (with a different label), but this time not ignoring NaN's
    db.load_pandas(df, labels="test", ignore_nan=False)

    imported_records = db.get_nodes(db.match(labels="test"), order_by="name")
    expected = [{'price': 55.0, 'name': 'microwave'}, {'price': np.nan, 'name': 'pan'}, {'price': 12.0, 'name': 'pot'}]
    # Check the records not involving NaN
    assert imported_records[0] == expected[0]
    assert imported_records[2] == expected[2]
    # Check the NaN record
    assert imported_records[1]["name"] == expected[1]["name"]
    assert np.isnan(imported_records[1]["price"])


def test_load_pandas_4b(db):
    # More tests of numeric columns
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Test with nans and ignore_nan = True
    df = pd.DataFrame({"name": ["Bob", "Tom"], "col1": [26, None], "col2": [1.1, None]})
    db.load_pandas(df, labels="X")
    X_label_match = db.match(labels="X")
    X_nodes = db.get_nodes(X_label_match)
    expected = [{'name': 'Bob', 'col1': 26, 'col2': 1.1},
                {'name': 'Tom'}]
    assert compare_recordsets(X_nodes, expected)


    # Test of record merge with nans and ignore_nan = False
    df = pd.DataFrame({"name": ["Bob", "Tom"], "col1": [26, None], "col2": [1.1, None]})
    db.load_pandas(df, labels="X", merge_primary_key='name', merge_overwrite=False, ignore_nan=False)
    X_nodes = db.get_nodes(X_label_match, order_by="name")
    expected = [{'name': 'Bob', 'col1': 26, 'col2': 1.1},
                {'name': 'Tom', 'col1': np.nan, 'col2': np.nan}]

    np.testing.assert_equal(X_nodes, expected)  # Two NaN's are treated as "equal" by this function


def test_load_pandas_4c(db):
    # Attempt to merge using columns with NULL values
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Attempt to merge using columns with NULL values
    df = pd.DataFrame({"name": ["Bob", "Tom"], "col1": [26, None], "col2": [1.1, None]})
    with pytest.raises(Exception):
        # Cannot merge node on NULL value in column `col1`
        db.load_pandas(df, labels="X", merge_primary_key='col1', merge_overwrite=False)

    with pytest.raises(Exception):
        # Cannot merge node on NULL value in column `col1`
        db.load_pandas(df, labels="X", merge_primary_key='col1', merge_overwrite=True)


def test_load_pandas_5(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # First group on 5 nodes to import
    df = pd.DataFrame({"name": ["A", "B", "C", "D", "E"], "price": [1, 2, 3, 4, 5]})
    db.load_pandas(df, labels="inventory")

    imported_records = db.get_nodes(db.match(labels="inventory"))
    expected = [{'price': 1, 'name': 'A'}, {'price': 2, 'name': 'B'}, {'price': 3, 'name': 'C'}, {'price': 4, 'name': 'D'}, {'price': 5, 'name': 'E'}]
    assert compare_recordsets(imported_records, expected)


    # Re-import them (with a different label) in tiny "import chunks" of size 2
    db.load_pandas(df, labels="test", max_chunk_size=2)

    imported_records = db.get_nodes(db.match(labels="test"))
    expected = [{'price': 1, 'name': 'A'}, {'price': 2, 'name': 'B'}, {'price': 3, 'name': 'C'}, {'price': 4, 'name': 'D'}, {'price': 5, 'name': 'E'}]
    assert compare_recordsets(imported_records, expected)
    # Verify that the first import is also still there
    imported_records = db.get_nodes(db.match(labels="inventory"))
    assert compare_recordsets(imported_records, expected)

    # Verify that the data (all the 10 records) got imported as integers
    q = "MATCH (n) WHERE toInteger(n.price) = n.price RETURN count(n) AS number_integers"
    res = db.query(q, single_cell="number_integers")
    assert res == 10


def test_load_pandas_6(db):
    # Test times/dates
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    # Dataframe with group of dates, turned into a datetime column
    df = pd.DataFrame({"name": ["A", "B", "C"], "arrival date": ["2020-01-01", "2020-01-11", "2020-01-21"]})
    df['arrival date'] = pd.to_datetime(df['arrival date'])
    id_list = db.load_pandas(df, labels="events")

    for node_id in id_list:
        cyp = db.property_data_type_cypher()
        q = f'''MATCH (n :events) WHERE id(n) = {node_id} RETURN {cyp}(n.`arrival date`) AS dtype'''
        res = db.query(q, single_cell="dtype")
        assert res == "LocalDateTime" or res == "LOCAL_DATE_TIME"
        # Respectively, for v.4 and v.5 of Neo4j


def test_load_pandas_7(db):
    # More tests of times/dates
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    df = pd.DataFrame([[datetime(2019, 6, 1, 18, 40, 32, 0), date(2019, 6, 1)]], columns=["dtm", "dt"])
    db.load_pandas(df, labels="MYTEST")
    result = db.query("MATCH (x:MYTEST) return x.dtm as dtm, x.dt as dt", single_row=True)
    print(result)
    assert result == {'dtm': neo4j.time.DateTime(2019, 6, 1, 18, 40, 32, 0), 'dt': neo4j.time.Date(2019, 6, 1)}


def test_load_pandas_8(db):
    # More tests of times/dates
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    input_df = pd.DataFrame({
        'int_values': [2, 1, 3, 4],
        'str_values': ['abc', 'def', 'ghi', 'zzz'],
        'start': [datetime(year=2010, month=1, day=1, hour=0, minute=1, second=2, microsecond=123),
                  datetime(year=2023, month=1, day=1),
                  pd.NaT,
                  None]
    })  # Note: for Pandas' datetime64[ns] types, NaT represents missing values

    db.load_pandas(input_df, "MYTEST")
    res = db.query("MATCH (x:MYTEST) RETURN x.start as start ORDER BY start")

    assert res == [{'start': neo4j.time.DateTime(2010, 1, 1, 0, 1, 2, 123000)},
                   {'start': neo4j.time.DateTime(2023, 1, 1, 0, 0, 0, 0)},
                   {'start': None}, {'start': None}]



def test_pd_datetime_to_neo4j_datetime(db):
    # Prepare a dataframe with group of dates, turned into a datetime column
    df = pd.DataFrame({"name": ["A", "B", "C"], "my_date": ["2023-01-01", np.nan, "2023-01-21"]})
    df['my_date'] = pd.to_datetime(df['my_date'])

    # First, check the original dataframe
    date_col = list(df.my_date) # [Timestamp('2023-01-01 00:00:00'), Timestamp('2023-01-11 00:00:00'), ...]
    first_dt = date_col[0]      # Timestamp('2023-01-01 00:00:00')
    assert first_dt == pd.Timestamp('2023-01-01 00:00:00')


    result = db.pd_datetime_to_neo4j_datetime(df)

    result_col = list(result.my_date)   # [neo4j.time.DateTime(2023, 1, 1, 0, 0, 0, 0), ... ]

    assert result_col[0] == neo4j.time.DateTime(2023, 1, 1, 0, 0, 0, 0)
    assert result_col[1] == None
    assert result_col[2] == neo4j.time.DateTime(2023, 1, 21, 0, 0, 0, 0)

    assert id(df) != id(result)     # A clone of the original dataframe was created


    # If a dataframe is using strings rather than datetime value, no change will be made to it
    df = pd.DataFrame({"name": ["A", "B"], "my_date": ["2023-01-01", "2023-01-21"]})

    result = db.pd_datetime_to_neo4j_datetime(df)
    result_col = list(result.my_date)
    assert result_col == ['2023-01-01', '2023-01-21']

    assert id(df) == id(result)     # No cloning took place




###  ~ JSON IMPORT/EXPORT ~

# =>  SEE test_neoaccess_import_export.py




###  ~ DEBUGGING SUPPORT ~


def test_debug_trim(db):
    assert db.debug_trim("hello") == "hello"
    assert db.debug_trim(44) == "44"
    assert db.debug_trim("1234567890", max_len=5) == "12345 ..."


def test_debug_trim_print(db):
    pass    # TODO



def test_indent_chooser(db):
    pass    # TODO
