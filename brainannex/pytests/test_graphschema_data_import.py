# Testing of Schema-based Data Import
# *** CAUTION! ***  The database gets cleared out during some of the tests!
# NOTES: - some tests require APOC
#        - some tests may fail their date check if done close to midnight, server time


import pytest
import pandas as pd
import numpy as np
from brainannex import GraphAccess, GraphSchema, SchemaCache
from test_graph_schema import create_sample_schema_1, create_sample_schema_2
from utilities.comparisons import *


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    GraphSchema.set_database(neo_obj)
    GraphSchema.debug = False
    yield neo_obj



# ************  CREATE A SAMPLE City-State database for the testing  **************
def create_sample_city_state_dbase(db):
    # Clear the database, create a schemas about City and State classes, with an "IS_IN" relationship,
    # and populate it with 4 cities and 3 states

    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties - based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["city_id", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["state_id", "name", "2-letter abbr"])

    # Add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some node data
    city_df = pd.DataFrame({"city_id": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"state_id": [1, 2, 3],  "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # Import the data nodes
    result = GraphSchema.import_pandas_nodes(df=city_df, class_name="City", report=False)
    assert result["number_nodes_created"] == 4

    result = GraphSchema.import_pandas_nodes(df=state_df, class_name="State", report=False)
    assert result["number_nodes_created"] == 3



def test_import_pandas_nodes_1(db):
    db.empty_dbase()

    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    with pytest.raises(Exception):
        GraphSchema.import_pandas_nodes(df=df, class_name="State")    # Undefined Class

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="State",
                                             properties=["name"], strict=True)


    # Import all state with a particular batch size
    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=1)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    n_deleted = GraphSchema.delete_data_nodes(class_name="State")
    assert n_deleted == 3

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=2)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    GraphSchema.delete_data_nodes(class_name="State")
    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=3)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)


    # Delete all state Data Nodes, and re-do import with a different batch size
    GraphSchema.delete_data_nodes(class_name="State")
    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=100)
    assert import_result["number_nodes_created"] == 3
    import_state_list = import_result["affected_nodes_ids"]

    # Verify that 3 Data Node were imported
    assert len(import_state_list) == 3
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 3
    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")
    assert compare_unordered_lists(result, import_state_list)



def test_import_pandas_nodes_2(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="State",
                                             properties=["name"], strict=True)


    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    # Import all states with a large batch size, as done in test_import_pandas_nodes_1()
    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="State", max_batch_size=100)
    assert import_result["number_nodes_created"] == 3


    # Prepare, and import, a second dataset
    df_2 = pd.DataFrame({"name": ["FL", "CA", "TX", "FL"]})    # Notice that "CA" is a duplicate from the earlier dataframe
                                                                # and that "FL" occurs twice

    # Import this second dataset with a medium batch size - and treat "name" as a unique primary key
    import_result = GraphSchema.import_pandas_nodes(df=df_2, class_name="State", primary_key="name",
                                                    max_batch_size=2)
    assert import_result["number_nodes_created"] == 2       # 2 of the 4 imports already existed



def test_import_pandas_nodes_3(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["vehicle ID", "make", "year"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    max_batch_size=2)
    assert import_result["number_nodes_created"] == 3
    assert len(import_result["affected_nodes_ids"]) == 3


    # Add more imports.  Note that "c2" is already present (if "vehicle ID" is a primary key),
    # and that "color" is not the Schema
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                              "color": ["red",       "white", "blue"]})

    with pytest.raises(Exception):      # "color" in not in the Schema
        GraphSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                        primary_key="vehicle ID")

    # Expand the Schema, to also include "color"
    GraphSchema.add_properties_to_class(class_node="Motor Vehicle", property_list=["color"])

    import_result_2 = GraphSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                      max_batch_size=2,
                                                      primary_key="vehicle ID", duplicate_option="merge")   # Duplicate records will be merged
    assert import_result_2["number_nodes_created"] == 2         # One of the 3 imports doesn't lead to node creation
    assert len(import_result_2["affected_nodes_ids"]) == 3      # 3 nodes were either created or updated

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'         # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013, '_CLASS': 'Motor Vehicle'} # The duplicate record 'c2' was updated by the new one
                                                                                                # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                                # and the 'year' value was left untouched
    assert result[0]["internal_id"] in import_result_2["affected_nodes_ids"]
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    # Re-import the first 3 records
    import_result_1 = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle", max_batch_size=2)
    assert import_result_1["number_nodes_created"] == 3
    assert len(import_result_1["affected_nodes_ids"]) == 3

    # Re-import the next 3 records (one of which has a duplicate)
    import_result_2 = GraphSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                      max_batch_size=2,
                                                      primary_key="vehicle ID", duplicate_option="replace")   # Duplicate records will be REPLACED (not "merged") this time
    assert import_result_2["number_nodes_created"] == 2         # One of the 3 imports doesn't lead to node creation
    assert len(import_result_2["affected_nodes_ids"]) == 3      # 3 nodes were either created or updated

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'     # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1

    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', '_CLASS': 'Motor Vehicle'}  # The duplicate record 'c2' was completely replaced by the new one
                                                                                    # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                    # and (unlike before) the 'year' value is gone
    assert result[0]["internal_id"] in import_result_2["affected_nodes_ids"]
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported



