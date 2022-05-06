# Testing of Schema-based Data Import
# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.utilities.comparisons import compare_recordsets
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from tests.test_neoschema import create_sample_schema_1, create_sample_schema_2


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=True)
    NeoSchema.set_database(neo_obj)
    yield neo_obj



def test_create_data_nodes_from_python_data_1(db):
    db.empty_dbase()

    # Set up the Schema
    sch_1 = NeoSchema.new_class_with_properties(class_name="Import Data",
                                        property_list=["source", "date"])

    sch_2 = NeoSchema.new_class_with_properties(class_name="my_class_1",
                                    property_list=["legit", "other"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="imported_data")


    # 1-layer dictionary, with a key in the Schema and one not

    data = {"legit": 123, "unexpected": 456}
    # Import step
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="my_class_1")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    q = '''
        MATCH (c1:CLASS {name:"Import Data"})<-[:SCHEMA]-
              (n1:`Import Data`)-[:imported_data]->(n2:my_class_1 {item_id:$item_id})
              -[:SCHEMA]->(c2:CLASS {name:"my_class_1"})
        RETURN n2
        '''
    root_record = db.query(q, data_binding={"item_id": root_id}, single_row=True)
    assert root_record["n2"] == {"legit": 123, "item_id": root_id}     # Only the key in the Schema gets imported



def test_create_data_nodes_from_python_data_2(db):
    db.empty_dbase()

    # Set up the Schema.  Nothing in it yet, other than the "Import Data" node
    NeoSchema.new_class_with_properties(class_name="Import Data",
                                                property_list=["source", "date"])


    data = {"arbitrary": "Doesn't matter"}

    # Import step
    with pytest.raises(Exception):
        NeoSchema.create_data_nodes_from_python_data(data, class_name="non_existant_class")

    # Even though the import got aborted and raised an Exception, the `Import Data` is left behind
    q = '''
        MATCH (n:`Import Data` {date: date()}) RETURN n
        '''
    result = db.query(q)
    assert len(result) == 1



def test_create_data_nodes_from_python_data_3(db):
    db.empty_dbase()

    # Set up Schema that only contains parts of the attributes in the data - and lacks the "result" relationship
    sch_1 = NeoSchema.new_class_with_properties(class_name="Import Data",
                                        property_list=["source", "date"])
    sch_2 = NeoSchema.new_class_with_properties(class_name="patient",
                                                property_list=["age", "balance"])
    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="imported_data")


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
              (n1:`Import Data`)-[:imported_data]->(n2:patient {item_id:$item_id})
              -[:SCHEMA]->(c2:CLASS {name:"patient"})
        RETURN n2
        '''
    root_record = db.query(q, data_binding={"item_id": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    assert root_record["n2"] == {"age": 23, "balance": 150.25, "item_id": root_id}
    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    result = db.query(q)
    assert len(result) == 0



def test_create_data_nodes_from_python_data_4(db):
    db.empty_dbase()

    sch_info = create_sample_schema_1()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                   property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["patient"], rel_name="imported_data")


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
              (n1:`Import Data`)-[:imported_data]->(n2:patient {item_id:$item_id})
              -[:SCHEMA]->(c2:CLASS {name:"patient"})
        RETURN n2
        '''
    root_record = db.query(q, data_binding={"item_id": root_id}, single_row=True)

    # Only the keys in the Schema gets imported; the relationship "result" is not in the Schema, either
    assert root_record["n2"] == {"name": "Stephanie", "age": 23, "balance": 150.25, "item_id": root_id}
    q = '''MATCH (n:patient)-[:result]-(m) RETURN n, m'''
    result = db.query(q)
    assert len(result) == 0

    # Locate the "patient" data node
    match = db.find(key_name="item_id", key_value=root_id)

    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=match, rel_name="result", rel_dir="BOTH") == 0



