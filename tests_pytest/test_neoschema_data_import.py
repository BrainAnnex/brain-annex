# Testing of Schema-based Data Import
# *** CAUTION! ***  The database gets cleared out during some of the tests!
# NOTES: - some tests require APOC
#        - some tests may fail their date check if done close to midnight, server time


import pytest
import pandas as pd
from neoaccess import NeoAccess
from brainannex.neo_schema.neo_schema import NeoSchema, SchemaCache
from test_neoschema import create_sample_schema_1, create_sample_schema_2
from brainannex.utilities.comparisons import *


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    NeoSchema.debug = False
    yield neo_obj



def test_import_pandas_nodes_1(db):
    db.empty_dbase()

    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    with pytest.raises(Exception):
        NeoSchema.import_pandas_nodes(df=df, class_name="State")    # Undefined Class

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="State",
                                           properties=["name"], strict=True)


    # Import all state with a particular batch size
    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=1)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    NeoSchema.delete_data_nodes(class_name="State")
    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=2)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    NeoSchema.delete_data_nodes(class_name="State")
    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=3)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    NeoSchema.delete_data_nodes(class_name="State")
    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=100)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)



def test_import_pandas_nodes_2(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="State",
                                           properties=["name"], strict=True)


    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    # Import all states with a large batch size, as done in test_import_pandas_nodes_1()
    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=100)
    assert import_result["number_nodes_created"] == 3


    # Prepare, and import, a second dataset
    df_2 = pd.DataFrame({"name": ["FL", "CA", "TX", "FL"]})    # Notice that "CA" is a duplicate from the earlier dataframe
                                                                # and that "FL" occurs twice

    # Import this second dataset with a medium batch size - and treat "name" as a unique primary key
    import_result = NeoSchema.import_pandas_nodes(df=df_2, class_name="State", primary_key="name",
                                                  max_batch_size=2)
    assert import_result["number_nodes_created"] == 2       # 2 of the 4 imports already existed



def test_import_pandas_nodes_3(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["vehicle ID", "make", "year"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  max_batch_size=2)
    assert import_result["number_nodes_created"] == 3
    assert len(import_result["affected_nodes_ids"]) == 3


    # Add more imports.  Note that "c2" is already present (if "vehicle ID" is a primary key),
    # and that "color" is not the Schema
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                              "color": ["red",       "white", "blue"]})

    with pytest.raises(Exception):      # "color" in not in the Schema
        NeoSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                      primary_key="vehicle ID")

    # Expand the Schema, to also include "color"
    NeoSchema.add_properties_to_class(class_node="Motor Vehicle", property_list=["color"])

    import_result_2 = NeoSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                    max_batch_size=2,
                                                    primary_key="vehicle ID", duplicate_option="merge")   # Duplicate records will be merged
    assert import_result_2["number_nodes_created"] == 2         # One of the 3 imports doesn't lead to node creation
    assert len(import_result_2["affected_nodes_ids"]) == 3      # 3 nodes were either created or updated

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'         # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013} # The duplicate record 'c2' was updated by the new one
                                                                                                # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                                # and the 'year' value was left untouched
    assert result[0]["internal_id"] in import_result_2["affected_nodes_ids"]
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    # Re-import the first 3 records
    import_result_1 = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle", max_batch_size=2)
    assert import_result_1["number_nodes_created"] == 3
    assert len(import_result_1["affected_nodes_ids"]) == 3

    # Re-import the next 3 records (one of which has a duplicate)
    import_result_2 = NeoSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                    max_batch_size=2,
                                                    primary_key="vehicle ID", duplicate_option="replace")   # Duplicate records will be REPLACED (not "merged") this time
    assert import_result_2["number_nodes_created"] == 2         # One of the 3 imports doesn't lead to node creation
    assert len(import_result_2["affected_nodes_ids"]) == 3      # 3 nodes were either created or updated

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'     # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1

    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white'}  # The duplicate record 'c2' was completely replaced by the new one
                                                                                    # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                    # and (unlike before) the 'year' value is gone
    assert result[0]["internal_id"] in import_result_2["affected_nodes_ids"]
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported



def test_import_pandas_nodes_4(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_result_1 = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    max_batch_size=2,
                                                    rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert import_result_1['number_nodes_created'] == 3
    import_car_list_1 = import_result_1['affected_nodes_ids']
    assert len(import_car_list_1) == 3

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2013, 'manufacturer': 'Toyota', 'internal_id': import_car_list_1[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], 'neo4j_labels': ['Motor Vehicle']}
               ]
    assert compare_recordsets(result, expected)


    # Note that "c2" is already present (if "vehicle ID" is a primary key)
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                               "year": [2005,        2015,    2025],
                              "color": ["red",       "white", "blue"]
                        })

    import_result_2 = NeoSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                    primary_key="vehicle ID", duplicate_option="merge",
                                                    rename={"vehicle ID": "VID", "make": "manufacturer"},
                                                    max_batch_size=2)
    assert import_result_2['number_nodes_created'] == 2     # Only 2 of the 3 records imported led to the creation of a new node
    import_car_list_2 = import_result_2['affected_nodes_ids']
    assert len(import_car_list_2) == 3                      # 3 nodes were either created or updated
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'manufacturer': 'BMW',    'internal_id': import_car_list_1[1], 'neo4j_labels': ['Motor Vehicle'], 'color': 'white'},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], 'neo4j_labels': ['Motor Vehicle']},

                {'VID': 'c4', 'color': 'red', 'year': 2005, 'manufacturer': 'Chevrolet', 'internal_id': import_car_list_2[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue', 'year': 2025, 'manufacturer': 'Fiat',     'internal_id': import_car_list_2[2], 'neo4j_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)

    assert import_car_list_1[1] == import_car_list_2[1]     # The "c2" record import (first created, then updated)



def test_import_pandas_nodes_5(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["VID", "make", "year", "color"], strict=True)

    # Notice that "c2" is a duplicate
    df = pd.DataFrame({  "VID":   ["c1",    "c2",     "c3",     "c4",        "c2",     "c5"],
                         "make":  ["Honda", "Toyota", "Ford",   "Chevrolet", "BMW",    "Fiat"],
                         "year":  [2003,    2013,     2023,     2005,        2015,     2025],
                         "color": ["red",  "white",   "black",  "pink",      "yellow", "blue"]})

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  primary_key="VID", duplicate_option="merge",
                                                  max_batch_size=3, drop="year")
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'color': 'red',    'make': 'Honda',     'internal_id': import_car_list[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'color': 'yellow', 'make': 'BMW',       'internal_id': import_car_list[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'color': 'black',  'make': 'Ford',      'internal_id': import_car_list[2], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'color': 'pink',   'make': 'Chevrolet', 'internal_id': import_car_list[3], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue',   'make': 'Fiat',      'internal_id': import_car_list[5], 'neo4j_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  primary_key="VID", duplicate_option="merge",
                                                  max_batch_size=2, select=["VID", "make", "color"])
    # Notice that the 3 fields we're selected have the identical effect as the dropping of "year" we did before;
    # also, changing the max_chunk_size.  All the results will be identical to before

    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'color': 'red',    'make': 'Honda',     'internal_id': import_car_list[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'color': 'yellow', 'make': 'BMW',       'internal_id': import_car_list[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'color': 'black',  'make': 'Ford',      'internal_id': import_car_list[2], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'color': 'pink',   'make': 'Chevrolet', 'internal_id': import_car_list[3], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue',   'make': 'Fiat',      'internal_id': import_car_list[5], 'neo4j_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)



def test_import_pandas_nodes_6(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["VID", "make", "year", "color"], strict=True)

    # Notice that "c2" is a duplicate
    df = pd.DataFrame({  "VID":   ["c1",    "c2",     "c3",     "c4",        "c2",     "c5"],
                         "make":  ["Honda", "Toyota", "Ford",   "Chevrolet", "BMW",    "Fiat"],
                         "year":  [2003,    2013,     2023,     2005,        2015,     2025],
                         "color": ["red",  "white",   "black",  "pink",      "yellow", "blue"]})

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  primary_key="VID", duplicate_option="merge",
                                                  max_batch_size=4, drop=["make", "color"])

    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'internal_id': import_car_list[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'internal_id': import_car_list[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'internal_id': import_car_list[2], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'year': 2005, 'internal_id': import_car_list[3], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'year': 2025, 'internal_id': import_car_list[5], 'neo4j_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  primary_key="VID", duplicate_option="merge",
                                                  max_batch_size=10, select="VID")

    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'internal_id': import_car_list[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'internal_id': import_car_list[2], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'internal_id': import_car_list[3], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'internal_id': import_car_list[5], 'neo4j_labels': ['Motor Vehicle']}
               ]

    assert compare_recordsets(result, expected)


    # Another fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                  max_batch_size=10, select="VID")
    # This time, NOT specifying a primary_key

    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 6      # Verify that ALL Data Nodes were imported this time
    assert import_result['number_nodes_created'] == 6
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 6                   # 6 unique values (the internal ID for node "c2" repeats twice)

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'internal_id': import_car_list[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'internal_id': import_car_list[2], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'internal_id': import_car_list[3], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[4], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'internal_id': import_car_list[5], 'neo4j_labels': ['Motor Vehicle']}
               ]

    assert compare_recordsets(result, expected)