def test_import_pandas_nodes_4(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_result_1 = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                      max_batch_size=2,
                                                      rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert import_result_1['number_nodes_created'] == 3
    import_car_list_1 = import_result_1['affected_nodes_ids']
    assert len(import_car_list_1) == 3

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2013, 'manufacturer': 'Toyota', 'internal_id': import_car_list_1[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], '_node_labels': ['Motor Vehicle']}
               ]
    assert compare_recordsets(result, expected)


    # Note that "c2" is already present (if "vehicle ID" is a primary key)
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                               "year": [2005,        2015,    2025],
                              "color": ["red",       "white", "blue"]
                        })

    import_result_2 = GraphSchema.import_pandas_nodes(df=df_2, class_name="Motor Vehicle",
                                                      primary_key="vehicle ID", duplicate_option="merge",
                                                      rename={"vehicle ID": "VID", "make": "manufacturer"},
                                                      max_batch_size=2)
    assert import_result_2['number_nodes_created'] == 2     # Only 2 of the 3 records imported led to the creation of a new node
    import_car_list_2 = import_result_2['affected_nodes_ids']
    assert len(import_car_list_2) == 3                      # 3 nodes were either created or updated
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'manufacturer': 'BMW',    'internal_id': import_car_list_1[1], '_node_labels': ['Motor Vehicle'], 'color': 'white'},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], '_node_labels': ['Motor Vehicle']},

                {'VID': 'c4', 'color': 'red', 'year': 2005, 'manufacturer': 'Chevrolet', 'internal_id': import_car_list_2[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue', 'year': 2025, 'manufacturer': 'Fiat',     'internal_id': import_car_list_2[2], '_node_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)

    assert import_car_list_1[1] == import_car_list_2[1]     # The "c2" record import (first created, then updated)



def test_import_pandas_nodes_5(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["VID", "make", "year", "color"], strict=True)

    # Notice that "c2" is a duplicate
    df = pd.DataFrame({  "VID":   ["c1",    "c2",     "c3",     "c4",        "c2",     "c5"],
                         "make":  ["Honda", "Toyota", "Ford",   "Chevrolet", "BMW",    "Fiat"],
                         "year":  [2003,    2013,     2023,     2005,        2015,     2025],
                         "color": ["red",  "white",   "black",  "pink",      "yellow", "blue"]})

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    primary_key="VID", duplicate_option="merge",
                                                    max_batch_size=3, drop="year")
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'color': 'red',    'make': 'Honda',     'internal_id': import_car_list[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'color': 'yellow', 'make': 'BMW',       'internal_id': import_car_list[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'color': 'black',  'make': 'Ford',      'internal_id': import_car_list[2], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'color': 'pink',   'make': 'Chevrolet', 'internal_id': import_car_list[3], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue',   'make': 'Fiat',      'internal_id': import_car_list[5], '_node_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    primary_key="VID", duplicate_option="merge",
                                                    max_batch_size=2, select=["VID", "make", "color"])
    # Notice that the 3 fields we're selected have the identical effect as the dropping of "year" we did before;
    # also, changing the max_chunk_size.  All the results will be identical to before

    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'color': 'red',    'make': 'Honda',     'internal_id': import_car_list[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'color': 'yellow', 'make': 'BMW',       'internal_id': import_car_list[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'color': 'black',  'make': 'Ford',      'internal_id': import_car_list[2], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'color': 'pink',   'make': 'Chevrolet', 'internal_id': import_car_list[3], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue',   'make': 'Fiat',      'internal_id': import_car_list[5], '_node_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)



def test_import_pandas_nodes_6(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["VID", "make", "year", "color"], strict=True)

    # Notice that "c2" is a duplicate
    df = pd.DataFrame({  "VID":   ["c1",    "c2",     "c3",     "c4",        "c2",     "c5"],
                         "make":  ["Honda", "Toyota", "Ford",   "Chevrolet", "BMW",    "Fiat"],
                         "year":  [2003,    2013,     2023,     2005,        2015,     2025],
                         "color": ["red",  "white",   "black",  "pink",      "yellow", "blue"]})

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    primary_key="VID", duplicate_option="merge",
                                                    max_batch_size=4, drop=["make", "color"])

    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'internal_id': import_car_list[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'internal_id': import_car_list[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'internal_id': import_car_list[2], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'year': 2005, 'internal_id': import_car_list[3], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'year': 2025, 'internal_id': import_car_list[5], '_node_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    primary_key="VID", duplicate_option="merge",
                                                    max_batch_size=10, select="VID")

    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    assert import_result['number_nodes_created'] == 5
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 5                   # 5 unique values (the internal ID for node "c2" repeats twice)

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'internal_id': import_car_list[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'internal_id': import_car_list[2], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'internal_id': import_car_list[3], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'internal_id': import_car_list[5], '_node_labels': ['Motor Vehicle']}
               ]

    assert compare_recordsets(result, expected)


    # Another fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    import_result = GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                                    max_batch_size=10, select="VID")
    # This time, NOT specifying a primary_key

    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 6      # Verify that ALL Data Nodes were imported this time
    assert import_result['number_nodes_created'] == 6
    import_car_list = import_result['affected_nodes_ids']
    assert len(import_car_list) == 6                        # 6 nodes were either created or updated
    assert len(set(import_car_list)) == 6                   # 6 unique values (the internal ID for node "c2" repeats twice)

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'internal_id': import_car_list[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'internal_id': import_car_list[2], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c4', 'internal_id': import_car_list[3], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'internal_id': import_car_list[4], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'internal_id': import_car_list[5], '_node_labels': ['Motor Vehicle']}
               ]

    assert compare_recordsets(result, expected)



def test_import_pandas_nodes_7(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"VID": ["c1",    "c2",     "c3"],
                      "make": ["Honda", "Toyota", "Ford"],
                      "year": [2003,    2013,     2023]})

    with pytest.raises(Exception):
        GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                        primary_key="non_existent")     # Primary key not in the dataframe

    with pytest.raises(Exception):
        GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                        primary_key="VID", drop="VID")     # Primary key is a dropped column

    with pytest.raises(Exception):
        GraphSchema.import_pandas_nodes(df=df, class_name="Motor Vehicle",
                                        primary_key="VID", drop=["VID", "year"])     # Primary key is a dropped column





