# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.utilities.comparisons import compare_recordsets
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=True)
    NeoSchema.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE SCHEMAS  **************

def create_sample_schema_1():
    # patient/result/doctor
    sch_1 = NeoSchema.new_class_with_properties(class_name="patient",
                                                property_list=["name", "age", "balance"])

    sch_2 = NeoSchema.new_class_with_properties(class_name="result",
                                                property_list=["biomarker", "value"])

    sch_3 = NeoSchema.new_class_with_properties(class_name="doctor",
                                                property_list=["name", "specialty"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="HAS_RESULT")
    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_3, rel_name="IS_ATTENDED_BY")

    return {"patient": sch_1, "result": sch_2, "doctor": sch_3}



def create_sample_schema_2():
    # Class "quotes" with relationship "in_category" to class "Categories"
    sch_1 = NeoSchema.new_class_with_properties(class_name="quotes",
                                                property_list=["quote", "attribution", "verified"])

    sch_2 = NeoSchema.new_class_with_properties(class_name="Categories",
                                                property_list=["name", "remarks"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="in_category")

    return {"quotes": sch_1, "categories": "sch_2"}



#############   CLASS-related   #############

def test_create_class(db):
    db.empty_dbase()

    french_class_id = NeoSchema.create_class("French Vocabulary")
    match = db.find()   # All nodes
    result = db.get_nodes(match)
    assert result == [{'name': 'French Vocabulary', 'schema_id': french_class_id, 'type': 'L'}]

    class_A_id = NeoSchema.create_class("A", schema_type="S")
    result = db.get_nodes(match)
    expected = [{'name': 'French Vocabulary', 'schema_id': french_class_id, 'type': 'L'},
                {'name': 'A', 'schema_id': class_A_id, 'type': 'S'}]
    assert compare_recordsets(result, expected)

    with pytest.raises(Exception):
        assert NeoSchema.create_class("A", schema_type="L")  # A class by that name already exists; so, nothing gets created

    with pytest.raises(Exception):
        assert NeoSchema.create_class("B", schema_type="X")   # Non-existent schema_type that raises exception



def test_get_class_id(db):
    db.empty_dbase()
    class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_id("A") == class_A_id

    class_B_id = NeoSchema.create_class("B")
    assert NeoSchema.get_class_id("A") == class_A_id
    assert NeoSchema.get_class_id("B") == class_B_id

    assert NeoSchema.get_class_id("NON-EXISTENT CLASS") == -1



def test_class_exists(db):
    pass    # TODO



def test_class_name_exists(db):
    pass    # TODO



def test_get_class_name(db):
    db.empty_dbase()    # Completely clear the database
    class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_name(class_A_id) == "A"

    class_B_id = NeoSchema.create_class("B")
    assert NeoSchema.get_class_name(class_A_id) == "A"
    assert NeoSchema.get_class_name(class_B_id) == "B"

    assert NeoSchema.get_class_name(2345) == ""
    assert NeoSchema.get_class_name(-1) == ""



def test_get_all_classes(db):
    db.empty_dbase()    # Completely clear the database

    class_list = NeoSchema.get_all_classes()
    assert class_list == []

    NeoSchema.create_class("p")
    class_list = NeoSchema.get_all_classes()
    assert class_list == ['p']

    NeoSchema.create_class("A")
    NeoSchema.create_class("c")

    class_list = NeoSchema.get_all_classes()
    assert class_list == ['A', 'c', 'p']



def test_create_class_relationship(db):
    db.empty_dbase()        # Completely clear the database
    french_class_id = NeoSchema.create_class("French Vocabulary")
    foreign_class_id = NeoSchema.create_class("Foreign Vocabulary")
    NeoSchema.create_class_relationship(from_id=french_class_id, to_id=foreign_class_id, rel_name="INSTANCE_OF")

    q = f'''
        MATCH (from :CLASS {{name:"French Vocabulary"}})
        -[:INSTANCE_OF]
        ->(:CLASS {{schema_id: {foreign_class_id}}}) 
        RETURN count(from) AS number_found
        '''

    assert db.query(q, single_cell="number_found") == 1

    # Attempting to create an identical link between the same nodes will result in an Exception
    with pytest.raises(Exception):
        assert NeoSchema.create_class_relationship(from_id=french_class_id, to_id=foreign_class_id, rel_name="INSTANCE_OF")


    # Blank or None name will also raise an Exception
    with pytest.raises(Exception):
        assert NeoSchema.create_class_relationship(from_id=french_class_id, to_id=foreign_class_id, rel_name="")
        assert NeoSchema.create_class_relationship(from_id=french_class_id, to_id=foreign_class_id, rel_name=None)



def test_rename_class_rel(db):
    pass    # TODO



def test_delete_class_relationship(db):
    pass    # TODO



def test_unlink_classes(db):
    pass    # TODO



def test_delete_class(db):
    pass    # TODO


def test_allows_data_nodes(db):
    pass    # TODO



def test_get_class_instances(db):
    pass    # TODO



def test_get_related_class_names(db):
    pass    # TODO



def test_get_class_relationships(db):
    pass    # TODO




#############   PROPERTIES-RELATED   #############


def test_get_class_properties(db):
    pass    # TODO



def test_add_properties_to_class(db):
    pass    # TODO



def test_new_class_with_properties(db):
    pass    # TODO



def test_remove_property_from_class(db):
    pass    # TODO




#############   SCHEMA-CODE  RELATED   ###########

def test_get_schema_code(db):
    pass    # TODO



def test_get_schema_id(db):
    db.empty_dbase()
    schema_id_i = NeoSchema.create_class("My_class", code="i")
    schema_id_n = NeoSchema.create_class("My_other_class", code="n")

    assert NeoSchema.get_schema_id(schema_code="i") == schema_id_i
    assert NeoSchema.get_schema_id(schema_code="n") == schema_id_n
    assert NeoSchema.get_schema_id(schema_code="x") == -1



#############   DATA POINTS   ###########

def test_all_properties(db):
    pass    # TODO


def test_fetch_data_point(db):
    pass    # TODO



def test_add_data_point(db):
    db.empty_dbase()

    create_sample_schema_1()

    doctor_data_id = NeoSchema.add_data_point(class_name="doctor",
                             data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"})

    result_data_id = NeoSchema.add_data_point(class_name="result",
                             data_dict={"biomarker": "glucose", "value": 99.0})

    q = '''
        MATCH (d:doctor {item_id: $doctor, name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]-(c1:CLASS)
            -[*]-
            (c2:CLASS)<-[:SCHEMA]-(r:result {item_id: $result, biomarker: "glucose", value: 99.0})
        RETURN d, c1, c2, r
        '''

    #db.debug_print(q, data_binding={"doctor": doctor_data_id, "result": result_data_id}, force_output=True)

    result = db.query(q, data_binding={"doctor": doctor_data_id, "result": result_data_id})
    print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c1"]["name"] == "doctor"
    assert record["c2"]["name"] == "result"



def test_add_and_link_data_point(db):
    db.empty_dbase()

    create_sample_schema_1()

    doctor_data_id = NeoSchema.add_data_point(class_name="doctor",
                                              data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"})

    result_data_id = NeoSchema.add_data_point(class_name="result",
                                              data_dict={"biomarker": "glucose", "value": 99.0})

    patient_data_id = NeoSchema.add_and_link_data_point(class_name="patient",
                                      data_dict={"name": "Jill", "age": 19, "balance": 312.15},
                                      connected_to_list = [ (doctor_data_id, "IS_ATTENDED_BY") , (result_data_id, "HAS_RESULT") ])

    # Traverse a loop in the graph, from the patient data node, back to itself - going thru data and schema nodes
    q = '''
        MATCH (p:patient {item_id: $patient, name: "Jill", age: 19, balance: 312.15})-[:IS_ATTENDED_BY]->
            (d:doctor {item_id: $doctor, name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]-(c1:CLASS)
            -[*]-
            (c2:CLASS)<-[:SCHEMA]-(r:result {item_id: $result, biomarker: "glucose", value: 99.0})
            <-[:HAS_RESULT]-(p)
        RETURN d, c1, c2, r
        '''

    result = db.query(q, data_binding={"patient": patient_data_id, "doctor": doctor_data_id, "result": result_data_id})
    print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c1"]["name"] == "doctor"
    assert record["c2"]["name"] == "result"


    # Attempt to sneak in a relationship not in the Schema
    with pytest.raises(Exception):
        NeoSchema.add_and_link_data_point(class_name="patient",
                          data_dict={"name": "Jill", "age": 19, "balance": 312.15},
                          connected_to_list = [ (doctor_data_id, "NOT_A_DECLARED_RELATIONSHIP") , (result_data_id, "HAS_RESULT") ])


    # Attempt to use a Class not in the Schema
    with pytest.raises(Exception):
        NeoSchema.add_and_link_data_point(class_name="NO_SUCH CLASS",
                                          data_dict={"name": "Jill", "age": 19, "balance": 312.15},
                                          connected_to_list = [ ])




def test_register_existing_data_point(db):
    pass    # TODO



def test_delete_data_point(db):
    pass    # TODO



def test_add_data_relationship(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=123, to_id=456, rel_name="junk")  # No such nodes exist

    neo_id_1 = db.create_node("random A")
    neo_id_2 = db.create_node("random B")
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=neo_id_1, to_id=neo_id_2, rel_name="junk") # Not data nodes with a Schema

    person_class_id = NeoSchema.create_class("Person")
    person_id = NeoSchema.add_data_point("Person")

    car_class_id = NeoSchema.create_class("Car")
    car_id = NeoSchema.add_data_point("Car")

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="DRIVES", id_type="item_id")

    # Add the "DRIVE" relationship between the classes
    NeoSchema.create_class_relationship(from_id=person_class_id, to_id=car_class_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="", id_type="item_id")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name=None, id_type="item_id")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=car_id, to_id=person_id, rel_name="DRIVES", id_type="item_id")  # Wrong direction

    # Now it works
    NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="DRIVES", id_type="item_id")

    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="DRIVES", id_type="item_id")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="SOME_OTHER_NAME", id_type="item_id")


    # Now add reverse a relationship, and this use the Neo4j ID's to locate the nodes
    NeoSchema.create_class_relationship(from_id=car_class_id, to_id=person_class_id, rel_name="IS_DRIVEN_BY")

    neo_person_id = NeoSchema.get_data_point_id(person_id)
    neo_car_id = NeoSchema.get_data_point_id(car_id)
    NeoSchema.add_data_relationship(from_id=neo_car_id, to_id=neo_person_id, rel_name="IS_DRIVEN_BY")