def test_create_data_nodes_from_python_data_5(db):
    db.empty_dbase()

    sch_info = create_sample_schema_1()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                     property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["patient"], rel_name="imported_data")


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
        MATCH (p:patient {item_id: $patient, name: "Stephanie", age: 23, balance: 150.25})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0})-[:SCHEMA]->(cl_r:CLASS {name:"result"})
            <-[:HAS_RESULT]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)<-[:imported_data]-(i: `Import Data`)
        WHERE i.date = date()
        RETURN p, r, cl_r, cl_p, i
        '''
    result = db.query(q, data_binding={"patient": root_id})

    print(result)
    # Only the keys in the Schema gets imported; the relationship "HAS_RESULT" is in the Schema
    assert len(result) == 1

    # The relationship "WRONG_LINK_TO_DOCTOR" is not in the Schema
    q = '''MATCH (n:patient)-[:WRONG_LINK_TO_DOCTOR]-(m) RETURN n, m'''
    result = db.query(q)
    assert len(result) == 0

    # Locate the "patient" data node
    match = db.find(key_name="item_id", key_value=root_id)
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="OUT", neighbor_labels="result") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=match, rel_name="WRONG_LINK_TO_DOCTOR", rel_dir="BOTH") == 0

    # Locate the "result" data node
    match = db.find(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1




def test_create_data_nodes_from_python_data_6(db):
    db.empty_dbase()

    sch_info = create_sample_schema_1()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                     property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["patient"], rel_name="imported_data")


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
        MATCH (p:patient {item_id: $patient, name: "Stephanie", age: 23, balance: 150.25})-[:HAS_RESULT]->
            (r:result {biomarker:"insulin", value: 123.0})-[:SCHEMA]->(cl_r:CLASS {name:"result"})
            <-[:HAS_RESULT]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)<-[:imported_data]-(i: `Import Data`)
        WHERE i.date = date()
        RETURN p, r, cl_r, cl_p, i
        '''
    result = db.query(q, data_binding={"patient": root_id})
    #print(result)
    assert len(result) == 1

    # Again, traverse a loop in the graph, from the patient data node, back to itself,
    # but this time going thru the `doctor` data and schema nodes
    q = '''
        MATCH (p:patient {item_id: $patient, name: "Stephanie", age: 23, balance: 150.25})-[:IS_ATTENDED_BY]->
            (d:doctor {name:"Dr. Kane", specialty: "OB/GYN"})-[:SCHEMA]->(cl_d:CLASS {name:"doctor"})
            <-[:IS_ATTENDED_BY]-(cl_p:CLASS {name:"patient"})<-[:SCHEMA]-(p)
        RETURN p, d, cl_d, cl_p
        '''
    result = db.query(q, data_binding={"patient": root_id})
    #print(result)
    assert len(result) == 1


    # Locate the "patient" data node
    match = db.find(key_name="item_id", key_value=root_id)
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="OUT", neighbor_labels="result") == 1
    assert db.count_links(match=match, rel_name="IS_ATTENDED_BY", rel_dir="OUT", neighbor_labels="doctor") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1

    # Locate the "result" data node
    match = db.find(labels="result")
    assert db.count_links(match=match, rel_name="HAS_RESULT", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "doctor" data node
    match = db.find(labels="doctor")
    assert db.count_links(match=match, rel_name="IS_ATTENDED_BY", rel_dir="IN", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "Import Data" data node
    match = db.find(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="patient") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1



def test_create_data_nodes_from_python_data_7(db):
    db.empty_dbase()

    sch_info = create_sample_schema_2()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                     property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["quotes"], rel_name="imported_data")

    data = [
                {   "quote": "I wasn't kissing her. I was whispering in her mouth",
                    "attribution": "Chico Marx"
                }
           ]

    # Import
    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="quotes")
    print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 1
    root_id = node_id_list[0]

    # Traverse a loop in the graph, from the `quotes` data node, back to itself,
    # going thru the data and schema nodes
    q = '''
        MATCH (q :quotes {item_id: $quote_id, attribution: "Chico Marx", quote: "I wasn't kissing her. I was whispering in her mouth"})
            -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
            <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
            -[:imported_data]->(q)
        WHERE i.date = date()
        RETURN q, cl_q, cl_i
        '''
    result = db.query(q, data_binding={"quote_id": root_id})
    print(result)
    assert len(result) == 1

    # Locate the "Import Data" data node
    match = db.find(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 1
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Locate the "quotes" data node
    match = db.find(key_name="item_id", key_value=root_id)
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_8(db):
    # Similar to test_create_data_nodes_from_python_data_7, but importing 2 quotes instead of 1,
    # and introducing non-Schema data
    db.empty_dbase()

    sch_info = create_sample_schema_2()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                     property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["quotes"], rel_name="imported_data")

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
    print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.find(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    for root_id in node_id_list:
        # Traverse a loop in the graph, from the `quotes` data node, back to itself,
        # going thru the data and schema nodes
        q = '''
            MATCH (q :quotes {item_id: $quote_id})
                -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
                <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                -[:imported_data]->(q)
            WHERE i.date = date()
            RETURN q, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        print(result)
        assert len(result) == 1

        # Locate the "quotes" data node
        match = db.find(key_name="item_id", key_value=root_id)
        assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
        assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1



def test_create_data_nodes_from_python_data_9(db):
    # Similar to test_create_data_nodes_from_python_data_8, but also using the class "Categories"
    db.empty_dbase()

    sch_info = create_sample_schema_2()
    # Add to the Schema the "Import Data" node, and a link to the Class of the import's root
    sch_import = NeoSchema.new_class_with_properties(class_name="Import Data",
                                                     property_list=["source", "date"])
    NeoSchema.create_class_relationship(from_id=sch_import, to_id=sch_info["quotes"], rel_name="imported_data")

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
    print("node_id_list: ", node_id_list)
    assert len(node_id_list) == 2

    # Locate the "Import Data" data node
    match = db.find(labels="Import Data")
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="quotes") == 2
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    for root_id in node_id_list:
        # Locate the "quotes" data node
        match = db.find(key_name="item_id", key_value=root_id)
        assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1
        assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
        assert db.count_links(match=match, rel_name="in_category", rel_dir="OUT", neighbor_labels="Categories") == 1

        # Traverse a loop in the graph, from the `quotes` data node, back to itself,
        # going thru the data and schema nodes
        q = '''
            MATCH (q :quotes {item_id: $quote_id})
                -[:SCHEMA]->(cl_q :CLASS {name:"quotes"})
                <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                -[:imported_data]->(q)
            WHERE i.date = date()
            RETURN q, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        print(result)
        assert len(result) == 1

        # Traverse a longer loop in the graph, again from the `quotes` data node to itself,
        # but this time also passing thru the category data and schema nodes
        q = '''
            MATCH (q :quotes {item_id: $quote_id})-[:in_category]->(cat :Categories)
                -[:SCHEMA]->(cl_c :CLASS {name:"Categories"})<-[:in_category]-
                (cl_q :CLASS {name:"quotes"})
                <-[:imported_data]-(cl_i :CLASS {name:"Import Data"})<-[:SCHEMA]-(i: `Import Data`)
                -[:imported_data]->(q)
            WHERE i.date = date()
            RETURN q, cat, cl_q, cl_i
            '''
        result = db.query(q, data_binding={"quote_id": root_id})
        print(result)
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
    print("new_node_id_list: ", new_node_id_list)
    assert len(new_node_id_list) == 1
    new_root_id = new_node_id_list[0]

    # Locate the latest "quotes" data node
    match = db.find(labels="quotes", key_name="item_id", key_value=new_root_id)
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="IN", neighbor_labels="Import Data") == 1
    assert db.count_links(match=match, rel_name="in_category", rel_dir="OUT", neighbor_labels="Categories") == 2
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Traverse a loop in the graph, from the `quotes` data node back to itself,
    # going thru the 2 category data nodes and their shared Schema node
    q = '''
            MATCH (q :quotes {item_id: $quote_id})-[:in_category]->(cat1 :Categories {name: "French Literature"})
            -[:SCHEMA]->(cl_c :CLASS {name:"Categories"})
            <-[:SCHEMA]-(cat2 :Categories {name: "Philosophy"})
            <-[:in_category]-(q)

            RETURN q, cat1, cl_c, cat2
            '''
    result = db.query(q, data_binding={"quote_id": new_root_id})
    print(result)
    assert len(result) == 1
    record = result[0]
    assert record["q"]["attribution"] == "Proust"
    assert record["q"]["quote"] == "My destination is no longer a place, rather a new way of seeing"
    assert record["q"]["verified"] == False

    # Locate the data node for the Class "Import Data"
    match = db.find(labels="CLASS", key_name="name", key_value="Import Data")
    assert db.count_links(match=match, rel_name="SCHEMA", rel_dir="IN", neighbor_labels="Import Data") == 2
    assert db.count_links(match=match, rel_name="imported_data", rel_dir="OUT", neighbor_labels="CLASS") == 1

    # Verify the data types
    q = '''
        MATCH (n {item_id: $quote_id})
        RETURN apoc.meta.cypher.types(n) AS data_types  
    '''
    data_types = db.query(q, data_binding={"quote_id": new_root_id}, single_cell="data_types")
    print(data_types)
    assert data_types == {'verified': 'BOOLEAN', 'attribution': 'STRING', 'quote': 'STRING', 'item_id': 'INTEGER'}
