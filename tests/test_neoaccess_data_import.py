# Testing of Data Import

import pytest
from BrainAnnex.modules.utilities.comparisons import *
from BrainAnnex.modules.neo_access import neo_access



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=False, verbose=False)
    yield neo_obj



def test_create_nodes_from_python_data_1(db):
    db.empty_dbase()

    # A literal
    data = 123
    new_id_list = db.create_nodes_from_python_data(data, root_labels="literal")
    assert len(new_id_list) == 1
    new_id = new_id_list[0]
    result = db.fetch_nodes(match=new_id, single_row=True)
    assert result == {"value": 123}
    assert db.get_node_labels(new_id) == ["literal"]


    # 1-layer dictionaries

    data = {"a": 123}
    new_id_list = db.create_nodes_from_python_data(data, root_labels="dict1")
    assert len(new_id_list) == 1
    new_id = new_id_list[0]
    result = db.fetch_nodes(match=new_id, single_row=True)
    assert result == {"a": 123}
    assert db.get_node_labels(new_id) == ["dict1"]


    data = {"name": "Joe",
            "sales": True,
            "salary": 52000,
            "performance scale": 3.4,
            "team": None}
    new_id_list = db.create_nodes_from_python_data(data, root_labels="dict2")
    assert len(new_id_list) == 1
    new_id = new_id_list[0]
    result = db.fetch_nodes(match=new_id, single_row=True)
    print(result)
    assert result == {'name': 'Joe', 'sales': True, 'salary': 52000, 'performance scale': 3.4}
    assert db.get_node_labels(new_id) == ["dict2"]


    # 1-layer lists

    data = [1, 2, 3]
    new_id_list = db.create_nodes_from_python_data(data, root_labels="list1")
    extracted_data = []
    for new_id in new_id_list:
        result = db.fetch_nodes(match=new_id, single_row=True)
        print(result)
        assert db.get_node_labels(new_id) == ["list1"]
        assert len(result) == 1
        extracted_data.append(result["value"])

    assert compare_unordered_lists(extracted_data, data)


    data = [1, 2.5, True, False,  None, "hello"]
    new_id_list = db.create_nodes_from_python_data(data, root_labels="list2")
    extracted_data = []
    for new_id in new_id_list:
        result = db.fetch_nodes(match=new_id, single_row=True)
        print(result)
        assert db.get_node_labels(new_id) == ["list2"]
        assert len(result) == 1
        extracted_data.append(result["value"])

    assert compare_unordered_lists(extracted_data + [None] , data)  # Need to add [None] because dropped from import



def test_create_nodes_from_python_data_2(db):
    db.empty_dbase()

    # A dictionary containing another dictionary
    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "result": {
                    "biomarker": "insulin",
                    "value": 123.
                },
                "balance": 150.25,
                "insurance": False
                }
    new_id_list = db.create_nodes_from_python_data(data, root_labels="dict_dict")
    assert len(new_id_list) == 1
    new_id = new_id_list[0]
    q = '''
        MATCH (root :dict_dict {name: "Stephanie", age: 23, balance: 150.25, insurance: false}) 
                -[:result]->(n1 :result {biomarker: "insulin", value: 123.0})
        RETURN id(root) AS id0
        '''     # , id(n1) AS id1
    result = db.query(q, single_row=True)
    assert result == {"id0": new_id}



def test_create_nodes_from_python_data_3(db):
    db.empty_dbase()

    # A dictionary containing a simple list
    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "measurements": [1, 2, 3.14],
                "balance": 150.25,
                "insurance": False
                }
    new_id_list = db.create_nodes_from_python_data(data, root_labels="dict_list")
    assert len(new_id_list) == 1
    new_id = new_id_list[0]

    q = '''
        MATCH (root :dict_list {name: "Stephanie", age: 23, balance: 150.25, insurance: false}) 
                    -[:measurements]->(n1 :measurements {value: 1}),
              (root)-[:measurements]->(n2 :measurements {value: 2}),
              (root)-[:measurements]->(n3 :measurements {value: 3.14})
        RETURN id(root) AS id_root
        '''
    result = db.query(q, single_row=True)
    assert result == {"id_root": new_id}



def test_create_nodes_from_python_data_4(db):
    db.empty_dbase()

    # A dictionary containing a complex list
    data = {    "name": "Stephanie",
                "age": 23,
                "referred by": None,
                "results": [
                    {
                        "biomarker": "insulin",
                        "value": 123.
                    },
                    {
                        "biomarker": "bilirubin",
                        "value": 0.8
                    }
                ],
                "balance": 150.25,
                "insurance": False
                }
    new_id_list = db.create_nodes_from_python_data(data, root_labels="dict_list_2")
    assert len(new_id_list) == 1
    root_id = new_id_list[0]

    q = '''
        MATCH (root :dict_list_2 {name: "Stephanie", age: 23, balance: 150.25, insurance: false}) 
                    -[:results]->(n1 :results {biomarker: "insulin", value: 123.0}),
              (root)-[:results]->(n2 :results {biomarker: "bilirubin", value: 0.8})
        RETURN id(root) AS id_root
        '''
    result = db.query(q, single_row=True)
    assert result == {"id_root": root_id}



def test_create_nodes_from_python_data_5(db):
    db.empty_dbase()

    # A list containing a dictionary
    data = [1, 2.5, True, False, {"a": 123}, None, "hello"]
    new_id_list = db.create_nodes_from_python_data(data, root_labels="list_dict")

    q = '''
        MATCH (n0:list_dict {value: 1}),
              (n1:list_dict {value: 2.5}),
              (n2:list_dict {value: true}),
              (n3:list_dict {value: false}),
              (n4:list_dict {a: 123}),
              (n5:list_dict {value: "hello"})
         RETURN id(n0), id(n1), id(n2), id(n3), id(n4), id(n5)
    '''
    result = db.query(q, single_row=True)
    assert compare_unordered_lists(result.values() , new_id_list)



def test_create_nodes_from_python_data_6(db):
    db.empty_dbase()

    # A list containing a list
    data = [1, 2.5, True, False, [10, 20], None, "hello"]
    new_id_list = db.create_nodes_from_python_data(data, root_labels="list_list")

    q = '''
        MATCH (n0:list_list {value: 1}),
              (n1:list_list {value: 2.5}),
              (n2:list_list {value: true}),
              (n3:list_list {value: false}),
                    (n4:list_list)-[:list_list]->(c1:list_list {value: 10}),
                    (n4)-[:list_list]->(c2:list_list {value: 20}),
              (n5:list_list {value: "hello"})
         RETURN id(n0), id(n1), id(n2), id(n3), id(n4), id(n5)
    '''
    result = db.query(q, single_row=True)
    print(result)
    assert compare_unordered_lists(result.values() , new_id_list)