def test_import_pandas_nodes_1_OLD(db):
    db.empty_dbase()

    df = pd.DataFrame({"name": ["CA", "NY", "OR"]})

    with pytest.raises(Exception):
        GraphSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="State")    # Undefined Class

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="State",
                                             properties=["name"], strict=True)

    import_state_list_1 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="State")

    # Verify that 3 Data Node were imported
    assert len(import_state_list_1) == 3
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 3

    # Make sure our 3 states are present in the import
    q = '''
        UNWIND ["CA", "NY", "OR"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")

    assert compare_unordered_lists(result, import_state_list_1)


    # Duplicate entry: "CA" (from new dataset to be added to the previous one)
    df_2 = pd.DataFrame({"name": ["NV", "CA", "WA"]})

    import_state_list_2 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="State",
                                                                   primary_key="name")

    # Verify that a grand total of only 5 Data Node were imported (i.e.,
    # the duplicate didn't lead to an extra record)
    assert len(import_state_list_2) == 2
    assert GraphSchema.count_data_nodes_of_class(class_name="State") == 5

    q = '''
        UNWIND ["CA", "NY", "OR", "NV", "WA"] AS state_name
        MATCH (s :State {name:state_name, `_CLASS`: "State"})
        RETURN id(s) AS internal_id
        '''
    result = db.query(q, single_column="internal_id")

    assert set(result) == set(import_state_list_1).union(set(import_state_list_2))


    # Expand the Schema with a new Class
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["vehicle ID", "make", "year"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_car_list_1 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle")


    assert len(import_car_list_1) == 3

    # Note that "c2" is already present (if "vehicle ID" is a primary key),
    # and that "color" is not the Schema
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                              "color": ["red",       "white", "blue"]})

    with pytest.raises(Exception):      # "color" in not in the Schema
        GraphSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                 primary_key="vehicle ID")

    GraphSchema.add_properties_to_class(class_node="Motor Vehicle", property_list=["color"])

    import_car_list_2 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                                 primary_key="vehicle ID", duplicate_option="merge")   # Duplicate records will be merged
    assert len(import_car_list_2) == 2

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'         # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', 'year':2013, '_CLASS': 'Motor Vehicle'} # The duplicate record 'c2' was updated by the new one
                                                                                                # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                                # and the 'year' value was left untouched
    assert result[0]["internal_id"] in import_car_list_1
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported


    # A fresh start with "Motor Vehicle" data nodes
    db.delete_nodes_by_label(delete_labels="Motor Vehicle")

    # Re-import the first 3 records
    import_car_list_1 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle")
    assert len(import_car_list_1) == 3

    # Re-import the next 3 records (one of which has a duplicate)
    import_car_list_2 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                                 primary_key="vehicle ID", duplicate_option="replace")   # Duplicate records will be REPLACED (not "merged") this time
    assert len(import_car_list_2) == 2

    q = 'MATCH (m:`Motor Vehicle` {`vehicle ID`: "c2"}) RETURN m, id(m) as internal_id'     # Retrieve the record that was in both dataframes
    result = db.query(q)
    assert len(result) == 1

    assert result[0]["m"] == {'vehicle ID': 'c2', 'make': 'BMW', 'color': 'white', '_CLASS': 'Motor Vehicle'}  # The duplicate record 'c2' was completely replaced by the new one
                                                                                    # Notice how the Toyota became a BMW, the 'color' was added,
                                                                                    # and (unlike before) the 'year' value is gone
    assert result[0]["internal_id"] in import_car_list_1
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported



def test_import_pandas_nodes_2_OLD(db):
    db.empty_dbase()

    # Populate the Schema
    GraphSchema.create_class_with_properties(name="Motor Vehicle",
                                             properties=["VID", "manufacturer", "year", "color"], strict=True)

    df = pd.DataFrame({"vehicle ID": ["c1",    "c2",     "c3"],
                             "make": ["Honda", "Toyota", "Ford"],
                             "year": [2003,    2013,     2023]})

    import_car_list_1 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df, class_name="Motor Vehicle",
                                                                 rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert len(import_car_list_1) == 3

    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2013, 'manufacturer': 'Toyota', 'internal_id': import_car_list_1[1], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], '_node_labels': ['Motor Vehicle']}
               ]
    assert compare_recordsets(result, expected)


    # Note that "c2" is already present (if "vehicle ID" is a primary key)
    df_2 = pd.DataFrame({"vehicle ID": ["c4",        "c2",    "c5"],
                               "make": ["Chevrolet", "BMW",   "Fiat"],
                               "year": [2005,        2015,    2025],
                              "color": ["red",       "white", "blue"]
                        })

    import_car_list_2 = GraphSchema.import_pandas_nodes_NO_BATCH(df=df_2, class_name="Motor Vehicle",
                                                                 primary_key="vehicle ID", duplicate_option="merge",
                                                                 rename={"vehicle ID": "VID", "make": "manufacturer"})
    assert len(import_car_list_2) == 2
    assert GraphSchema.count_data_nodes_of_class(class_name="Motor Vehicle") == 5      # Verify that a grand total of only 5 Data Node were imported
    result = GraphSchema.get_all_data_nodes_of_class("Motor Vehicle")
    expected = [
                {'VID': 'c1', 'year': 2003, 'manufacturer': 'Honda',  'internal_id': import_car_list_1[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c2', 'year': 2015, 'manufacturer': 'BMW',    'internal_id': import_car_list_1[1], '_node_labels': ['Motor Vehicle'], 'color': 'white'},
                {'VID': 'c3', 'year': 2023, 'manufacturer': 'Ford',   'internal_id': import_car_list_1[2], '_node_labels': ['Motor Vehicle']},

                {'VID': 'c4', 'color': 'red', 'year': 2005, 'manufacturer': 'Chevrolet', 'internal_id': import_car_list_2[0], '_node_labels': ['Motor Vehicle']},
                {'VID': 'c5', 'color': 'blue', 'year': 2025, 'manufacturer': 'Fiat',     'internal_id': import_car_list_2[1], '_node_labels': ['Motor Vehicle']}
               ]    # Notice how the 'c2' record got updated

    assert compare_recordsets(result, expected)

    # TODO: test "drop", "select"

    q = f'''
        MATCH (n :`Motor Vehicle`) WHERE id(n) IN {import_car_list_2}
        RETURN n
        '''

    # TODO: more tests; see also the tests for NeoAccess.load_pandas()



def test_import_pandas_links_NO_BATCH(db):
    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Now add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3], "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate table ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"State ID": [1, 1, 2, 3], "City ID": [1, 3, 2, 4]})

    # Import the data nodes
    city_node_ids = GraphSchema.import_pandas_nodes_NO_BATCH(df=city_df, class_name="City")
    assert len(city_node_ids) == 4

    state_node_ids = GraphSchema.import_pandas_nodes_NO_BATCH(df=state_df, class_name="State")
    assert len(state_node_ids) == 3

    # Now import the links
    link_ids = GraphSchema.import_pandas_links_NO_BATCH(df=state_city_links_df,
                                                        class_from="City", class_to="State",
                                                        col_from="City ID", col_to="State ID",
                                                        link_name="IS_IN")
    assert len(link_ids) == 4

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)



def test_import_pandas_links_OLD_1(db):
    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3], "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate table ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"State ID": [1, 1, 2, 3], "City ID": [1, 3, 2, 4]})

    # Import the data nodes
    result = GraphSchema.import_pandas_nodes(df=city_df, class_name="City")
    assert result["number_nodes_created"] == 4

    result = GraphSchema.import_pandas_nodes(df=state_df, class_name="State")
    assert result["number_nodes_created"] == 3

    # Now import the links
    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="City ID", col_to="State ID",
                                                   link_name="IS_IN",
                                                   max_batch_size=4)      # This will lead to 1 batch
    assert len(link_ids) == 4

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)


    # Repeat the entire link creation with a different batch size
    q = "MATCH (:City)-[r :IS_IN]-(:State) DETACH DELETE r"     # Det rid of existing links
    result = db.update_query(q)
    assert result["relationships_deleted"] == 4

    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="City ID", col_to="State ID",
                                                   link_name="IS_IN",
                                                   max_batch_size=3)      # This will lead to 2 batches
    assert len(link_ids) == 4

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id" # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)


    # Repeat the entire link creation with a different batch size
    q = "MATCH (:City)-[r :IS_IN]-(:State) DETACH DELETE r"     # Det rid of existing links
    result = db.update_query(q)
    assert result["relationships_deleted"] == 4

    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="City ID", col_to="State ID",
                                                   link_name="IS_IN",
                                                   max_batch_size=1)      # This will lead to 4 batches
    assert len(link_ids) == 4

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id" # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)



def test_import_pandas_links_OLD_2(db):
    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some node data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3], "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate table ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"State ID": [1, 1, 2, 3], "City ID": [1, 3, 2, 4], "Rank": [10, None, 12, 13]})
    # The None value in the "Rank" will appear as a NaN in the data frame

    # Import the data nodes
    result = GraphSchema.import_pandas_nodes(df=city_df, class_name="City")
    assert result["number_nodes_created"] == 4

    result = GraphSchema.import_pandas_nodes(df=state_df, class_name="State")
    assert result["number_nodes_created"] == 3

    # Now import the links
    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="City ID", col_to="State ID",
                                                   link_name="IS_IN", col_link_props="Rank",
                                                   max_batch_size=4)      # This will lead to 1 batch
    assert len(link_ids) == 4

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 10
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 12
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 13
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert "Rank" not in result[0]      # No value got set, because it was a missing value (NaN) in the imported dataframe
    assert result[0]["internal_id"] in link_ids



def test_import_pandas_links_OLD_3(db):
    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some node data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3],  "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate table ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"state_id": [1, 1, 2, 3], "city_id": [1, 3, 2, 4]})
    # The None value in the "Rank" will appear as a NaN in the data frame

    # Import the data nodes
    result = GraphSchema.import_pandas_nodes(df=city_df, class_name="City")
    assert result["number_nodes_created"] == 4

    result = GraphSchema.import_pandas_nodes(df=state_df, class_name="State")
    assert result["number_nodes_created"] == 3

    # Now import the links
    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="city_id", col_to="state_id",
                                                   rename={"city_id": "City ID", "state_id": "State ID"},
                                                   link_name="IS_IN",
                                                   max_batch_size=4)      # This will lead to 1 batch
    assert len(link_ids) == 4

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")

    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)



def test_import_pandas_links_1(db):
    create_sample_city_state_dbase(db)      # 4 cities and 3 states

    # A separate dataframe ("join table") with the data about the relationships;
    city_state_df = pd.DataFrame({"city_id": [1,         3,       2,       4],
                                 "state_id": [1,         1,       2,       3],
                                 "rank":     [53,        4,       1,       1],
                                 "region":   ["north", "north", "north", "south"]
                                 })
    '''
                                           city_id  state_id  rank region
                                    0            1         1    53  north
                                    1            3         1     4  north
                                    2            2         2     1  north
                                    3            4         3     1  south
    '''

    # Import in batches of 1
    link_ids = GraphSchema.import_pandas_links(df=city_state_df,
                                               class_from="City", class_to="State",
                                               col_from="city_id", col_to="state_id",
                                               link_name="IS_IN",
                                               cols_link_props=["rank", "region"],
                                               report=False, max_batch_size=1)

    assert len(link_ids) == 4       # Verify the number of the links reported to have been imported
    # Verify the values of the imported links' internal dbase ID's
    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 53, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 4, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1, "region": "south"}]



def test_import_pandas_links_2(db):
    # Same as version 1, but with a different import batch size
    create_sample_city_state_dbase(db)  # 4 cities and 3 states

    # A separate dataframe ("join table") with the data about the relationships;
    city_state_df = pd.DataFrame({"city_id": [1,         3,       2,       4],
                                 "state_id": [1,         1,       2,       3],
                                 "rank":     [53,        4,       1,       1],
                                 "region":   ["north", "north", "north", "south"]
                                 })
    '''
                                           city_id  state_id  rank region
                                    0            1         1    53  north
                                    1            3         1     4  north
                                    2            2         2     1  north
                                    3            4         3     1  south
    '''

    # Import in batches of 2
    link_ids = GraphSchema.import_pandas_links(df=city_state_df,
                                               class_from="City", class_to="State",
                                               col_from="city_id", col_to="state_id",
                                               link_name="IS_IN",
                                               cols_link_props=["rank", "region"],
                                               report=False, max_batch_size=2)

    assert len(link_ids) == 4       # Verify the number of the links reported to have been imported
    # Verify the values of the imported links' internal dbase ID's
    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 53, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 4, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1, "region": "south"}]



def test_import_pandas_links_3(db):
    # Similar to versions 1 and 2, but with a different import batch size: all data at once,
    # and some values are None, or empty strings or Numpy NaN (all to be dropped)
    create_sample_city_state_dbase(db)  # 4 cities and 3 states

    # A separate dataframe ("join table") with the data about the relationships;
    city_state_df = pd.DataFrame({"city_id": [1,         3,       2,       4],
                                 "state_id": [1,         1,       2,       3],
                                 "rank":     [None,      4,       1,       1],
                                 "region":   ["north",  "", "north",    None]
                                 })
    '''
                                           city_id  state_id  rank region
                                    0            1         1    NaN  north
                                    1            3         1    4.0  
                                    2            2         2    1.0  north
                                    3            4         3    1.0  
                                    (Notice that the numbers in the 'rank' col are now floats because of the NaN)
    '''

    # Import in batches of 4, i.e. all the data at once
    link_ids = GraphSchema.import_pandas_links(df=city_state_df,
                                               class_from="City", class_to="State",
                                               col_from="city_id", col_to="state_id",
                                               link_name="IS_IN",
                                               cols_link_props=["rank", "region"],
                                               report=False, max_batch_size=4)

    assert len(link_ids) == 4       # Verify the number of the links reported to have been imported
    # Verify the values of the imported links' internal dbase ID's
    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 4.0}]

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1.0, "region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"rank": 1.0}]



def test_import_pandas_links_4(db):
    # Very similar to versions 2, but importing only 1 property on the new links, rather than 2
    create_sample_city_state_dbase(db)  # 4 cities and 3 states

    # A separate dataframe ("join table") with the data about the relationships;
    city_state_df = pd.DataFrame({"city_id": [1,         3,       2,       4],
                                 "state_id": [1,         1,       2,       3],
                                 "rank":     [53,        4,       1,       1],
                                 "region":   ["north", "north", "north", "south"]
                                 })
    '''
                                           city_id  state_id  rank region
                                    0            1         1    53  north
                                    1            3         1     4  north
                                    2            2         2     1  north
                                    3            4         3     1  south
    '''

    # Import in batches of 2  (Note: the "rank" column is NOT imported)
    link_ids = GraphSchema.import_pandas_links(df=city_state_df,
                                               class_from="City", class_to="State",
                                               col_from="city_id", col_to="state_id",
                                               link_name="IS_IN",
                                               cols_link_props="region",
                                               report=False, max_batch_size=2)

    assert len(link_ids) == 4       # Verify the number of the links reported to have been imported
    # Verify the values of the imported links' internal dbase ID's
    q = "MATCH (:City)-[r :IS_IN]-(:State) RETURN id(r) AS rel_id"  # Get the dbase IDs of all the "IS_IN" links created
    result = db.query(q, single_column="rel_id")
    assert compare_unordered_lists(result, link_ids)

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"region": "north"}]

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=False)
    assert result == [{"region": "south"}]



def test_import_pandas_links_5(db):
    db.empty_dbase()

    # Create a "City" Class node - together with its Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])

    # Likewise for a "State" Class node - together with its Properties, based on the data to import
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Now add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3], "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    state_city_links_df = pd.DataFrame({"State ID": [1, 1, 2, 3], "City ID": [1, 3, 2, 4]})
    print(state_city_links_df)

    GraphSchema.import_pandas_nodes(df=city_df, class_name="City", report=False)      # Import the 4 cities
    GraphSchema.import_pandas_nodes(df=state_df, class_name="State", report=False)    # Import the 3 states

    # Finally, link up the cities to the states, using links named "IS_IN"
    GraphSchema.import_pandas_links(df=state_city_links_df,
                                    class_from="City", class_to="State",
                                    col_from="City ID", col_to="State ID",
                                    link_name="IS_IN")

    assert GraphSchema.data_link_exists(node1_id="Berkeley", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="San Francisco", node2_id="California", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="Chicago", node2_id="Illinois", id_key="name", link_name="IS_IN")
    assert GraphSchema.data_link_exists(node1_id="New York City", node2_id="New York", id_key="name", link_name="IS_IN")



def test__convert_df_chunk():
    data = {
        "A": [1, 2, 3],
        "B": ["x", "y", "z"],
        "C": [10, 20, 30],
        "D": [100, 200, 300],
        "E": [1000, 2000, 3000]
    }
    df = pd.DataFrame(data)
    '''
       A  B   C    D     E
    0  1  x  10  100  1000
    1  2  y  20  200  2000
    2  3  z  30  300  3000
    '''
    result = GraphSchema._convert_df_chunk(df=df, row_start=0, row_end=2,
                                           col_from="A", col_to="B", cols_other=["C", "E"])
    assert result == [{'FROM': 1, 'TO': 'x', 'OTHER_FIELDS': {'C': 10, 'E': 1000}},
                      {'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {'C': 20, 'E': 2000}},
                      {'FROM': 3, 'TO': 'z', 'OTHER_FIELDS': {'C': 30, 'E': 3000}}]

    assert type(result[0]["FROM"]) == int
    assert type(result[0]["OTHER_FIELDS"]["C"]) == int

    result = GraphSchema._convert_df_chunk(df=df, row_start=0, row_end=1,
                                           col_from="A", col_to="B", cols_other=["C", "E"])
    assert result == [{'FROM': 1, 'TO': 'x', 'OTHER_FIELDS': {'C': 10, 'E': 1000}},
                      {'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {'C': 20, 'E': 2000}}]

    result = GraphSchema._convert_df_chunk(df=df, row_start=1, row_end=1,
                                           col_from="A", col_to="B", cols_other=["C", "E"])
    assert result == [{'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {'C': 20, 'E': 2000}}]

    with pytest.raises(Exception):  # Starting after the endrow
        GraphSchema._convert_df_chunk(df=df, row_start=2, row_end=1,
                                      col_from="A", col_to="B", cols_other=["C", "E"])
    with pytest.raises(Exception):  # Exessive row_end
        GraphSchema._convert_df_chunk(df=df, row_start=1, row_end=3,
                                      col_from="A", col_to="B", cols_other=["C", "E"])

    result = GraphSchema._convert_df_chunk(df=df, row_start=1, row_end=2,
                                           col_from="A", col_to="B", cols_other=["C", "E"])
    assert result == [{'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {'C': 20, 'E': 2000}},
                      {'FROM': 3, 'TO': 'z', 'OTHER_FIELDS': {'C': 30, 'E': 3000}}]

    result = GraphSchema._convert_df_chunk(df=df, row_start=0, row_end=2,
                                           col_from="A", col_to="B", cols_other=[])
    assert result == [{'FROM': 1, 'TO': 'x', 'OTHER_FIELDS': {}},
                      {'FROM': 2, 'TO': 'y', 'OTHER_FIELDS': {}},
                      {'FROM': 3, 'TO': 'z', 'OTHER_FIELDS': {}}]



    # With new data that contains some None values, empty strings and NaN's
    data = {
        "A": [1, 2, 3],
        "B": ["", "y", "z"],
        "C": [10, 20, 30],
        "D": [100, None, 300],
        "E": ["alpha", "beta", None]
    }
    df = pd.DataFrame(data)
    '''
       A  B    C      D      E
    0  1  ""  10  100.0  alpha
    1  2  y   20    NaN   beta
    2  3  z   30  300.0   None
    '''
    result = GraphSchema._convert_df_chunk(df=df, row_start=0, row_end=2,
                                           col_from="A", col_to="C", cols_other=["B", "D", "E"])

    assert result == [  {'FROM': 1, 'TO': 10, 'OTHER_FIELDS': {'D': 100.0, 'E': 'alpha'}},
                        {'FROM': 2, 'TO': 20, 'OTHER_FIELDS': {'B': 'y',   'E': 'beta'}},
                        {'FROM': 3, 'TO': 30, 'OTHER_FIELDS': {'B': 'z',   'D': 300.0}}
                     ]

    result = GraphSchema._convert_df_chunk(df=df, row_start=1, row_end=2,
                                           col_from="A", col_to="C", cols_other=["B", "D", "E"])

    assert result == [
                        {'FROM': 2, 'TO': 20, 'OTHER_FIELDS': {'B': 'y',   'E': 'beta'}},
                        {'FROM': 3, 'TO': 30, 'OTHER_FIELDS': {'B': 'z',   'D': 300.0}}
                     ]



def test__not_junk():
    assert GraphSchema._not_junk(5)
    assert GraphSchema._not_junk(3.14)
    assert GraphSchema._not_junk("hello")
    assert GraphSchema._not_junk([1, 2])

    assert not GraphSchema._not_junk(None)
    assert not GraphSchema._not_junk("")
    assert not GraphSchema._not_junk(np.nan)




def test_get_data_link_properties(db):
    db.empty_dbase()
    GraphSchema.set_database(db)

    # Create "City" and "State" Class node - together with their respective Properties - based on the data to import
    GraphSchema.create_class_with_properties(name="City", properties=["City ID", "name"])
    GraphSchema.create_class_with_properties(name="State", properties=["State ID", "name", "2-letter abbr"])

    # Add a relationship named "IS_IN", from the "City" Class to the "State" Class
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="IS_IN")

    # Now import some node data
    city_df = pd.DataFrame({"City ID": [1, 2, 3, 4], "name": ["Berkeley", "Chicago", "San Francisco", "New York City"]})
    state_df = pd.DataFrame({"State ID": [1, 2, 3],  "name": ["California", "Illinois", "New York"], "2-letter abbr": ["CA", "IL", "NY"]})

    # In this example, we assume a separate dataframe ("join table") with the data about the relationships;
    # this would always be the case for many-to-many relationships;
    # 1-to-many relationships, like we have here, could also be stored differently
    state_city_links_df = pd.DataFrame({"state_id": [1, 1, 2, 3], "city_id": [1, 3, 2, 4], "rank_value": [10, None, 12, 13]})
    # The None value in the "Rank" will appear as a NaN in the data frame

    # Import the data nodes
    result = GraphSchema.import_pandas_nodes(df=city_df, class_name="City")
    assert result["number_nodes_created"] == 4

    result = GraphSchema.import_pandas_nodes(df=state_df, class_name="State")
    assert result["number_nodes_created"] == 3

    # Now import the links
    link_ids = GraphSchema.import_pandas_links_OLD(df=state_city_links_df,
                                                   class_from="City", class_to="State",
                                                   col_from="city_id", col_to="state_id",
                                                   link_name="IS_IN", col_link_props="rank_value",
                                                   rename={"city_id": "City ID", "state_id": "State ID", "rank_value": "Rank"},
                                                   max_batch_size=2)      # This will lead to 2 batches
    assert len(link_ids) == 4

    result = GraphSchema.get_data_link_properties(node1_id="Berkeley", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 10
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="Chicago", node2_id="Illinois", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 12
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="New York City", node2_id="New York", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert result[0]["Rank"] == 13
    assert result[0]["internal_id"] in link_ids

    result = GraphSchema.get_data_link_properties(node1_id="San Francisco", node2_id="California", id_key="name",
                                                  link_name="IS_IN", include_internal_id=True)
    assert len(result) == 1
    assert "Rank" not in result[0]      # No value got set, because it was a missing value (NaN) in the imported dataframe
    assert result[0]["internal_id"] in link_ids



def test_create_tree_from_dict_1(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="address",
                                             properties=["state", "city"])

    # Import a data dictionary
    data = {"state": "California", "city": "Berkeley"}
    cache = SchemaCache()    # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of a new node, with 2 attributes, named "state" and "city"
    root_neo_id = GraphSchema.create_tree_from_dict(data, class_name="address", cache=cache)
    #print(root_neo_id)
    assert root_neo_id is not None

    q = '''
        MATCH (root :address {state: "California", city: "Berkeley", `_CLASS`: "address"})
        WHERE id(root) = $root_neo_id
        RETURN root
    '''

    root_node = db.query(q, data_binding={"root_neo_id": root_neo_id})
    assert root_node == [{'root': {'city': 'Berkeley', 'state': 'California', '_CLASS': 'address'}}]



def test_create_tree_from_dict_2(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="person",
                                             properties=["name"])
    GraphSchema.create_class_with_properties(name="address",
                                             properties=["state", "city"])

    GraphSchema.create_class_relationship(from_class="person", to_class="address", rel_name="address")

    # Import a data dictionary
    data = {"name": "Julian", "address": {"state": "California", "city": "Berkeley"}}
    cache = SchemaCache()    # All needed Schema-related data will be automatically queried and cached here

    # This import will result in the creation of 2 nodes, namely the tree root (with a single attribute "name"), with
    # an outbound link named "address" to another node (the subtree) that has the "state" and "city" attributes
    root_neo_id = GraphSchema.create_tree_from_dict(data, class_name="person", cache=cache)
    #print(root_neo_id)

    assert root_neo_id is not None


    q = '''
        MATCH (root :person {name: "Julian", `_CLASS`: "person"})-[:address]->
        (a :address {state: "California", city: "Berkeley", `_CLASS`: "address"})
        WHERE id(root) = $root_neo_id
        RETURN root
    '''

    root_node = db.query(q, data_binding={"root_neo_id": root_neo_id})
    assert root_node == [{'root': {'name': 'Julian', '_CLASS': 'person'}}]




####################################################################################################

def test_create_tree_from_list_1(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="address",
                                             properties=["state", "city"])

    # Import a data dictionary
    data = [{"state": "California", "city": "Berkeley"}, {"state": "Texas", "city": "Dallas"}]
    cache = SchemaCache()    # All needed Schema-related data will be automatically queried and cached here


    # This import will result in the creation of two new nodes, each with 2 attributes, named "state" and "city"
    root_neo_id_list = GraphSchema.create_trees_from_list(data, class_name="address", cache=cache)
    #print(root_neo_id_list)

    assert root_neo_id_list is not None

    q = '''
    MATCH 
        (root1 :address {state: "California", city: "Berkeley", `_CLASS`: "address"}),
        (root2 :address {state: "Texas", city: "Dallas", `_CLASS`: "address"})
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
    GraphSchema.create_class_with_properties(name="address",
                                             properties=["value"])

    # Import a data dictionary
    data = ["California", "Texas"]
    cache = SchemaCache()    # All needed Schema-related data will be automatically queried and cached here


    # This import will result in the creation of two new nodes, each with a property by default named "value"
    root_neo_id_list = GraphSchema.create_trees_from_list(data, class_name="address", cache=cache)
    #print("root_neo_id_list: ", root_neo_id_list)

    assert len(root_neo_id_list) == 2

    q = '''
        MATCH 
            (root1 :address {value: "California", `_CLASS`: "address"}),
            (root2 :address {value: "Texas", `_CLASS`: "address"})
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
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])

    GraphSchema.create_class_with_properties(name="my_class_1",
                                             properties=["legit", "other"])

    GraphSchema.create_class_relationship(from_class="Import Data", to_class="my_class_1", rel_name="imported_data")


    # 1-layer dictionary, with a key in the Schema and one not

    data = {"legit": 123, "unexpected": 456}
    # Import step
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="my_class_1")

    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH (n1:`Import Data` {`_CLASS`: "Import Data"})
            -[:imported_data]->
            (n2:my_class_1 {`_CLASS`: "my_class_1"})
        WHERE id(n2) = $uri
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"uri": root_id}, single_row=True)

    root_record = root_node["n2"]
    assert root_record["legit"] == 123
    #assert "uri" in root_record                # Not currently is use
    assert "unexpected" not in root_record      # Only the key in the Schema gets imported



def test_create_data_nodes_from_python_data_2(db):
    db.empty_dbase()

    # Set up the Schema.  Nothing in it yet, other than the "Import Data" node
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])


    data = {"arbitrary": "Doesn't matter"}

    # Import step
    with pytest.raises(Exception):
        GraphSchema.create_data_nodes_from_python_data(data, class_name="non_existent_class")

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
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_with_properties(name="patient",
                                             properties=["age", "balance"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH 
            (n1:`Import Data` {`_CLASS`: "Import Data"})
            -[:imported_data]->
            (n2:patient {`_CLASS`: "patient"})
        WHERE id(n2) = $uri
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"uri": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    root_record = root_node["n2"]
    assert root_record["age"] == 23
    assert root_record["balance"] == 150.25
    assert root_record["_CLASS"] == "patient"
    #assert "uri" in root_record            # Not currently is use
    assert len(root_record) == 3            # Only the keys in the Schema gets imported

    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    res = db.query(q)
    assert len(res) == 0         # "result" is not in the Schema



def test_create_data_nodes_from_python_data_4(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH 
            (n1:`Import Data` {`_CLASS`: "Import Data"})
            -[:imported_data]->
            (n2:patient {`_CLASS`: "patient"})
        WHERE id(n2) = $root_id
        RETURN n2
        '''
    root_node = db.query(q, data_binding={"root_id": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    root_record = root_node["n2"]

    assert root_record["name"] == "Stephanie"
    assert root_record["age"] == 23
    assert root_record["balance"] == 150.25
    assert root_record["_CLASS"] == "patient"
    #assert "uri" in root_record        # Not currently is use
    assert len(root_record) == 4            # Only the keys in the Schema gets imported

    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    res = db.query(q)
    assert len(res) == 0    # the relationship "result" is not in the Schema

    # Count the links from the "patient" data node (the root)
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=root_id, rel_name="result", rel_dir="BOTH") == 0



def test_create_data_nodes_from_python_data_5(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")


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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH 
            (i: `Import Data`)-[:imported_data]->
            (p:patient {name: "Stephanie", age: 23, balance: 150.25, `_CLASS`: "patient"})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0, `_CLASS`: "result"})
        WHERE i.date = date() AND id(p) = $root_id
        RETURN p, r, i
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
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=root_id, rel_name="WRONG_LINK_TO_DOCTOR", rel_dir="BOTH") == 0

    # Locate the "result" data node, and count the links in/out of it
    match = db.match(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1




def test_create_data_nodes_from_python_data_6(db):
    db.empty_dbase()

    create_sample_schema_1()     # Schema with patient/result/doctor

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="patient", rel_name="imported_data")

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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="patient")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]


    q = '''
        MATCH 
            (i: `Import Data`)-[:imported_data]->
            (p:patient {name: "Stephanie", age: 23, balance: 150.25, `_CLASS`: "patient"})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0, `_CLASS`: "result"})
        WHERE i.date = date() AND id(p) = $root_id
        RETURN p, r, i
        '''
    result = db.query(q, data_binding={"root_id": root_id})
    #print(result)
    assert len(result) == 1

    # Again, traverse the graph,
    # but this time going thru the `doctor` data node
    q = '''
        MATCH 
            (p:patient {name: "Stephanie", age: 23, balance: 150.25, `_CLASS`: "patient"})-[:IS_ATTENDED_BY]->
            (d:doctor {name:"Dr. Kane", specialty: "OB/GYN", `_CLASS`: "doctor"})
        WHERE id(p) = $root_id
        RETURN p, d
        '''
    result = db.query(q, data_binding={"root_id": root_id})
    #print(result)
    assert len(result) == 1


    # Count the links from the "patient" data node (the root)
    assert db.count_links(match=root_id, rel_name="HAS_RESULT", rel_dir="OUT", neighbor_labels="result") == 1
    assert db.count_links(match=root_id, rel_name="IS_ATTENDED_BY", rel_dir="OUT", neighbor_labels="doctor") == 1
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1

    # Locate the "result" data node, and count the links in/out of it
    match = db.match(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1

    # Locate the "doctor" data node, and count the links in/out of it
    match = db.match(labels="doctor")
    assert db.count_links(match=match, rel_name="IS_ATTENDED_BY", rel_dir="IN", neighbor_labels="patient") == 1

    # Locate the "Import Data" data node, and count the links in/out of it
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="patient") == 1