def test_remove_data_relationship(db):
    pass    # TODO



def test_locate_node(db):
    pass    # TODO



def test_class_of_data_point(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.class_of_data_point(node_id=123)  # No such data node exists

    neo_id = db.create_node("random")
    with pytest.raises(Exception):
        NeoSchema.class_of_data_point(node_id=neo_id)     # It's not a data node

    NeoSchema.create_class("Person")
    item_id = NeoSchema.add_data_point("Person")

    assert NeoSchema.class_of_data_point(node_id=item_id, id_type="item_id") == "Person"
    assert NeoSchema.class_of_data_point(node_id=item_id, id_type="item_id", labels="Person") == "Person"

    # Now locate thru the Neo4j ID
    neo_id = NeoSchema.get_data_point_id(item_id)
    #print("neo_id: ", neo_id)
    assert NeoSchema.class_of_data_point(node_id=neo_id) == "Person"

    NeoSchema.create_class("Extra")
    # Create a forbidden scenario with a data node having 2 Schema classes
    q = f'''
        MATCH (n {{item_id: {item_id} }}), (c :CLASS {{name: 'Extra'}})
        MERGE (n)-[:SCHEMA]->(c)
        '''
    #db.debug_print(q, {}, "test")
    db.update_query(q)
    with pytest.raises(Exception):
        assert NeoSchema.class_of_data_point(node_id=neo_id) == "Person"    # Data node is associated to multiple classes



def test_data_points_of_class(db):
    pass    # TODO



def test_data_points_lacking_schema(db):
    pass    # TODO



def test_get_data_point_id(db):
    pass    # TODO




#############   DATA IMPORT   ###########

# See separate file


#############   EXPORT SCHEMA   ###########


###############   INTERNAL  METHODS   ###############

def test_valid_schema_id(db):
    db.empty_dbase()
    result = NeoSchema.create_class("Records")
    assert NeoSchema.valid_schema_id(result)



def test_next_available_id(db):
    pass    # TODO



def test_next_autoincrement(db):
    db.empty_dbase()
    assert NeoSchema.next_autoincrement("a") == 1
    assert NeoSchema.next_autoincrement("a") == 2
    assert NeoSchema.next_autoincrement("a") == 3
    assert NeoSchema.next_autoincrement("schema") == 1
    assert NeoSchema.next_autoincrement("schema") == 2
    assert NeoSchema.next_autoincrement("data_node") == 1
    assert NeoSchema.next_autoincrement("data_node") == 2


def test_next_available_datapoint_id(db):
    db.empty_dbase()
    assert NeoSchema.next_available_datapoint_id() == 1
    assert NeoSchema.next_available_datapoint_id() == 2
    assert NeoSchema.next_available_datapoint_id() == 3