def test_import_pandas_nodes_7(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"VID": ["c1",    "c2",     "c3"],
                      "make": ["Honda", "Toyota", "Ford"],
                      "year": [2003,    2013,     2023]})

    with pytest.raises(Exception):
        NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                      primary_key="non_existent")     # Primary key not in the dataframe

    with pytest.raises(Exception):
        NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                      primary_key="VID", drop="VID")     # Primary key is a dropped column

    with pytest.raises(Exception):
        NeoSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                      primary_key="VID", drop=["VID", "year"])     # Primary key is a dropped column






def test_import_pandas_nodes_1_OLD(db):
    db.empty_dbase()

    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    with pytest.raises(Exception):
        NeoSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="State")    # Undefined Class

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="State",
                                           properties=["name"], strict=True)

    import_state_list_1 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="State")

    # Verify that 3 Data Node were imported
    assert len(import_state_list_1) == 3
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 3

    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")

    assert compare_unordered_lists(result, import_state_list_1)


    # Duplicate entry: "CA" (from new dataset to be added to the previous one)
    df_2 = pd.DataFrame({"name": ["NV", "CA", "WA"]})

    import_state_list_2 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="State",
                                                                 primary_key="name")

    # Verify that a grand total of only 5 Data Node were imported (i.e.,
    # the duplicate didn't lead to an extra record)
    assert len(import_state_list_2) == 2
    assert NeoSchema.count_data_nodes_of_class(class_name="State") == 5

    q = '''
        UNWIND ["CA", "NY", "OR", "NV", "WA"] AS state_name
        MATCH (s :State {name:state_name})-[:SCHEMA]-(:CLASS {name: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")

    assert set(result) == set(import_state_list_1).union(set(import_state_list_2))


    # Expand the Schema with a new Class
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["vehicle ID", "make", "year"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_car_list_1 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle")


    assert len(import_car_list_1) == 3

    # Note that "c2" is already present (if "vehicle ID" is a primary key),
    # and that "color" is not the Schema
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                              "color": ["red",       "white", "blue"]})

    with pytest.raises(Exception):      # "color" in not in the Schema
        NeoSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                               primary_key="vehicle ID")

    NeoSchema.add_properties_to_class(class_node="Motor Vehicle", property_list=["color"])

    import_car_list_2 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                               primary_key="vehicle ID", duplicate_option="merge")   # Duplicate records will be merged
    assert len(import_car_list_2) == 2

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'         # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013} # The duplicate record 'c2' was updated by the new one
                                                                                                # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                                # and the 'year' value was left untouched
    assert result[0]["internal_id"] in import_car_list_1
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    # Re-import the first 3 records
    import_car_list_1 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle")
    assert len(import_car_list_1) == 3

    # Re-import the next 3 records (one of which has a duplicate)
    import_car_list_2 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                               primary_key="vehicle ID", duplicate_option="replace")   # Duplicate records will be REPLACED (not "merged") this time
    assert len(import_car_list_2) == 2

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'     # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1

    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white'}  # The duplicate record 'c2' was completely replaced by the new one
                                                                                    # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                    # and (unlike before) the 'year' value is gone
    assert result[0]["internal_id"] in import_car_list_1
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported


def test_import_pandas_nodes_2_OLD(db):
    db.empty_dbase()

    # Populate the Schema
    NeoSchema.create_class_with_properties(name="Motor Vehicle",
                                           properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_car_list_1 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle",
                                                               rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert len(import_car_list_1) == 3

    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2013, 'manufacturer': 'Toyota', 'internal_id': import_car_list_1[1], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], 'neo4j_labels': ['Motor Vehicle']}
               ]
    assert compare_recordsets(result, expected)


    # Note that "c2" is already present (if "vehicle ID" is a primary key)
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                               "year": [2005,        2015,    2025],
                              "color": ["red",       "white", "blue"]
                        })

    import_car_list_2 = NeoSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                               primary_key="vehicle ID", duplicate_option="merge",
                                                               rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert len(import_car_list_2) == 2
    assert NeoSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    result = NeoSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'manufacturer': 'BMW',    'internal_id': import_car_list_1[1], 'neo4j_labels': ['Motor Vehicle'], 'color': 'white'},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], 'neo4j_labels': ['Motor Vehicle']},

                {'VID': 'c4', 'color': 'red', 'year': 2005, 'manufacturer': 'Chevrolet', 'internal_id': import_car_list_2[0], 'neo4j_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue', 'year': 2025, 'manufacturer': 'Fiat',     'internal_id': import_car_list_2[1], 'neo4j_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)

    # TODO: test "drop", "select"

    q = f'''
        MATCH (n :`Motor Vehicle`) WHERE id(n) IN {import_car_list_2}
        RETURN n
        '''

    # TODO: more tests; see also the tests for NeoAccess.load_pandas()



def test_import_pandas_links(db):
    db.empty_dbase()
    NeoSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties, based on the data to import
    NeoSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    NeoSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Now add a relationship named "IS_IN", from the "City" Class to the "State" Class
    NeoSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3], "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate table ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"State ID": [1, 1, 2, 3], "City ID": [1, 3, 2, 4]})

    # Import the data nodes
    city_node_ids = NeoSchema.import_pandas_nodes_NO_BATCH(df=city_df, class_name="City")
    assert len(city_node_ids) == 4

    state_node_ids = NeoSchema.import_pandas_nodes_NO_BATCH(df=state_df, class_name="State")
    assert len(state_node_ids) == 3

    # Now import the links
    link_ids = NeoSchema.import_pandas_links(df=state_city_links_df,
                                             class_from="City", class_to="State",
                                             col_from="City ID", col_to="State ID",
                                             link_name="IS_IN")
    assert len(link_ids) == 4

    assert NeoSchema.data_link_exists(node_1_id="Berkeley", node_2_id="California", id_key="name", rel_name="IS_IN")
    assert NeoSchema.data_link_exists(node_1_id="San Francisco", node_2_id="California", id_key="name", rel_name="IS_IN")
    assert NeoSchema.data_link_exists(node_1_id="New York City", node_2_id="New York", id_key="name", rel_name="IS_IN")
    assert NeoSchema.data_link_exists(node_1_id="Chicago", node_2_id="Illinois", id_key="name", rel_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)



def test_create_tree_from_dict_1(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="address",
                                           properties=["state", "city"])

    # Import a data dictionary
    data = {"state": "California", "city": "Berkeley"}
    cache = SchemaCache()    # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of a new node, with 2 attributes, named "state" and "city"
    root_neo_id = NeoSchema.create_tree_from_dict(data, class_name="address", cache=cache)
    #print(root_neo_id)
    assert root_neo_id is not None

    q = '''
    MATCH (root :address {state: "California", city: "Berkeley"})
    -[:SCHEMA]->(c : CLASS {name: "address"})
    WHERE id(root) = $root_neo_id
    RETURN root
    '''

    root_node = db.query(q, data_binding={"root_neo_id": root_neo_id})
    assert root_node == [{'root': {'city': 'Berkeley', 'state': 'California'}}]



def test_create_tree_from_dict_2(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="person",
                                           properties=["name"])
    NeoSchema.create_class_with_properties(name="address",
                                           properties=["state", "city"])

    NeoSchema.create_class_relationship(from_class="person", to_class="address", rel_name="address")

    # Import a data dictionary
    data = {"name": "Julian", "address": {"state": "California", "city": "Berkeley"}}
    cache = SchemaCache()   # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of 2 nodes, namely the tree root (with a single attribute "name"), with
    # an outbound link named "address" to another node (the subtree) that has the "state" and "city" attributes
    root_neo_id = NeoSchema.create_tree_from_dict(data, class_name="person", cache=cache)
    #print(root_neo_id)

    assert root_neo_id is not None


    q = '''
    MATCH (c1 :CLASS {name: "person"})<-[:SCHEMA]-
    (root :person {name: "Julian"})-[:address]->
    (a :address {state: "California", city: "Berkeley"})
    -[:SCHEMA]->(c2 :CLASS {name: "address"})
    WHERE id(root) = $root_neo_id
    RETURN root
    '''

    root_node = db.query(q, data_binding={"root_neo_id": root_neo_id})
    assert root_node == [{'root': {'name': 'Julian'}}]



####################################################################################################

def test_create_tree_from_list_1(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="address",
                                           properties=["state", "city"])

    # Import a data dictionary
    data = [{"state": "California", "city": "Berkeley"}, {"state": "Texas", "city": "Dallas"}]
    cache = SchemaCache()       # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of two new nodes, each with 2 attributes, named "state" and "city"
    root_neo_id_list = NeoSchema.create_trees_from_list(data, class_name="address", cache=cache)
    #print(root_neo_id_list)

    assert root_neo_id_list is not None

    q = '''
    MATCH (root1 :address {state: "California", city: "Berkeley"})
    -[:SCHEMA]->(c : CLASS {name: "address"})
    <-[:SCHEMA]-(root2 :address {state: "Texas", city: "Dallas"})
    RETURN id(root1) as id_1, id(root2) as id_2
    '''

    result = db.query(q)
    #print(result)   # EXAMPLE: [{'id_1': 8, 'id_2': 9}]
    actual_root_ids_dict = result[0]
    actual_root_ids_list = [actual_root_ids_dict['id_1'], actual_root_ids_dict['id_2']]
    assert actual_root_ids_list == root_neo_id_list \
           or actual_root_ids_list == root_neo_id_list.reverse()   # The order isn't guaranteed




def test_create_tree_from_list_2(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="address",
                                           properties=["value"])

    # Import a data dictionary
    data = ["California", "Texas"]
    cache = SchemaCache()       # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of two new nodes, each with a property by default named "value"
    root_neo_id_list = NeoSchema.create_trees_from_list(data, class_name="address", cache=cache)
    #print("root_neo_id_list: ", root_neo_id_list)

    assert len(root_neo_id_list) == 2

    q = '''
    MATCH (root1 :address {value: "California"})
    -[:SCHEMA]->(c : CLASS {name: "address"})
    <-[:SCHEMA]-(root2 :address {value: "Texas"})
    RETURN id(root1) as id_1, id(root2) as id_2
    '''

    result = db.query(q)
    #print(result)   # EXAMPLE: [{'id_1': 8, 'id_2': 9}]

    actual_root_ids_dict = result[0]
    actual_root_ids_list = [actual_root_ids_dict['id_1'], actual_root_ids_dict['id_2']]
    assert actual_root_ids_list == root_neo_id_list \
           or actual_root_ids_list == root_neo_id_list.reverse()   # The order isn't guaranteed



####################################################################################################

def test_create_data_nodes_from_python_data_1(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])

    NeoSchema.create_class_with_properties(name="my_class_1",
                                           properties=["legit", "other"])

    NeoSchema.create_class_relationship(from_class="Import Data", to_class="my_class_1", rel_name="imported_data")


    # 1-layer dictionary, with a key in the Schema and one not

    data = {"legit": 123, "unexpected": 456}
    # Import step
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="my_class_1")

    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH (c1:CLASS {name:"Import Data"})<-[:SCHEMA]-
              (n1:`Import Data`)-[:imported_data]->(n2:my_class_1)
              -[:SCHEMA]->(c2:CLASS {name:"my_class_1"})
        WHERE id(n2) = $uri
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"uri": root_id}, single_row=True)

    root_record = root_node["n2"]
    assert root_record["legit"] == 123
    #assert "uri" in root_record            # Not currently is use
    assert "unexpected" not in root_record      # Only the key in the Schema gets imported



def test_create_data_nodes_from_python_data_2(db):
    db.empty_dbase()

    # Set up the Schema.  Nothing in it yet, other than the "Import Data" node
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])


    data = {"arbitrary": "Doesn't matter"}

    # Import step
    with pytest.raises(Exception):
        NeoSchema.create_data_nodes_from_python_data(data, class_name="non_existent_class")

    # Even though the import got aborted and raised an Exception, the `Import Data` is left behind;
    # locate it by its date stamp
    q = '''
        MATCH (n:`Import Data` {date: date()}) RETURN n
        '''
    result = db.query(q)
    assert len(result) == 1



def test_create_data_nodes_from_python_data_3(db):
    db.empty_dbase()

    # Set up Schema that only contains parts of the attributes in the data - and lacks the "result" relationship
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_with_properties(name="patient",
                                           properties=["age", "balance"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "result": {
                    "biomarker": "insulin",
                    "value": 123.
                },
                "balance": 150.25,
                "extraneous": "I don't belong",
                "insurance": False
                }

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH (c1:CLASS {name:"Import Data"})<-[:SCHEMA]-
              (n1:`Import Data`)-[:imported_data]->(n2:patient)
              -[:SCHEMA]->(c2:CLASS {name:"patient"})
        WHERE id(n2) = $uri
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"uri": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    root_record = root_node["n2"]
    assert root_record["age"] == 23
    assert root_record["balance"] == 150.25
    #assert "uri" in root_record            # Not currently is use
    assert len(root_record) == 2     # Only the keys in the Schema gets imported

    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    res = db.query(q)
    assert len(res) == 0         # "result" is not in the Schema



def test_create_data_nodes_from_python_data_4(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "result": {         # Note: this doesn't match the "HAS_RESULT" in the Schema
                    "biomarker": "insulin",
                    "value": 123.
                },
                "balance": 150.25,
                "extraneous": "I don't belong",
                "insurance": False
                }

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH (c1:CLASS {name:"Import Data"})<-[:SCHEMA]-
              (n1:`Import Data`)-[:imported_data]->(n2:patient)
              -[:SCHEMA]->(c2:CLASS {name:"patient"})
        WHERE id(n2) = $root_id
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"root_id": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    root_record = root_node["n2"]

    assert root_record["name"] == "Stephanie"
    assert root_record["age"] == 23
    assert root_record["balance"] == 150.25
    #assert "uri" in root_record        # Not currently is use
    assert len(root_record) == 3            # Only the keys in the Schema gets imported

    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    res = db.query(q)
    assert len(res) == 0    # the relationship "result" is not in the Schema

    # Count the links from the "patient" data node (the root)
    assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=root_id, rel_name="result", rel_dir="BOTH") == 0



def test_create_data_nodes_from_python_data_5(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "HAS_RESULT": {
                    "biomarker": "insulin",
                    "value": 123.,
                    "intruder": "the schema doesn't know me"
                },
                "balance": 150.25,
                "extraneous": "I don't belong",
                "WRONG_LINK_TO_DOCTOR" : {
                    "name": "Dr. Kane",
                    "hospital": "Mt. Zion",
                    "specialty": "OB/GYN"
                },
                "insurance": False
            }

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]


    # Traverse a loop in the graph, from the patient data node, back to itself,
    # and finally to the `Import Data` node - going thru data and schema nodes
    q = '''
        MATCH (p:patient {name: "Stephanie", age: 23, balance: 150.25})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0})-[:SCHEMA]->(cl_r:CLASS {name:"result"})
            <-[:HAS_RESULT]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)<-[:imported_data]-(i: `Import Data`)
        WHERE i.date = date() AND id(p) = $root_id
        RETURN p, r, cl_r, cl_p, i
        '''
    result = db.query(q, data_binding={"root_id": root_id})

    #print(result)
    # Only the keys in the Schema gets imported; the relationship "HAS_RESULT" is in the Schema
    assert len(result) == 1

    # The relationship "WRONG_LINK_TO_DOCTOR" is not in the Schema
    q = '''MATCH (n:patient)-[:WRONG_LINK_TO_DOCTOR]-(m) RETURN n, m'''
    result = db.query(q)
    assert len(result) == 0

    # Count the links from the "patient" data node (the root)
    assert db.count_links(match=root_id, rel_name="HAS_RESULT", rel_dir="OUT", neighbor_labels="result") == 1
    assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=root_id, rel_name="WRONG_LINK_TO_DOCTOR", rel_dir="BOTH") == 0

    # Locate the "result" data node, and count the links in/out of it
    match = db.match(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1



def test_create_data_nodes_from_python_data_6(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")

    # Some of the data below is not registered in the Schema
    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "HAS_RESULT": {
                    "biomarker": "insulin",
                    "value": 123.,
                    "intruder": "the schema doesn't know me"
                },
                "balance": 150.25,
                "extraneous": "I don't belong",
                "IS_ATTENDED_BY" : {
                    "name": "Dr. Kane",
                    "hospital": "Mt. Zion",
                    "specialty": "OB/GYN"
                },
                "insurance": False
                }

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]


    # Traverse a loop in the graph, from the patient data node, back to itself,
    # and finally to the `Import Data` node - going thru data and schema nodes
    q = '''
        MATCH (p:patient {name: "Stephanie", age: 23, balance: 150.25})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0})-[:SCHEMA]->(cl_r:CLASS {name:"result"})
            <-[:HAS_RESULT]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)<-[:imported_data]-(i: `Import Data`)
        WHERE i.date = date() AND id(p) = $root_id
        RETURN p, r, cl_r, cl_p, i
        '''
    result = db.query(q, data_binding={"root_id": root_id})
    #print(result)
    assert len(result) == 1

    # Again, traverse a loop in the graph, from the patient data node, back to itself,
    # but this time going thru the `doctor` data and schema nodes
    q = '''
        MATCH (p:patient {name: "Stephanie", age: 23, balance: 150.25})-[:IS_ATTENDED_BY]->
            (d:doctor {name:"Dr. Kane", specialty: "OB/GYN"})-[:SCHEMA]->(cl_d:CLASS {name:"doctor"})
            <-[:IS_ATTENDED_BY]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)
        WHERE id(p) = $root_id
        RETURN p, d, cl_d, cl_p
        '''
    result = db.query(q, data_binding={"root_id": root_id})
    #print(result)
    assert len(result) == 1


    # Count the links from the "patient" data node (the root)
    assert db.count_links(match=root_id, rel_name="HAS_RESULT", rel_dir="OUT", neighbor_labels="result") == 1
    assert db.count_links(match=root_id, rel_name="IS_ATTENDED_BY", rel_dir="OUT", neighbor_labels="doctor") == 1
    assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1

    # Locate the "result" data node, and count the links in/out of it
    match = db.match(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "doctor" data node, and count the links in/out of it
    match = db.match(labels="doctor")
    assert db.count_links(match=match, rel_name="IS_ATTENDED_BY", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "Import Data" data node, and count the links in/out of it
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1



def test_create_data_nodes_from_python_data_7(db):
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "categories"

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

    data = [
                {   "quote": "I wasn't kissing her. I was whispering in her mouth",
                    "attribution": "Chico Marx"
                }
           ]

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    # Traverse a loop in the graph, from the `quotes` data node, back to itself,
    # going thru the data and schema nodes
    q = '''
        MATCH (q :quotes {attribution: "Chico Marx", quote: "I wasn't kissing her. I was whispering in her mouth"})
              -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
              <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
              -[:imported_data]->(q)
        WHERE i.date = date() AND id(q) = $quote_id
        RETURN q, cl_q, cl_i
        '''
    result = db.query(q, data_binding={"quote_id": root_id})
    #print(result)
    assert len(result) == 1

    # Locate the "Import Data" data node, and count the links in/out of it
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "quotes" data node (the root), and count the links in/out of it
    assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_8(db):
    # Similar to test_create_data_nodes_from_python_data_8, but importing 2 quotes instead of 1,
    # and introducing non-Schema data
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "categories"

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

    data = [
                {   "quote": "I wasn't kissing her. I was whispering in her mouth",
                    "attribution": "Chico Marx"
                },
                {   "quote": "Inspiration exists, but it has to find us working",
                    "attribution": "Pablo Picasso",
                    "extraneous": "I don't belong in the Schema"
                },
                {   "junk": "This whole record has no place in the Schema"
                }
    ]

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    for root_id in node_id_list:
        # Traverse a loop in the graph, from the `quotes` data node, back to itself,
        # going thru the data and schema nodes
        q = '''
            MATCH (q :quotes)
                  -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
                  <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                  -[:imported_data]->(q)
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        assert len(result) == 1

        # Locate the "quotes" data node, and count the links in/out of it
        assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
        assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_9(db):
    # Similar to test_create_data_nodes_from_python_data_8, but also using the class "categories"
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "categories"

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    NeoSchema.create_class_with_properties(name="Import Data",
                                           properties=["source", "date"])
    NeoSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

    data = [
            {   "quote": "I wasn't kissing her. I was whispering in her mouth",
                "attribution": "Chico Marx",
                "in_category": {    "name": "Literature",
                                    "remarks": "English only",
                                    "junk": "trying to sneak in"
                                }
            },
            {   "quote": "Inspiration exists, but it has to find us working",
                "attribution": "Pablo Picasso",
                "in_category": {    "name": "Famous Quotes"
                               }
            }
    ]

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    for root_id in node_id_list:
        # Locate the "quotes" data node, and count the links in/out of it
        assert db.count_links(match=root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
        assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
        assert db.count_links(match=root_id, rel_name="in_category", rel_dir="OUT", neighbor_labels="categories") == 1

        # Traverse a loop in the graph, from the `quotes` data node, back to itself,
        # going thru the data and schema nodes
        q = '''
            MATCH (q :quotes)
                -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
                <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                -[:imported_data]->(q)
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        #print(result)
        assert len(result) == 1

        # Traverse a longer loop in the graph, again from the `quotes` data node to itself,
        # but this time also passing thru the category data and schema nodes
        q = '''
            MATCH (q :quotes)-[:in_category]->(cat :categories)
                -[:SCHEMA]->(cl_c :CLASS {name:"categories"})<-[:in_category]-
                (cl_q :CLASS {name:"quotes"})
                <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                -[:imported_data]->(q)
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q, cat, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        #print(result)
        assert len(result) == 1
        record = result[0]
        author = record["q"]["attribution"]
        assert author == 'Chico Marx' or author == 'Pablo Picasso'
        if author == 'Chico Marx':
            assert record["cat"]["name"] == "Literature"
            assert record["q"]["quote"] == "I wasn't kissing her. I was whispering in her mouth"
        else:
            assert record["cat"]["name"] == "Famous Quotes"
            assert record["q"]["quote"] == "Inspiration exists, but it has to find us working"
    # END of for loop


    # Add an extra quote, connected to 2 categories
    data = {    "quote": "My destination is no longer a place, rather a new way of seeing",
                "attribution": "Proust",
                "in_category": [
                                    {
                                        "name": "French Literature"
                                    }
                                    ,
                                    {
                                        "name": "Philosophy"
                                    }
                                ],
                "verified": False
           }

    # Import
    new_node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("new_node_id_list: ", new_node_id_list)
    assert len(new_node_id_list) == 1
    new_root_id = new_node_id_list[0]

    # Locate the latest "quotes" data node, and count the links in/out of it
    assert db.count_links(match=new_root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=new_root_id, rel_name="in_category", rel_dir="OUT", neighbor_labels="categories") == 2
    assert db.count_links(match=new_root_id, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Traverse a loop in the graph, from the `quotes` data node back to itself,
    # going thru the 2 category data nodes and their shared Schema node
    q = '''
            MATCH (q :quotes)-[:in_category]->(cat1 :categories {name: "French Literature"})
            -[:SCHEMA]->(cl_c :CLASS {name:"categories"})
            <-[:SCHEMA]-(cat2 :categories {name: "Philosophy"})
            <-[:in_category]-(q)
            WHERE id(q) = $quote_id
            RETURN q, cat1, cl_c, cat2
            '''
    result = db.query(q, data_binding={"quote_id": new_root_id})
    assert len(result) == 1
    record = result[0]
    assert record["q"]["attribution"] == "Proust"
    assert record["q"]["quote"] == "My destination is no longer a place, rather a new way of seeing"
    assert record["q"]["verified"] == False

    # Locate the data node for the Class "Import Data", and count the links in/out of it
    match = db.match(labels="CLASS", key_name="name", key_value="Import Data")
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="IN", neighbor_labels="Import Data") == 2
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Verify the data types  (Note: APOC must be installed, and enabled in the Neo4j config file)
    q = '''
        MATCH (n)
        WHERE id(n) = $quote_id
        RETURN apoc.meta.cypher.types(n) AS data_types  
    '''
    data_types = db.query(q, data_binding={"quote_id": new_root_id}, single_cell="data_types")
    #print(data_types)
    assert data_types == {'verified': 'BOOLEAN', 'attribution': 'STRING', 'quote': 'STRING'}    # 'uri': 'INTEGER' (not in current use)



def test_import_triplestore(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties(name="Course", strict=True,
                                           properties=["uri", "Course Title", "School", "Semester"])

    df = pd.DataFrame({"subject": [57, 57, 57],
                       "predicate": [1, 2, 3],
                       "object": ["Advanced Graph Databases", "New York University", "Fall 2024"]})

    result = NeoSchema.import_triplestore(df=df, class_node="Course",
                                          col_names = {1: "Course Title", 2: "School", 3: "Semester"},
                                          uri_prefix = "r-")
    assert len(result) == 1

    internal_id = result[0]
    lookup = db.get_nodes(internal_id)
    assert lookup == [{'School': 'New York University', 'Semester': 'Fall 2024', 'Course Title': 'Advanced Graph Databases', 'uri': 'r-57'}]


    # A second 1-entity import
    df = pd.DataFrame({"subject": ["MCB 273", "MCB 273", "MCB 273"],
                       "predicate": ["Course Title", "School", "Semester"],
                       "object": ["Systems Biology", "UC Berkeley", "Spring 2023"]})

    result = NeoSchema.import_triplestore(df=df, class_node="Course")
    assert len(result) == 1

    internal_id = result[0]
    lookup = db.get_nodes(internal_id)
    assert lookup == [{'School': 'UC Berkeley', 'Semester': 'Spring 2023', 'Course Title': 'Systems Biology', 'uri': 'MCB 273'}]



def test_scrub_dict():
    d = {"a": 1,
         "b": 3.5, "c": float("nan"),
         "d": "some value", "e": "   needs  cleaning!    ",
         "f": "", "g": "            ",
         "h": (1, 2)}

    result = NeoSchema.scrub_dict(d)
    assert result == {"a": 1,
                      "b": 3.5,
                      "d": "some value", "e": "needs  cleaning!",
                      "h": (1, 2)}