def test_create_data_nodes_from_python_data_7(db):
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "Category"

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

    data = [
                {   "quote": "I wasn't kissing her. I was whispering in her mouth",
                    "attribution": "Chico Marx"
                }
           ]

    # Import
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    # Traverse a loop in the graph, from the `quotes` data node, back to itself,
    # going thru the data and schema nodes
    q = '''
        MATCH 
            (i: `Import Data` {`_CLASS`: "Import Data"})-[:imported_data]->
            (q :quotes {attribution: "Chico Marx", quote: "I wasn't kissing her. I was whispering in her mouth", `_CLASS`: "quotes"})
        WHERE i.date = date() AND id(q) = $quote_id
        RETURN q
        '''
    result = db.query(q, data_binding={"quote_id": root_id})
    #print(result)
    assert len(result) == 1

    # Locate the "Import Data" data node, and count the links in/out of it
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 1

    # Locate the "quotes" data node (the root), and count the links in/out of it
    assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_8(db):
    # Similar to test_create_data_nodes_from_python_data_8, but importing 2 quotes instead of 1,
    # and introducing non-Schema data
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "Category"

    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2

    for root_id in node_id_list:
        # Traverse a loop in the graph, from the `quotes` data node, back to itself,
        # going thru the data and schema nodes
        q = '''
            MATCH (i: `Import Data` {`_CLASS`: "Import Data"})
                  -[:imported_data]->(q :quotes {`_CLASS`: "quotes"})
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        assert len(result) == 1

        # Locate the "quotes" data node, and count the links in/out of it
        assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_9(db):
    # Similar to test_create_data_nodes_from_python_data_8, but also using the class "Category"
    db.empty_dbase()

    create_sample_schema_2()     # Class "quotes", with a relationship "in_category" to class "Category"

    # Add to the Schema the "Import Data" Class node, and a link to the Class of the import's root
    GraphSchema.create_class_with_properties(name="Import Data",
                                             properties=["source", "date"])
    GraphSchema.create_class_relationship(from_class="Import Data", to_class="quotes", rel_name="imported_data")

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
    node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.match(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2

    for root_id in node_id_list:
        # Locate the "quotes" data node, and count the links in/out of it
        assert db.count_links(match=root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
        assert db.count_links(match=root_id, rel_name="in_category", rel_dir="OUT", neighbor_labels="Category") == 1

        q = '''
            MATCH (i: `Import Data` {`_CLASS`: "Import Data"})
                  -[:imported_data]->(q :quotes {`_CLASS`: "quotes"})
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        #print(result)
        assert len(result) == 1

        # Traverse the graph, but this time also passing thru the category data and schema nodes
        q = '''
            MATCH (i: `Import Data` {`_CLASS`: "Import Data"})
                  -[:imported_data]->(q :quotes {`_CLASS`: "quotes"})
                  -[:in_category]->(cat :Category {`_CLASS`: "Category"})
            WHERE i.date = date() AND id(q) = $quote_id
            RETURN q, cat 
            '''
        #print(q)
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
    new_node_id_list = GraphSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    #print("new_node_id_list: ", new_node_id_list)
    assert len(new_node_id_list) == 1
    new_root_id = new_node_id_list[0]

    # Locate the latest "quotes" data node, and count the links in/out of it
    assert db.count_links(match=new_root_id, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=new_root_id, rel_name="in_category", rel_dir="OUT", neighbor_labels="Category") == 2

    # Traverse the graph, going thru the 2 category data nodes
    q = '''
            MATCH 
                (cat2 :Category {name: "Philosophy", `_CLASS`: "Category"})
                <-[:in_category]-(q :quotes)-[:in_category]->(cat1 :Category {name: "French Literature", `_CLASS`: "Category"})
            WHERE id(q) = $quote_id
            RETURN q, cat1, cat2
            '''
    result = db.query(q, data_binding={"quote_id": new_root_id})
    assert len(result) == 1
    record = result[0]
    assert record["q"]["attribution"] == "Proust"
    assert record["q"]["quote"] == "My destination is no longer a place, rather a new way of seeing"
    assert record["q"]["verified"] == False

    # Locate the data node for the Class "Import Data", and count the links in/out of it
    match = db.match(labels="CLASS", key_name="name", key_value="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Verify the data types  (Note: APOC must be installed, and enabled in the Neo4j config file)
    q = '''
        MATCH (n)
        WHERE id(n) = $quote_id
        RETURN apoc.meta.cypher.types(n) AS data_types  
    '''
    data_types = db.query(q, data_binding={"quote_id": new_root_id}, single_cell="data_types")
    #print(data_types)
    assert data_types == {'verified': 'BOOLEAN', 'attribution': 'STRING', 'quote': 'STRING', '_CLASS': 'STRING'}    # 'uri': 'INTEGER' (not in current use)



def test_import_triplestore(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties(name="Course", strict=True,
                                             properties=["uri", "Course Title", "School", "Semester"])

    df = pd.DataFrame({"subject": [57, 57, 57],
                       "predicate": [1, 2, 3],
                       "object": ["Advanced Graph Databases", "New York University", "Fall 2024"]})

    result = GraphSchema.import_triplestore(df=df, class_node="Course",
                                            col_names = {1: "Course Title", 2: "School", 3: "Semester"},
                                            uri_prefix = "r-")
    assert len(result) == 1

    internal_id = result[0]
    lookup = db.get_nodes(internal_id)
    assert lookup == [{'School': 'New York University', 'Semester': 'Fall 2024', 'Course Title': 'Advanced Graph Databases', 'uri': 'r-57', '_CLASS': 'Course'}]


    # A second 1-entity import
    df = pd.DataFrame({"subject": ["MCB 273", "MCB 273", "MCB 273"],
                       "predicate": ["Course Title", "School", "Semester"],
                       "object": ["Systems Biology", "UC Berkeley", "Spring 2023"]})

    result = GraphSchema.import_triplestore(df=df, class_node="Course")
    assert len(result) == 1

    internal_id = result[0]
    lookup = db.get_nodes(internal_id)
    assert lookup == [{'School': 'UC Berkeley', 'Semester': 'Spring 2023', 'Course Title': 'Systems Biology', 'uri': 'MCB 273', '_CLASS': 'Course'}]



def test_scrub_dict():
    d = {"a": 1,
         "b": 3.5, "c": float("nan"),
         "d": "some value", "e": "   needs  cleaning!    ",
         "f": "", "g": "            ",
         "h": (1, 2)}

    result = GraphSchema.scrub_dict(d)
    assert result == {"a": 1,
                      "b": 3.5,
                      "d": "some value", "e": "needs  cleaning!",
                      "h": (1, 2)}
