# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from utilities.comparisons import compare_unordered_lists, compare_recordsets
from brainannex import GraphAccess, GraphSchema
import neo4j.time


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    GraphSchema.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE SCHEMAS for the testing  **************

def create_sample_schema_1():
    # Schema with patient/result/doctor Classes (each with some Properties),
    # and relationships between the Classes: HAS_RESULT, IS_ATTENDED_BY (both originating from "patient"

    patient_id, _  = GraphSchema.create_class_with_properties(name="patient",
                                                              properties=["name", "age", "balance"], strict=True)

    result_id, _  = GraphSchema.create_class_with_properties(name="result",
                                                             properties=["biomarker", "value"], strict=False)

    doctor_id, _  = GraphSchema.create_class_with_properties(name="doctor",
                                                             properties=["name", "specialty"], strict=False)

    GraphSchema.create_class_relationship(from_class="patient", to_class="result", rel_name="HAS_RESULT")
    GraphSchema.create_class_relationship(from_class="patient", to_class="doctor", rel_name="IS_ATTENDED_BY")

    return {"patient": patient_id, "result": result_id, "doctor": doctor_id}



def create_sample_schema_2():
    # Class "quotes" with relationship named "in_category" to Class "Category";
    # each Class has some properties
    _, sch_1 = GraphSchema.create_class_with_properties(name="quotes",
                                                        properties=["quote", "attribution", "verified"])

    _, sch_2 = GraphSchema.create_class_with_properties(name="Category",
                                                        properties=["name", "remarks"])

    GraphSchema.create_class_relationship(from_class="quotes", to_class="Category", rel_name="in_category")

    return {"quotes": sch_1, "category": "sch_2"}




#############   CLASS-related   #############

def test_create_class(db):
    db.empty_dbase()

    _ , french_class_uri = GraphSchema.create_class("French Vocabulary")
    match_specs = db.match(labels="CLASS")   # All Class nodes
    result = db.get_nodes(match_specs)
    assert result == [{'name': 'French Vocabulary', 'uri': french_class_uri, 'strict': False}]

    _ , class_A_uri = GraphSchema.create_class("A", strict=True)
    result = db.get_nodes(match_specs)
    expected = [{'name': 'French Vocabulary', 'uri': french_class_uri, 'strict': False},
                {'name': 'A', 'uri': class_A_uri, 'strict': True}]
    assert compare_recordsets(result, expected)

    with pytest.raises(Exception):
        assert GraphSchema.create_class("A", strict=False)  # A class by that name already exists



def test_get_class_internal_id(db):
    db.empty_dbase()
    A_neo_uri, _ = GraphSchema.create_class("A")
    assert GraphSchema.get_class_internal_id("A") == A_neo_uri

    B_neo_uri, _ = GraphSchema.create_class("B")
    assert GraphSchema.get_class_internal_id("A") == A_neo_uri
    assert GraphSchema.get_class_internal_id("B") == B_neo_uri

    with pytest.raises(Exception):
        assert GraphSchema.get_class_internal_id("NON-EXISTENT CLASS")



def test_get_class_uri(db):
    db.empty_dbase()
    _ , class_A_uri = GraphSchema.create_class("A")
    assert GraphSchema.get_class_uri("A") == class_A_uri

    _ , class_B_uri = GraphSchema.create_class("B")
    assert GraphSchema.get_class_uri("A") == class_A_uri
    assert GraphSchema.get_class_uri("B") == class_B_uri

    with pytest.raises(Exception):
        assert GraphSchema.get_class_uri("NON-EXISTENT CLASS")



def test_get_class_uri_by_internal_id(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.get_class_uri_by_internal_id(999)   # Non-existent class

    class_A_neo_uri , class_A_uri = GraphSchema.create_class("A")
    assert GraphSchema.get_class_uri_by_internal_id(class_A_neo_uri) == class_A_uri

    class_B_neo_uri , class_B_uri = GraphSchema.create_class("B")
    assert GraphSchema.get_class_uri_by_internal_id(class_A_neo_uri) == class_A_uri
    assert GraphSchema.get_class_uri_by_internal_id(class_B_neo_uri) == class_B_uri



def test_class_uri_exists(db):
    db.empty_dbase()
    assert not GraphSchema.class_uri_exists("schema-123")

    with pytest.raises(Exception):
        assert GraphSchema.class_uri_exists(123)  # Not a string

    _ , class_A_uri = GraphSchema.create_class("A")
    assert GraphSchema.class_uri_exists(class_A_uri)



def test_class_name_exists(db):
    db.empty_dbase()

    assert not GraphSchema.class_name_exists("A")
    GraphSchema.create_class("A")
    assert GraphSchema.class_name_exists("A")

    with pytest.raises(Exception):
        assert GraphSchema.class_uri_exists("B")

    with pytest.raises(Exception):
        assert GraphSchema.class_uri_exists(123)



def test_get_class_name_by_schema_uri(db):
    db.empty_dbase()
    _ , class_A_uri = GraphSchema.create_class("A")
    assert GraphSchema.get_class_name_by_schema_uri(class_A_uri) == "A"

    _ , class_B_uri = GraphSchema.create_class("B")
    assert GraphSchema.get_class_name_by_schema_uri(class_A_uri) == "A"
    assert GraphSchema.get_class_name_by_schema_uri(class_B_uri) == "B"

    with pytest.raises(Exception):
        assert GraphSchema.get_class_name_by_schema_uri("schema-XYZ")

    with pytest.raises(Exception):
        assert GraphSchema.get_class_name_by_schema_uri(123)


def test_get_class_name(db):
    db.empty_dbase()
    class_A_neoid , _ = GraphSchema.create_class("A")
    assert GraphSchema.get_class_name(class_A_neoid) == "A"

    class_B_neoid , _ = GraphSchema.create_class("B")
    assert GraphSchema.get_class_name(class_A_neoid) == "A"
    assert GraphSchema.get_class_name(class_B_neoid) == "B"

    with pytest.raises(Exception):
        GraphSchema.get_class_name(2345)                    # No such Class exists

    with pytest.raises(Exception):
        GraphSchema.get_class_name(-1)                      # Invalid internal dbase id

    with pytest.raises(Exception):
        GraphSchema.get_class_name("I'm not an integer!")   # Invalid internal dbase id



def test_get_class_attributes(db):
    db.empty_dbase()

    class_A_neoid , class_A_uri = GraphSchema.create_class("A")
    assert GraphSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'uri': class_A_uri, 'strict': False}

    class_B_neoid , class_B_uri = GraphSchema.create_class("B", no_datanodes=True)
    assert GraphSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'uri': class_A_uri, 'strict': False}
    assert GraphSchema.get_class_attributes(class_B_neoid) == {'name': 'B', 'uri': class_B_uri, 'strict': False, 'no_datanodes': True}

    with pytest.raises(Exception):
        GraphSchema.get_class_attributes(2345)                    # No such Class exists
        GraphSchema.get_class_attributes(-1)                      # Invalid id
        GraphSchema.get_class_attributes("I'm not an integer!")   # Invalid id



def test_get_all_classes(db):
    db.empty_dbase()

    class_list = GraphSchema.get_all_classes()
    assert class_list == []

    GraphSchema.create_class("p")
    class_list = GraphSchema.get_all_classes()
    assert class_list == ['p']

    GraphSchema.create_class("A")
    GraphSchema.create_class("c")

    class_list = GraphSchema.get_all_classes()
    assert class_list == ['A', 'c', 'p']



def test_rename_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.rename_class(old_name="some name", new_name="some name")

    with pytest.raises(Exception):
        GraphSchema.rename_class(old_name="some name", new_name="")

    with pytest.raises(Exception):
        GraphSchema.rename_class(old_name="some name", new_name="    bad name    ")

    with pytest.raises(Exception):
        GraphSchema.rename_class(old_name="Car", new_name="Vehicle")  # Doesn't exist

    internal_id, _ = GraphSchema.create_class_with_properties("Car", strict=True,
                                                              properties=["color"])

    result = GraphSchema.rename_class(old_name="Car", new_name="Vehicle")
    assert result == 0       # No Data Nodes were affected

    q = f'''MATCH 
        (n:CLASS {{name:"Vehicle"}}) 
        WHERE id(n) = {internal_id} 
        RETURN count(n) AS number_found
        '''
    assert db.query(q, single_cell="number_found") == 1

    q = f'''MATCH 
        (n:CLASS {{name:"Car"}})     // The old name
        WHERE id(n) = {internal_id} 
        RETURN count(n) AS number_found
        '''
    assert db.query(q, single_cell="number_found") == 0


    # Now add a Data Node, prior to again renaming the Class
    data_node_id = GraphSchema.create_data_node(class_name="Vehicle", properties={"color": "white"},
                                                extra_labels="West Coast")

    result = GraphSchema.rename_class(old_name="Vehicle", new_name="Recreational Vehicle")
    assert result == 1      # 1 Data Nodes was affected

    q = f'''
        MATCH (n :`Recreational Vehicle`:`West Coast`) 
        WHERE id(n) = {data_node_id} AND n.`_CLASS` = "Recreational Vehicle" AND n.color = "white"
        RETURN count(n) AS number_found
        '''

    assert db.query(q, single_cell="number_found") == 1

    q = f'''MATCH 
        (n:CLASS {{name:"Recreational Vehicle"}}) 
        WHERE id(n) = {internal_id} 
        RETURN count(n) AS number_found
        '''
    assert db.query(q, single_cell="number_found") == 1

    q = f'''MATCH 
        (n:CLASS {{name:"Vehicle"}})    // The old name
        WHERE id(n) = {internal_id} 
        RETURN count(n) AS number_found
        '''
    assert db.query(q, single_cell="number_found") == 0



def test_create_class_relationship(db):
    db.empty_dbase()
    french_id , french_uri  = GraphSchema.create_class("French Vocabulary")
    foreign_id, foreign_uri = GraphSchema.create_class("Foreign Vocabulary")

    # Blank or None name will also raise an Exception
    with pytest.raises(Exception):
        assert GraphSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="")
    with pytest.raises(Exception):
        assert GraphSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name=None)

    GraphSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="INSTANCE_OF")

    q = f'''MATCH 
        (from :CLASS {{name:"French Vocabulary", uri: '{french_uri}'}})
        -[:INSTANCE_OF]
        ->(to :CLASS {{name:"Foreign Vocabulary", uri: '{foreign_uri}'}}) 
        WHERE id(from) = {french_id} AND id(to) = {foreign_id}
        RETURN count(from) AS number_found
        '''

    assert db.query(q, single_cell="number_found") == 1

    # Attempting to create an identical link between the same nodes will result in an Exception
    with pytest.raises(Exception):
        assert GraphSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="INSTANCE_OF")


    GraphSchema.create_class("German Vocabulary")
    # Mixing names and internal database ID's
    GraphSchema.create_class_relationship(from_class="German Vocabulary", to_class=foreign_id, rel_name="INSTANCE_OF")

    # Verify
    q = f'''MATCH 
        (from :CLASS {{name:"French Vocabulary", uri: '{french_uri}'}})
        -[:INSTANCE_OF]
        ->(to :CLASS {{name:"Foreign Vocabulary", uri: '{foreign_uri}'}})
        <-[:INSTANCE_OF]-(:CLASS {{name:"German Vocabulary"}})
        WHERE id(from) = {french_id} AND id(to) = {foreign_id}
        RETURN count(from) AS number_found
        '''
    assert db.query(q, single_cell="number_found") == 1


    _, course_uri = GraphSchema.create_class("Course")
    GraphSchema.create_class_relationship(from_class="Foreign Vocabulary", to_class="Course",
                                          rel_name="USED_IN", link_properties=["Frequency", "Usefulness"])

    # Verify
    q = f'''MATCH 
        (from :CLASS {{name:"Foreign Vocabulary", uri: '{foreign_uri}'}})
        -[:USED_IN]->(l :LINK)-[:USED_IN]
        ->(to :CLASS {{name:"Course", uri: '{course_uri}'}})
        MATCH (l)-[:HAS_PROPERTY]->(p :PROPERTY)
        RETURN p.name AS prop_name ORDER BY prop_name
        '''
    assert db.query(q, single_column="prop_name") == ["Frequency", "Usefulness"]



def test_class_relationship_exists(db):
    db.empty_dbase()
    GraphSchema.create_class("A")
    GraphSchema.create_class("B")

    with pytest.raises(Exception):
        GraphSchema.class_relationship_exists(from_class="", to_class="B", rel_name="whatever name")

    with pytest.raises(Exception):
        GraphSchema.class_relationship_exists(from_class="A", to_class="", rel_name="whatever name")

    with pytest.raises(Exception):
        GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="")

    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="owns")

    GraphSchema.create_class_relationship(from_class="A", to_class="B", rel_name="owns")

    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="owns")

    assert not GraphSchema.class_relationship_exists(from_class="B", to_class="A", rel_name="owns")   # Reverse direction

    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="sells")  # Different link

    GraphSchema.create_class("SA")
    GraphSchema.create_class_relationship(from_class="A", to_class="SA", rel_name="INSTANCE_OF")
    GraphSchema.create_class_relationship(from_class="SA", to_class="B", rel_name="sells")

    # A "sells" relationship now exists (indirectly) from "A" to "B" because "A" was made an instance of "SA"
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="sells")

    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="builds")

    GraphSchema.create_class("SSA")
    GraphSchema.create_class_relationship(from_class="SA", to_class="SSA", rel_name="INSTANCE_OF")
    GraphSchema.create_class_relationship(from_class="SSA", to_class="B", rel_name="builds")

    # A "builds" relationship now exists (indirectly) from "A" to "B" because we can go thru "SSA"
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="builds")


    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="does business with")

    GraphSchema.create_class("SB")
    GraphSchema.create_class_relationship(from_class="B", to_class="SB", rel_name="INSTANCE_OF")
    GraphSchema.create_class_relationship(from_class="SSA", to_class="SB", rel_name="does business with")

    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="does business with")


    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="loans out")
    GraphSchema.create_class_relationship(from_class="A", to_class="B", rel_name="loans out", use_link_node=True)
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="loans out")

    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="friends with")
    GraphSchema.create_class_relationship(from_class="SA", to_class="SB", rel_name="friends with", use_link_node=True)
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="friends with")



def test_delete_class_relationship(db):
    db.empty_dbase()
    _ , class_A_uri = GraphSchema.create_class("A")
    _ , class_B_uri = GraphSchema.create_class("B")

    with pytest.raises(Exception):
        GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name=None)
    with pytest.raises(Exception):
        GraphSchema.delete_class_relationship(from_class="", to_class="B", rel_name="some name")
    with pytest.raises(Exception):
        GraphSchema.delete_class_relationship(from_class="A", to_class=None, rel_name="some name")
    with pytest.raises(Exception):
        GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create a relationship, and then immediately delete it
    GraphSchema.create_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    n_del = GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert n_del == 1
    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    with pytest.raises(Exception):  # Attempting to re-delete it, will cause error
        GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create 2 different relationships between the same classes, then delete each relationship at a time
    GraphSchema.create_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    GraphSchema.create_class_relationship(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="BOGUS_RELATIONSHIP")

    n_del = GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert n_del == 1
    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")

    n_del = GraphSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert n_del == 1
    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert not GraphSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")



def test_unlink_classes(db):
    db.empty_dbase()
    person, _ = GraphSchema.create_class(name="Person")
    car, _ = GraphSchema.create_class(name="Car")

    # Create links in both directions between our 2 Classes
    GraphSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    GraphSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    q = "MATCH (:CLASS {name: 'Person'}) -[r]- (:CLASS {name: 'Car'}) RETURN count(r) AS n_rel"
    assert db.query(q, single_cell="n_rel") == 2

    assert GraphSchema.unlink_classes(class1="Person", class2="Car") == 2     # Use class names
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    GraphSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    GraphSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert GraphSchema.unlink_classes(class1="Person", class2=car) == 2       # Use class name and internal ID
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    GraphSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    GraphSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert GraphSchema.unlink_classes(class1=person, class2="Car") == 2       # Use internal ID and class name
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    GraphSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    GraphSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert GraphSchema.unlink_classes(class1=person, class2=car) == 2      # Use internal IDs
    assert db.query(q, single_cell="n_rel") == 0



def test_delete_class(db):
    db.empty_dbase()

    # Nonexistent classes
    with pytest.raises(Exception):
        GraphSchema.delete_class("I_dont_exist")

    with pytest.raises(Exception):
        GraphSchema.delete_class("I_dont_exist", safe_delete=False)


    # Classes with no properties and no relationships
    GraphSchema.create_class("French Vocabulary")
    GraphSchema.create_class("German Vocabulary")

    GraphSchema.delete_class("French Vocabulary", safe_delete=False)
    # French should be gone; but German still there
    assert not GraphSchema.class_name_exists("French Vocabulary")
    assert GraphSchema.class_name_exists("German Vocabulary")

    GraphSchema.delete_class("German Vocabulary")
    # Both classes gone
    assert not GraphSchema.class_name_exists("French Vocabulary")
    assert not GraphSchema.class_name_exists("German Vocabulary")

    with pytest.raises(Exception):
        GraphSchema.delete_class("German Vocabulary")     # Was already deleted


    # Interlinked Classes with properties, but no data nodes
    db.empty_dbase()
    create_sample_schema_1()    # Schema with patient/result/doctor
    GraphSchema.delete_class("doctor")
    assert GraphSchema.class_name_exists("patient")
    assert GraphSchema.class_name_exists("result")
    assert not GraphSchema.class_name_exists("doctor")
    # The Class "patient" is still linked to the Class "result"
    assert GraphSchema.get_linked_class_names(class_name="patient", rel_name="HAS_RESULT") == ["result"]

    GraphSchema.delete_class("patient")
    assert not GraphSchema.class_name_exists("patient")
    assert GraphSchema.class_name_exists("result")
    assert not GraphSchema.class_name_exists("doctor")

    GraphSchema.delete_class("result")
    assert not GraphSchema.class_name_exists("patient")
    assert not GraphSchema.class_name_exists("result")
    assert not GraphSchema.class_name_exists("doctor")


    # Interlinked Classes with properties; one of the Classes has an attached data node
    db.empty_dbase()
    create_sample_schema_2()    # Schema with quotes and categories
    GraphSchema.create_data_node(class_name="quotes",
                                 properties={"quote": "Comparison is the thief of joy"})

    GraphSchema.delete_class("Category")    # No problem in deleting this Class with no attached data nodes
    assert GraphSchema.class_name_exists("quotes")
    assert not GraphSchema.class_name_exists("Category")

    with pytest.raises(Exception):
        GraphSchema.delete_class("quotes")    # But cannot by default delete Classes with data nodes

    GraphSchema.delete_class("quotes", safe_delete=False)     # Over-ride default protection mechanism

    q = '''
    MATCH (d :quotes)
    WHERE d.`_CLASS` IS NOT NULL
    RETURN count(d) AS number_orphaned
    '''
    assert db.query(q, single_cell="number_orphaned") == 1  # Now there's an "orphaned" data node



def test_is_link_allowed(db):
    db.empty_dbase()

    GraphSchema.create_class("strict", strict=True)
    GraphSchema.create_class("lax1", strict=False)
    GraphSchema.create_class("lax2", strict=False)

    assert GraphSchema.is_link_allowed("belongs to", from_class="lax1", to_class="lax2")  # Anything goes, if both Classes are lax!

    with pytest.raises(Exception):   # Classes that doesn't exist
        GraphSchema.is_link_allowed("belongs to", from_class="nonexistent", to_class="lax2")

    with pytest.raises(Exception):
        assert not GraphSchema.is_link_allowed("belongs to", from_class="lax1", to_class="nonexistent")

    assert not GraphSchema.is_link_allowed("belongs to", from_class="lax1", to_class="strict")

    GraphSchema.create_class_relationship(from_class="lax1", to_class="strict",
                                          rel_name="belongs to")

    assert  GraphSchema.is_link_allowed("belongs to", from_class="lax1", to_class="strict")

    assert  not GraphSchema.is_link_allowed("works for", from_class="strict", to_class="lax2")

    GraphSchema.create_class_relationship(from_class="strict", to_class="lax2",
                                          rel_name="works for", use_link_node=True)

    assert  GraphSchema.is_link_allowed("works for", from_class="strict", to_class="lax2")


    # Now check situations involving "INSTANCE_OF" relationships
    GraphSchema.create_class("ancestor", strict=True)
    GraphSchema.create_class_relationship(from_class="ancestor", to_class="lax2",
                                          rel_name="supplied by")
    assert GraphSchema.is_link_allowed("supplied by", from_class="ancestor", to_class="lax2")
    assert not GraphSchema.is_link_allowed("supplied by", from_class="strict", to_class="lax2")
    GraphSchema.create_class_relationship(from_class="strict", to_class="ancestor",
                                          rel_name="INSTANCE_OF")
    assert GraphSchema.is_link_allowed("supplied by", from_class="strict", to_class="lax2")   # Now allowed thru 'ISTANCE_OF` ancestry



def test_is_strict_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.is_strict_class("I dont exist")

    GraphSchema.create_class("I am strict", strict=True)
    assert GraphSchema.is_strict_class("I am strict")

    GraphSchema.create_class("I am lax", strict=False)
    assert not GraphSchema.is_strict_class("I am lax")

    db.create_node(labels="CLASS", properties={"name": "Damaged_class"})
    assert not GraphSchema.is_strict_class("Damaged_class")   # Sloppily-create Class node lacking a "strict" attribute




def test_is_strict_class_fast(db):
    db.empty_dbase()

    internal_id , _ = GraphSchema.create_class("I am strict", strict=True)
    assert GraphSchema.is_strict_class_fast(internal_id)

    internal_id , _ = GraphSchema.create_class("I am lax", strict=False)
    assert not GraphSchema.is_strict_class_fast(internal_id)



def test_allows_data_nodes(db):
    db.empty_dbase()

    int_id_yes , _ = GraphSchema.create_class("French Vocabulary")
    assert GraphSchema.allows_data_nodes(class_name="French Vocabulary") == True
    assert GraphSchema.allows_data_nodes(class_internal_id=int_id_yes) == True

    int_id_no , _ = GraphSchema.create_class("Vocabulary", no_datanodes = True)
    assert GraphSchema.allows_data_nodes(class_name="Vocabulary") == False
    assert GraphSchema.allows_data_nodes(class_internal_id=int_id_no) == False




def test_get_class_instances(db):
    pass    # TODO



def test_get_related_class_names(db):
    pass    # TODO



def test_get_class_relationships(db):
    db.empty_dbase()

    assert GraphSchema.get_class_relationships(class_name="I_dont_exist") == {"in": [], "out": []}

    GraphSchema.create_class(name="Loner")
    assert GraphSchema.get_class_relationships(class_name="Loner") == {"in": [], "out": []}
    assert GraphSchema.get_class_relationships(class_name="Loner", link_dir="OUT") == []
    assert GraphSchema.get_class_relationships(class_name="Loner", link_dir="IN") == []

    create_sample_schema_1()    # Schema with patient/result/doctor

    result = GraphSchema.get_class_relationships(class_name="patient", link_dir="OUT")
    assert compare_unordered_lists(result, ["HAS_RESULT", "IS_ATTENDED_BY"])
    assert GraphSchema.get_class_relationships(class_name="patient", link_dir="IN") == []

    assert GraphSchema.get_class_relationships(class_name="doctor", link_dir="OUT") == []
    assert GraphSchema.get_class_relationships(class_name="doctor", link_dir="IN") == ["IS_ATTENDED_BY"]

    assert GraphSchema.get_class_relationships(class_name="result", link_dir="OUT") == []
    assert GraphSchema.get_class_relationships(class_name="result", link_dir="IN") == ["HAS_RESULT"]

    #TODO: test the omit_instance argument




#############   PROPERTIES-RELATED   #############


def test_get_class_properties(db):
    db.empty_dbase()

    GraphSchema.create_class_with_properties("My first class", properties=["A", "B", "C"])
    neo_uri = GraphSchema.get_class_internal_id("My first class")
    props = GraphSchema.get_class_properties(neo_uri)
    assert props == ["A", "B", "C"]
    props = GraphSchema.get_class_properties("My first class")
    assert props == ["A", "B", "C"]

    neo_uri, _ = GraphSchema.create_class("My BIG class")
    props = GraphSchema.get_class_properties(neo_uri)
    assert props == []
    props = GraphSchema.get_class_properties("My BIG class")
    assert props == []

    GraphSchema.add_properties_to_class(class_node=neo_uri, property_list = ["X", "Y"])
    props = GraphSchema.get_class_properties(neo_uri)
    assert props == ["X", "Y"]
    props = GraphSchema.get_class_properties(class_node="My BIG class")
    assert props == ["X", "Y"]

    GraphSchema.add_properties_to_class(class_node=neo_uri, property_list = ["Z"])
    props = GraphSchema.get_class_properties(neo_uri)
    assert props == ["X", "Y", "Z"]


    # Make "My first class" an instance of "My BIG class"
    GraphSchema.create_class_relationship(from_class="My first class", to_class="My BIG class", rel_name="INSTANCE_OF")

    props = GraphSchema.get_class_properties("My first class", include_ancestors=False)
    assert props == ["A", "B", "C"]

    props = GraphSchema.get_class_properties("My first class", include_ancestors=True)
    assert compare_unordered_lists(props, ["A", "B", "C", "X", "Y", "Z"])

    with pytest.raises(Exception):
        GraphSchema.get_class_properties("My first class", sort_by_path_len="meaningless")

    props = GraphSchema.get_class_properties("My first class", include_ancestors=True, sort_by_path_len="ASC")
    assert props == ["A", "B", "C", "X", "Y", "Z"]

    props = GraphSchema.get_class_properties("My first class", include_ancestors=True, sort_by_path_len="DESC")
    assert props == ["X", "Y", "Z", "A", "B", "C"]


    # Set Property "Y" to be a "system" one
    GraphSchema.set_property_attribute(class_name="My BIG class", prop_name="Y",
                                       attribute_name="system", attribute_value=True)

    props = GraphSchema.get_class_properties("My BIG class")
    assert props == ["X", "Y", "Z"]

    props = GraphSchema.get_class_properties("My BIG class", exclude_system=True)
    assert props == ["X", "Z"]

    props = GraphSchema.get_class_properties("My first class", include_ancestors=True,
                                             sort_by_path_len="ASC", exclude_system=True)
    assert props == ["A", "B", "C", "X", "Z"]

    props = GraphSchema.get_class_properties("My first class", include_ancestors=True,
                                             sort_by_path_len="DESC", exclude_system=True)
    assert props == ["X", "Z", "A", "B", "C"]



def test_add_properties_to_class(db):
    pass    # TODO



def test_new_class_with_properties(db):
    pass    # TODO



def test_remove_property_from_class(db):
    pass    # TODO



def test_is_property_allowed(db):
    db.empty_dbase()

    assert not GraphSchema.is_property_allowed(property_name="cost", class_name="I_dont_exist")

    GraphSchema.create_class_with_properties("My Lax class", ["A", "B"], strict=False)
    _, strict_uri = GraphSchema.create_class_with_properties("My Strict class", ["X", "Y"], strict=True)

    assert GraphSchema.is_property_allowed(property_name="A", class_name="My Lax class")
    assert GraphSchema.is_property_allowed(property_name="B", class_name="My Lax class")
    assert GraphSchema.is_property_allowed(property_name="anything goes in a nonstrict class", class_name="My Lax class")

    assert GraphSchema.is_property_allowed(property_name="X", class_name="My Strict class")
    assert GraphSchema.is_property_allowed(property_name="Y", class_name="My Strict class")
    assert not GraphSchema.is_property_allowed(property_name="some other field", class_name="My Strict class")

    GraphSchema.add_properties_to_class(class_uri=strict_uri, property_list=["some other field"])   # Now it will be declared!

    assert GraphSchema.is_property_allowed(property_name="some other field", class_name="My Strict class")


    _ , german_uri = GraphSchema.create_class_with_properties("German Vocabulary", ["German"], strict=True)
    assert GraphSchema.is_property_allowed(property_name="German", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")

    # "notes" and "English" are Properties of the more general "Foreign Vocabulary" Class,
    # of which "German Vocabulary" is an instance
    _ , foreign_uri = GraphSchema.create_class_with_properties("Foreign Vocabulary", ["English", "notes"], strict=True)
    GraphSchema.create_class_relationship(from_class="German Vocabulary", to_class="Foreign Vocabulary", rel_name="INSTANCE_OF")

    assert GraphSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert GraphSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")

    _ , content_uri = GraphSchema.create_class_with_properties("Content Item", ["uri"], strict=True)
    GraphSchema.create_class_relationship(from_class="Foreign Vocabulary", to_class="Content Item", rel_name="INSTANCE_OF")

    assert GraphSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")   # "uri" is now available thru ancestry
    assert GraphSchema.is_property_allowed(property_name="uri", class_name="Foreign Vocabulary")

    assert not GraphSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    # Properties "New_1", "New_2", "New_3" will be added, respectively,
    # to the Classes "German Vocabulary", "Foreign Vocabulary" and "Content Item"
    GraphSchema.add_properties_to_class(class_uri=german_uri, property_list=["New_1"])
    assert GraphSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    GraphSchema.add_properties_to_class(class_uri=foreign_uri, property_list=["New_2"])
    assert GraphSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert GraphSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not GraphSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    GraphSchema.add_properties_to_class(class_uri=content_uri, property_list=["New_3"])
    assert GraphSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert GraphSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert GraphSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    assert not GraphSchema.is_property_allowed(property_name="New_1", class_name="Foreign Vocabulary")    # "New_1" was added to "German Vocabulary"
    assert GraphSchema.is_property_allowed(property_name="New_2", class_name="Foreign Vocabulary")
    assert GraphSchema.is_property_allowed(property_name="New_3", class_name="Foreign Vocabulary")

    assert not GraphSchema.is_property_allowed(property_name="New_1", class_name="Content Item")
    assert not GraphSchema.is_property_allowed(property_name="New_2", class_name="Content Item")      # New_2" was added to "Foreign Vocabulary"
    assert GraphSchema.is_property_allowed(property_name="New_3", class_name="Content Item")



def test_allowable_props(db):
    db.empty_dbase()

    lax_int_uri, lax_schema_uri = GraphSchema.create_class_with_properties("My Lax class", ["A", "B"], strict=False)
    strict_int_uri, strict_schema_uri = GraphSchema.create_class_with_properties("My Strict class", ["A", "B"], strict=True)


    d = GraphSchema.allowable_props(class_internal_id=lax_int_uri,
                                    requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped

    d = GraphSchema.allowable_props(class_internal_id=strict_int_uri,
                                    requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped


    d = GraphSchema.allowable_props(class_internal_id=lax_int_uri,
                                    requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = GraphSchema.allowable_props(class_internal_id=strict_int_uri,
                                    requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123}  # "C" got silently dropped

    with pytest.raises(Exception):
        GraphSchema.allowable_props(class_internal_id=strict_int_uri,
                                    requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=False)


    d = GraphSchema.allowable_props(class_internal_id=lax_int_uri,
                                    requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"X": 666, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = GraphSchema.allowable_props(class_internal_id=strict_int_uri,
                                    requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {}      # Everything got silently dropped

    with pytest.raises(Exception):
        GraphSchema.allowable_props(class_internal_id=strict_int_uri,
                                    requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=False)





#############   SCHEMA-CODE  RELATED   ###########

def test_get_schema_code(db):
    pass    # TODO



def test_get_schema_uri(db):
    db.empty_dbase()
    _ , schema_uri_i = GraphSchema.create_class("My_class", code="i")
    _ , schema_uri_n = GraphSchema.create_class("My_other_class", code="n")

    assert GraphSchema.get_schema_uri(schema_code="i") == schema_uri_i
    assert GraphSchema.get_schema_uri(schema_code="n") == schema_uri_n
    assert GraphSchema.get_schema_uri(schema_code="x") == ""



################   DATA NODES : READING   ##############

def test__assemble_cypher_clauses():
    result = GraphSchema._assemble_cypher_clauses(node_id=123, id_key=None, class_name=None)
    assert result == ( "WHERE (id(dn) = $node_id)" , {"node_id": 123} )

    result = GraphSchema._assemble_cypher_clauses(node_id=123, id_key=None, class_name="Car")
    assert result == ( "WHERE (id(dn) = $node_id) AND (dn.`_CLASS` = $class_name)" ,
                       {"node_id": 123, "class_name": "Car"} )

    result = GraphSchema._assemble_cypher_clauses(node_id="white", id_key="color", class_name="Car")
    assert result == ( "WHERE (dn.`color` = $node_id) AND (dn.`_CLASS` = $class_name)" ,
                        {"node_id": "white", "class_name": "Car"} )

    with pytest.raises(Exception):
        GraphSchema._assemble_cypher_clauses(node_id="white", id_key="color", class_name="")

    with pytest.raises(Exception):
        GraphSchema._assemble_cypher_clauses(node_id="white", id_key="color", class_name=None, method="caller_fn")



def test_get_data_node(db):
    db.empty_dbase()

    assert GraphSchema.get_single_data_node(node_id=1234) is None      # Database is empty


    # Create a 1st Car node
    GraphSchema.create_class(name="Car", strict=False)

    db_id = GraphSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white"})

    result = GraphSchema.get_single_data_node(node_id=db_id)
    assert result == {'color': 'white', 'make': 'Toyota'}

    result = GraphSchema.get_single_data_node(node_id=db_id, class_name="Car")     # Redundant use of class_name
    assert result == {'color': 'white', 'make': 'Toyota'}

    result = GraphSchema.get_single_data_node(node_id=db_id, class_name="Car", hide_schema=False)
    assert result == {'_CLASS': 'Car', 'color': 'white', 'make': 'Toyota'}

    result = GraphSchema.get_single_data_node(node_id="yellow", id_key="color", class_name="Car")
    assert result is None   # Not found


    # Create a 2nd Car node: another Toyota, but this time red
    GraphSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "red"})

    with pytest.raises(Exception):
        GraphSchema.get_single_data_node(node_id="Toyota", id_key="color") # Missing class_name

    result = GraphSchema.get_single_data_node(node_id="white", id_key="color", class_name="Car")   # Using "color" as primary key
    assert result == {'color': 'white', 'make': 'Toyota'}

    with pytest.raises(Exception):
        GraphSchema.get_single_data_node(node_id="Toyota", id_key="make", class_name="Car")   # Using "make" as primary key will fail uniqueness


    # Create a 3rd Car node, this time with a "uri" field
    GraphSchema.create_data_node(class_name="Car",
                                 properties={"make": "Honda", "color": "blue"}, new_uri="car-1")

    result = GraphSchema.get_single_data_node(node_id="car-1", id_key="uri", class_name="Car")
    assert result == {'color': 'blue', 'make': 'Honda', 'uri': 'car-1'}


    # Now try it on a generic database node that is NOT a Data Node
    db_id = db.create_node(labels="Truck", properties={"make": "BMW", "color": "black"})
    result = GraphSchema.get_single_data_node(class_name="Truck", node_id=db_id)
    assert result is None



def test_all_properties(db):
    pass    # TODO

def test_get_data_node_internal_id(db):
    pass    # TODO

def test_get_data_node_id(db):
    pass    # TODO



def test_data_node_exists(db):
    db.empty_dbase()

    assert not GraphSchema.data_node_exists(node_id=123)
    assert not GraphSchema.data_node_exists(node_id="c-88", id_key="uri", class_name="Car")
    assert not GraphSchema.data_node_exists(node_id=45, id_key="employee id", class_name="Employee")

    GraphSchema.create_class(name="Car", strict = True)
    internal_id = GraphSchema.create_data_node(class_name="Car", new_uri="c-88")
    assert GraphSchema.data_node_exists(node_id=internal_id)
    assert GraphSchema.data_node_exists(node_id=internal_id, class_name="Car")
    assert not GraphSchema.data_node_exists(node_id=internal_id, class_name="BOAT")
    assert GraphSchema.data_node_exists(node_id="c-88", id_key="uri", class_name="Car")
    assert not GraphSchema.data_node_exists(node_id="c-88", id_key="uri", class_name="BOAT")

    GraphSchema.create_class_with_properties(name="Employee", properties=["employee id", "remarks"], strict=True)
    GraphSchema.create_data_node(class_name="Employee", properties={"employee id": 45})
    assert GraphSchema.data_node_exists(node_id=45, id_key="employee id", class_name="Employee")
    assert not GraphSchema.data_node_exists(node_id=666, id_key="employee id", class_name="Employee")   # Non-existent

    with pytest.raises(Exception):
        GraphSchema.data_node_exists(node_id=45, id_key="employee id")    # Missing `class_name`

    GraphSchema.create_data_node(class_name="Employee", properties={"employee id": 45, "remarks": "duplicate"})

    with pytest.raises(Exception):
        GraphSchema.data_node_exists(node_id=45, id_key="employee id", class_name="Employee")   # Bad primary key



def test_data_node_exists_EXPERIMENTAL(db):
    db.empty_dbase()

    assert not GraphSchema.data_node_exists_EXPERIMENTAL(search=123)
    assert not GraphSchema.data_node_exists_EXPERIMENTAL(search={"class_name": "Car", "key_value": "c-88"})
    assert not GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": "employee id", "key_value": 45})

    with pytest.raises(Exception):
        GraphSchema.data_node_exists_EXPERIMENTAL(search={"class_name": "", "key_value": "c-88"})     # Bad Class bane

    with pytest.raises(Exception):
        assert not GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": [1, 2], "key_value": 45})  # Bad value for "key_name"

    GraphSchema.create_class(name="Car", strict = True)
    internal_id = GraphSchema.create_data_node(class_name="Car", new_uri="c-88")
    assert GraphSchema.data_node_exists_EXPERIMENTAL(search=internal_id)
    assert GraphSchema.data_node_exists_EXPERIMENTAL(search={"class_name": "Car", "key_value": "c-88"})
    assert not GraphSchema.data_node_exists_EXPERIMENTAL(search={"class_name": "BOAT", "key_value": "c-88"})

    GraphSchema.create_class_with_properties(name="Employee", properties=["employee id", "remarks"], strict=True)
    GraphSchema.create_data_node(class_name="Employee", properties={"employee id": 45})
    assert GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": "employee id", "key_value": 45})
    assert not GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": "employee id", "key_value": 666})   # Non-existent node


    GraphSchema.create_data_node(class_name="Employee", properties={"employee id": 45, "remarks": "duplicate"})

    # A non-unique search
    assert GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": "employee id", "key_value": 45}, require_unique=False)
    with pytest.raises(Exception):
        GraphSchema.data_node_exists_EXPERIMENTAL(
            search={"class_name": "Employee", "key_name": "employee id", "key_value": 45}, require_unique=True)   # Bad primary key



def test_data_link_exists(db):
    pass    # TODO

def test_get_data_link_properties(db):
    pass    # TODO



def test_get_nodes_by_filter(db):
    db.empty_dbase()

    assert GraphSchema.get_nodes_by_filter() == []

    # Create a GENERIC node (not a Data Node)
    internal_id = db.create_node(labels="Car", properties={"color": "yellow", "year": 1999})

    assert GraphSchema.get_nodes_by_filter() == [{"color": "yellow", "year": 1999}]

    assert GraphSchema.get_nodes_by_filter(include_id=True) == [{"color": "yellow", "year": 1999, "internal_id": internal_id}]

    assert GraphSchema.get_nodes_by_filter(include_labels=True) == [{"color": "yellow", "year": 1999, "node_labels": ["Car"]}]

    assert GraphSchema.get_nodes_by_filter(labels="Car") == [{"color": "yellow", "year": 1999}]

    assert GraphSchema.get_nodes_by_filter(labels="Car", key_names="") == [{"color": "yellow", "year": 1999}]

    with pytest.raises(Exception):
        GraphSchema.get_nodes_by_filter(labels="Car", key_names="some_key_name")   # Key name but no value

    with pytest.raises(Exception):
        GraphSchema.get_nodes_by_filter(labels="Car", key_value="yellow")         # Key value but no key name

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="yellow")
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="YELLOW")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="YELLOW", case_sensitive=False)
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="ello")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="ello", string_match="CONTAINS")
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names=["color", "year"], key_value="yellow")
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names=["year", "color"], key_value="yEllOW", case_sensitive=False)
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names=[], key_value="")
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="year", key_value=1999)
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="year", key_value=1999, case_sensitive=False)
    assert result == [{"color": "yellow", "year": 1999}]    # case_sensitive is ignored, because value isn't text

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="year", key_value="1999")
    assert result == []         # No match because we searched for the string "1999" rather than the number 1999

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="year", key_value="1999", case_sensitive=False)
    assert result == []         # No match because we searched for the string "1999" rather than the number 1999

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="lavender")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(labels="Plane", key_names="color", key_value="yellow")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(class_name="Car", key_names="color", key_value="yellow")
    assert result == []


    # Add a 2nd GENERIC node (not a Data Node)
    db.create_node(labels="Car", properties={"color": "black", "trim": "yellow", "year": 1999})

    assert GraphSchema.get_nodes_by_filter() == [{"color": "yellow", "year": 1999}, {"color": "black", "trim": "yellow", "year": 1999}]

    assert GraphSchema.get_nodes_by_filter(labels="Car") == [{"color": "yellow", "year": 1999}, {"color": "black", "trim": "yellow", "year": 1999}]

    assert GraphSchema.get_nodes_by_filter(labels="Car", key_names="") == [{"color": "yellow", "year": 1999}, {"color": "black", "trim": "yellow", "year": 1999}]

    assert GraphSchema.get_nodes_by_filter(labels="Car", key_names="year", key_value=1999) == \
           [{"color": "yellow", "year": 1999}, {"color": "black", "trim": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names="color", key_value="yellow")
    assert result == [{"color": "yellow", "year": 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", key_names=["color", "trim"], key_value="yellow")
    assert result == [{"color": "yellow", "year": 1999}, {"color": "black", "trim": "yellow", "year": 1999}]


    # Create a Schema
    GraphSchema.create_class_with_properties(name="Car", properties=["color", "year", "make"], strict=True)

    # Add a new Car node
    GraphSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "grey"})

    result = GraphSchema.get_nodes_by_filter(class_name="Elephant")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(class_name="Car")    # This locates 1 node
    assert result == [{'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = GraphSchema.get_nodes_by_filter(labels="Car")        # This locates 3 nodes
    expected = [{"_CLASS": "Car", "color": "grey", "make": "Toyota"},
                {"color": "yellow", "year": 1999},
                {"color": "black", "trim": "yellow", "year": 1999}
               ]
    assert compare_recordsets(result, expected)

    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="toyota")
    assert result == []     # Case-sensitive


    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="Toy")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="Toy", string_match="ENDS WITH")
    assert result == []

    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="yota", string_match="ENDS WITH")
    assert result == [{'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="Toy", string_match="STARTS WITH")
    assert result == [{'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="Toy", string_match="CONTAINS")
    assert result == [{'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    # Add a new Car node
    GraphSchema.create_data_node(class_name="Car", properties={"make": "Chevrolet", "color": "pink", "year": 1955})

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="year, color")
    assert result == [{'_CLASS': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'},
                      {'color': 'black', 'trim': 'yellow', 'year': 1999},
                      {'color': 'yellow', 'year': 1999},
                      {'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'}
                     ]          # The record with no date will be at the end, when sorting in ascending order

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="  year    DESC  , color  ")
    assert result == [{'_CLASS': 'Car', 'color': 'grey', 'make': 'Toyota'},
                      {'color': 'black', 'trim': 'yellow', 'year': 1999},
                      {'color': 'yellow', 'year': 1999},
                      {'_CLASS': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'}
                     ]          #  The record with no date will be at the end, when sorting in descending order


    # Add a new Car node
    GraphSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white", "year": 1988})

     # Add a new Car node
    GraphSchema.create_data_node(class_name="Car", properties={"make": "Chevrolet", "color": "green", "year": 1970})

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC, color DESC")
    assert result == [  {'make': 'Chevrolet', 'year': 1970,'_CLASS': 'Car', 'color': 'green' },
                        {'make': 'Chevrolet', 'year': 1955, '_CLASS': 'Car', 'color': 'pink'},
                        {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_CLASS': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999},
                        {'color': 'black', 'trim': 'yellow', 'year': 1999}]     # Records with no 'make' will appear last

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC", limit=4)
    assert result == [  {'make': 'Chevrolet', 'year': 1970,'_CLASS': 'Car', 'color': 'green' },
                        {'make': 'Chevrolet', 'year': 1955, '_CLASS': 'Car', 'color': 'pink'},
                        {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_CLASS': 'Car', 'color': 'white'}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC, color DESC", skip=2, limit=3)
    assert result == [  {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_CLASS': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999}]

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="   make   , year   DESC   ", skip=2, limit=1)
    assert result == [  {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'}]

    # Add a new Car node; notice the lower case in the "make"
    GraphSchema.create_data_node(class_name="Car", properties={"make": "fiat", "color": "blue", "year": 1970})

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="make, year,color")
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_CLASS': 'Car', 'color': 'pink'},
                        {'make': 'Chevrolet', 'year': 1970,'_CLASS': 'Car', 'color': 'green' },
                        {'make': 'Toyota', 'year': 1988, '_CLASS': 'Car', 'color': 'white'},
                        {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'},
                        {'make': 'fiat', 'year': 1970, '_CLASS': 'Car', 'color': 'blue'},
                        {'color': 'black', 'trim': 'yellow', 'year': 1999},
                        {'color': 'yellow', 'year': 1999}]   # "fiat" comes after "Toyota" due to capitalization

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="make, year,  color  ", sort_ignore_case=["make"])
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_CLASS': 'Car', 'color': 'pink'},
                        {'make': 'Chevrolet', 'year': 1970,'_CLASS': 'Car', 'color': 'green' },
                        {'make': 'fiat', 'year': 1970, '_CLASS': 'Car', 'color': 'blue'},
                        {'make': 'Toyota', 'year': 1988, '_CLASS': 'Car', 'color': 'white'},
                        {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'},
                        {'color': 'black', 'trim': 'yellow', 'year': 1999},
                        {'color': 'yellow', 'year': 1999}]  # The "fiat" is now alphabetized regardless of case


    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="year, make DESC, color DESC", sort_ignore_case=["make"])
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_CLASS': 'Car', 'color': 'pink'},
                        {'make': 'fiat', 'year': 1970, '_CLASS': 'Car', 'color': 'blue'},
                        {'make': 'Chevrolet', 'year': 1970,'_CLASS': 'Car', 'color': 'green' },
                        {'make': 'Toyota', 'year': 1988, '_CLASS': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999},
                        {'color': 'black', 'trim': 'yellow', 'year': 1999},
                        {'make': 'Toyota', '_CLASS': 'Car', 'color': 'grey'}]

    # Add a new Car node; notice the blank in the new field name
    db.create_node(labels="Car", properties={"year": 2003, "decommission year": 2025})      # A GENERIC node (not a Data Node)

    result = GraphSchema.get_nodes_by_filter(labels="Car", order_by="decommission year, make, year", sort_ignore_case=["make"], limit=2)
    assert result == [{'decommission year': 2025, 'year': 2003},
                      {'_CLASS': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'}]

    with pytest.raises(Exception):
        # Trying to sort by a property (field) name unregistered with the Schema
        GraphSchema.get_nodes_by_filter(class_name="Car", key_names="color", key_value="yellow",
                                        order_by="SOME_UNKNOWN_FIELD")


    # Add a new Car node, using a date as a field value
    db.create_node(labels="Car", properties={"color": "red", "make": "Honda",
                                             "bought_on": neo4j.time.Date(2019, 6, 1),
                                             "certified": neo4j.time.DateTime(2019, 1, 31, 18, 59, 35)
                                             })
    result = GraphSchema.get_nodes_by_filter(key_names="make", key_value="Honda")  # Retrieve that latest node
    assert result == [{'color': 'red', 'make': 'Honda',
                       'bought_on': '2019/06/01', 'certified': '2019/01/31'}]



def test__process_key_name_value():
    with pytest.raises(Exception):
        GraphSchema._process_key_name_value(key_name=123, key_value=22)   # key_name is not a string

    result = GraphSchema._process_key_name_value(key_name="age", key_value=22)
    assert result == "(n.`age` = $key_value)"

    result = GraphSchema._process_key_name_value(key_name="age", key_value=22, string_match="CONTAINS")
    assert result == "(n.`age` = $key_value)"   # The "CONTAINS" is ignored because the value isn't a string

    result = GraphSchema._process_key_name_value(key_name="age", key_value=22, case_sensitive=False)
    assert result == "(n.`age` = $key_value)"   # The `case_sensitive` arg is ignored because the value isn't a string

    result = GraphSchema._process_key_name_value(key_name="city", key_value="New York")
    assert result == "(n.`city` = $key_value)"

    result = GraphSchema._process_key_name_value(key_name="city", key_value="New York", case_sensitive=False)
    expected = '''
            (
                CASE 
                    WHEN n.`city` = toString(n.`city`) 
                    THEN toLower(n.`city`) 
                    ELSE n.`city` 
                END
                = toLower($key_value)
            )
            '''
    assert result == expected

    result = GraphSchema._process_key_name_value(key_name="city", key_value="New York", string_match="CONTAINS")
    assert result == "(n.`city` CONTAINS $key_value)"

    result = GraphSchema._process_key_name_value(key_name="city", key_value="New York", string_match="ENDS WITH", case_sensitive=False)
    expected = '''
            (
                CASE 
                    WHEN n.`city` = toString(n.`city`) 
                    THEN toLower(n.`city`) 
                    ELSE n.`city` 
                END
                ENDS WITH toLower($key_value)
            )
            '''
    assert result == expected



def test__process_order_by():
    s = "John DESC, Alice, Bob desc, Carol"
    result = GraphSchema._process_order_by(s)
    assert result == "n.`John` DESC, n.`Alice`, n.`Bob` DESC, n.`Carol`"

    s = "make, built year, make, decommission year DESC"
    result = GraphSchema._process_order_by(s)
    assert result == "n.`make`, n.`built year`, n.`make`, n.`decommission year` DESC"

    s = "  A B    C desc  ,   D desc,E,F G  "
    result = GraphSchema._process_order_by(s, dummy_node_name="node")
    assert result == "node.`A B    C` DESC, node.`D` DESC, node.`E`, node.`F G`"

    s="Alice DESC,Bob,   Carol   DESC   ,Disc Number    "
    result = GraphSchema._process_order_by(s, ignore_case = ["Carol"])
    assert result == "n.`Alice` DESC, n.`Bob`, toLower(n.`Carol`) DESC, n.`Disc Number`"



def test_locate_node(db):
    pass    # TODO



def test_get_all_data_nodes_of_class(db):
    db.empty_dbase()

    result= GraphSchema.get_all_data_nodes_of_class("Car")
    assert result == []

    GraphSchema.create_class(name="Car")
    
    result= GraphSchema.get_all_data_nodes_of_class("Car")
    assert result == []

    # Add a generic database node that is NOT a Data Node (with same label)
    db.create_node(labels="Car", properties={"make": "BMW", "color": "red"})
    result = GraphSchema.get_all_data_nodes_of_class(class_name="Car")
    assert result == []

    # Create a data node without uri field
    db_id_car1 = GraphSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white"})

    result= GraphSchema.get_all_data_nodes_of_class(class_name="Car")
    assert result == [{'color': 'white', 'make': 'Toyota', 'internal_id': db_id_car1, 'node_labels': ['Car']}]

    result= GraphSchema.get_all_data_nodes_of_class(class_name="Car", hide_schema=False)
    assert result == [{'_CLASS': 'Car', 'color': 'white', 'make': 'Toyota', 'internal_id': db_id_car1, 'node_labels': ['Car']}]


    result= GraphSchema.get_all_data_nodes_of_class(class_name="Boat")
    assert result == []

    # Create a data node without uri field
    GraphSchema.create_class(name="Boat")
    db_id_boat1 = GraphSchema.create_data_node(class_name="Boat", properties={"make": "C&C", "type": "sloop"})

    result= GraphSchema.get_all_data_nodes_of_class(class_name="Boat")
    assert result == [{'make': 'C&C', 'type': 'sloop', 'internal_id': db_id_boat1, 'node_labels': ['Boat']}]

    # Create a data node with uri field
    db_id_car2 = GraphSchema.create_data_node(class_name="Car", properties={"make": "Fiat", "color": "blue"}, new_uri="cincilla")

    result= GraphSchema.get_all_data_nodes_of_class(class_name="Car")

    expected = [{'make': 'Toyota', 'color': 'white', 'internal_id': db_id_car1, 'node_labels': ['Car']},
                {'make': 'Fiat', 'color': 'blue', 'internal_id': db_id_car2, 'node_labels': ['Car'], 'uri': 'cincilla'}
               ]

    assert compare_recordsets(result, expected)



def test_class_of_data_node(db):
    pass    # TODO

def test_data_nodes_of_class(db):
    pass    # TODO



def test_count_data_nodes_of_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.count_data_nodes_of_class("unknown")   # Non-existent Class

    GraphSchema.create_class("Some class")

    assert GraphSchema.count_data_nodes_of_class("Some class") == 0

    GraphSchema.create_data_node(class_name="Some class")
    assert GraphSchema.count_data_nodes_of_class("Some class") == 1

    GraphSchema.create_data_node(class_name="Some class")
    assert GraphSchema.count_data_nodes_of_class("Some class") == 2


    GraphSchema.create_class("Another class")

    assert GraphSchema.count_data_nodes_of_class("Another class") == 0

    GraphSchema.create_data_node(class_name="Another class")
    assert GraphSchema.count_data_nodes_of_class("Another class") == 1

    assert GraphSchema.count_data_nodes_of_class("Some class") == 2   # Where we left it off



def test_data_points_lacking_schema(db):
    pass    # TODO

def test_get_data_point_uri(db):
    pass    # TODO

def test_follow_links(db):
    pass    # TODO





###############   DATA NODES : CREATING / MODIFYING   ##############

def test_create_data_node_1(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="nonexistent",
                                     properties={"name": "who cares?"})

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="doctor", properties="NOT a dict")


    # Create a 1st "doctor" data node
    internal_id = GraphSchema.create_data_node(class_name="doctor",
                                               properties={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                               extra_labels = None,
                                               new_uri=None, silently_drop=False)

    q = '''
        MATCH (dn :doctor {name: "Dr. Preeti", specialty: "sports medicine", `_CLASS`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'dn': {'specialty': 'sports medicine', 'name': 'Dr. Preeti', '_CLASS': "doctor"}}


    # Create a 2nd "doctor" data node, this time assigning an extra label and storing a URI
    uri = "doc-1"
    internal_id = GraphSchema.create_data_node(class_name="doctor",
                                               properties={"name": "Dr. Watson", "specialty": "genetics"},
                                               extra_labels = "Nobelist",
                                               new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:Nobelist {name: "Dr. Watson", specialty: "genetics", `_CLASS`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'dn': {'specialty': 'genetics', 'name': 'Dr. Watson', 'uri': uri, '_CLASS': "doctor"}}


    # Create a 3rd "doctor" data node, this time assigning 2 extra labels and also assigning a URI
    uri = "d-123"
    internal_id = GraphSchema.create_data_node(class_name="doctor",
                                               properties={"name": "Dr. Lewis", "specialty": "radiology"},
                                               extra_labels = ["retired", "person"],
                                               new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:retired:person {name: "Dr. Lewis", specialty: "radiology", `_CLASS`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'dn': {'specialty': 'radiology', 'name': 'Dr. Lewis', 'uri': uri, '_CLASS': "doctor"}}


    # Create a 4th "doctor" data node, this time using a tuple rather than a list to assign 2 extra labels
    uri = "d-999"
    internal_id = GraphSchema.create_data_node(class_name="doctor",
                                               properties={"name": "Dr. Clark", "specialty": "pediatrics"},
                                               extra_labels = ("retired", "person"),
                                               new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:retired:person {name: "Dr. Clark", specialty: "pediatrics", `_CLASS`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'dn': {'specialty': 'pediatrics', 'name': 'Dr. Clark', 'uri': uri, '_CLASS': "doctor"}}



def test_create_data_node_2(db):
    db.empty_dbase()

    # Using a class of type "strict"
    GraphSchema.create_class_with_properties(name="person",
                                             properties=["name", "age"], strict=True)


    # Create a "person" data node, attempting to set a property not declared in the Schema; this will fail
    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="person",
                                     properties={"name": "Joe", "address": "extraneous undeclared field"},
                                     extra_labels = None, new_uri=None,
                                     silently_drop=False)

    # To prevent a failure, we can ask to silently drop any undeclared property
    internal_id = GraphSchema.create_data_node(class_name="person",
                                               properties={"age": 22, "address": "extraneous undeclared field"},
                                               extra_labels = None, new_uri=None,
                                               silently_drop=True)
    q = '''
        MATCH (p :person {age: 22, `_CLASS`: "person"}) 
        WHERE id(p) = $internal_id
        RETURN p
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'p': {'age': 22, '_CLASS': "person"}}      # Notice that the address never made it into the database


    # Switch a new class, of type "lenient"
    GraphSchema.create_class_with_properties(name="car",
                                             properties=["brand"], strict=False)

    # Because the class is "lenient", data nodes may be created with undeclared properties
    internal_id = GraphSchema.create_data_node(class_name="car",
                                               properties={"brand": "Toyota", "color": "white"},
                                               extra_labels = None, new_uri=None,
                                               silently_drop=False)
    q = '''
        MATCH (c :car {brand: "Toyota", color: "white", `_CLASS`: "car"}) 
        WHERE id(c) = $internal_id
        RETURN c
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'c': {"brand": "Toyota", "color": "white", '_CLASS': "car"}}  # The color, though undeclared in the Schema, got set



def test_create_data_node_3(db):
    db.empty_dbase()

    GraphSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="No data nodes allowed")   # The Class doesn't allow data nodes


    class_internal_id , class_schema_uri = GraphSchema.create_class("Car", strict=True)

    assert GraphSchema.count_data_nodes_of_class("Car") == 0

    # Successfully adding the first data node
    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car")
    assert GraphSchema.count_data_nodes_of_class("Car") == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]   # No other properties were set


    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="Car",
                                     properties={"color": "No properties allowed"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 2nd data node
    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car",
                                                            properties={"color": "No properties allowed"},
                                                            silently_drop=True)

    assert GraphSchema.count_data_nodes_of_class("Car") == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]   # No other properties were set


    # Successfully adding a 3rd data point
    GraphSchema.add_properties_to_class(class_node=class_internal_id, property_list=["color"]) # Expand the allow class properties

    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car",
                                                            properties={"color": "white"})

    assert GraphSchema.count_data_nodes_of_class("Car") == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], 'color': 'white', '_CLASS': "Car"}]]   # This time the properties got set


    # Again expand the allowed class properties
    GraphSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="Car",
                                     properties={"color": "white", "make": "Toyota"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 4th data point
    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car",
                                                            properties={"color": "red", "make": "VW"},
                                                            silently_drop=True)

    assert GraphSchema.count_data_nodes_of_class("Car") == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], 'color': 'red', '_CLASS': "Car"}]]   # The "color" got set, while the "make" got dropped


    # Successfully adding a 5th data point
    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car",
                                                            properties={"color": "blue", "make": "Fiat", "year": 2000},
                                                            silently_drop=True)

    assert GraphSchema.count_data_nodes_of_class("Car") == 5

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], 'color': 'blue', 'year': 2000, '_CLASS': "Car"}]]
    # The "color" and "year" got set, while the "make" got dropped


    # Successfully adding a 6th data point
    new_datanode_internal_id = GraphSchema.create_data_node(class_name="Car",
                                                            properties={"color": "green", "year": 2022},
                                                            silently_drop=False)

    assert GraphSchema.count_data_nodes_of_class("Car") == 6

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'node_labels': ['Car'], 'color': 'green', 'year': 2022, '_CLASS': "Car"}]]
    # All properties got set



def test_create_data_node_4(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

     # Create a new data point, and get its Neo4j ID
    doctor_internal_id = GraphSchema.create_data_node(class_name="doctor",
                                                      properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Jill", "age": 22, "balance": 145.50},
                                     links={}
                                     )   # links must be a list


    # Create a new data node for a "patient", linked to the existing "doctor" data point (OUT-bound relationship)
    patient_internal_id = GraphSchema.create_data_node(class_name="patient",
                                                       properties={"name": "Jill", "age": 22, "balance": 145},
                                                       links=[{"internal_id": doctor_internal_id, "rel_name": "IS_ATTENDED_BY", "rel_dir": "OUT"}]
                                                       )

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145, `_CLASS`:"patient"})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine", `_CLASS`:"doctor"})
        WHERE id(d) = $doctor_internal_id AND id(p) = $patient_internal_id
        RETURN p, d
        '''
    result = db.query(q, data_binding={"doctor_internal_id": doctor_internal_id, "patient_internal_id": patient_internal_id})
    assert len(result) == 1


    # Create a new data node for a "result", linked to the existing "patient" data node;
    #   this time, also assign a "uri" to the new data node, and it's an IN-bound relationship
    result_internal_id = GraphSchema.create_data_node(class_name="result",
                                                      properties={"biomarker": "glucose", "value": 99},
                                                      links=[{"internal_id": patient_internal_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                      new_uri= "RESULT-1")
    q = '''
        MATCH 
        (p :patient {name: "Jill", age: 22, balance: 145, `_CLASS`:"patient"})
        -[:HAS_RESULT]->
        (r :result {biomarker: "glucose", value: 99, `_CLASS`:"result"})
        WHERE id(p) = $patient_internal_id AND id(r) = $result_internal_id
        RETURN p, r
        '''
    result = db.query(q, data_binding={"patient_internal_id": patient_internal_id,
                                       "result_internal_id": result_internal_id
                                       })
    assert len(result) == 1
    record = result[0]
    assert record['r']['uri'] == "RESULT-1"


    # Create a 2nd data point for a "result", linked to the existing "patient" data point;
    #   agan with a specific "uri" assigned to the new data node
    result2_internal_id = GraphSchema.create_data_node(class_name="result",
                                                       properties={"biomarker": "cholesterol", "value": 180},
                                                       links=[{"internal_id": patient_internal_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                       new_uri="RESULT-2")
    q = '''
        MATCH 
        (r1 :result {biomarker: "glucose", value: 99, `_CLASS`:"result"})
        <-[:HAS_RESULT]-
        (p :patient {name: "Jill", age: 22, balance: 145, `_CLASS`:"patient"})
        -[:HAS_RESULT]->
        (r2 :result {biomarker: "cholesterol", value: 180, `_CLASS`:"result"})
        WHERE id(p) = $patient_internal_id AND id(r2) = $result_internal_id
        RETURN p, r1, r2
        '''
    result = db.query(q, data_binding={"patient_internal_id": patient_internal_id,
                                       "result_internal_id": result2_internal_id
                                       })
    assert len(result) == 1
    record = result[0]
    assert record['r1']['uri'] == "RESULT-1"    # From earlier
    assert record['r2']['uri'] == "RESULT-2"    # The specific "uri" that was passed


    # Create another "patient" node, linked to the existing "doctor" data node, this time with some extra properties
    patient_internal_id_2 = GraphSchema.create_data_node(class_name="patient",
                                                         properties={"name": "Jack", "age": 99, "balance": 8000},
                                                         links=[{"internal_id": doctor_internal_id,
                                                     "rel_name": "IS_ATTENDED_BY",
                                                     "rel_dir": "OUT",
                                                     "rel_attrs": {"since": 1999}
                                                    }]
                                                         )

    q = '''
        MATCH (p :patient {name: "Jack", age: 99, balance: 8000, `_CLASS`:"patient"})
        -[r :IS_ATTENDED_BY]-> 
        (d :doctor {name:"Dr. Preeti", specialty:"sports medicine", `_CLASS`:"doctor"})
        WHERE id(d) = $doctor_internal_id AND id(p) = $patient_internal_id
            AND r.since = 1999
        RETURN p, d
        '''
    result = db.query(q, data_binding={"doctor_internal_id": doctor_internal_id, "patient_internal_id": patient_internal_id_2})
    assert len(result) == 1


    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Spencer", "age": 55, "balance": 1200},
                                     links=[{"internal_id": -1,             # No such node exists
                                                     "rel_name": "IS_ATTENDED_BY"
                                                    }]
                                     )

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Spencer", "age": 55, "balance": 1200},
                                     links=666  # Not a list
                                     )

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Spencer", "age": 55, "balance": 1200},
                                     links=[{}]  # Missing required keys
                                     )

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Spencer", "age": 55, "balance": 1200},
                                     links=[{"internal_id": doctor_internal_id}]  # Missing required keys
                                     )

    with pytest.raises(Exception):
        GraphSchema.create_data_node(class_name="patient",
                                     properties={"name": "Spencer", "age": 55, "balance": 1200},
                                     links=[{"internal_id": doctor_internal_id,
                                                     "rel_name": "IS_ATTENDED_BY",
                                                     "unexpected_key": 666}]  # Unexpected key
                                     )

    assert GraphSchema.count_data_nodes_of_class("patient") == 2      # The 3rd patient node didn't get created by any of the failed calls

    # See if the 3rd patient node was perchance created
    q = f'''
        MATCH (n) 
        WHERE n.name = "Spencer"
        RETURN n
    '''
    result = db.query(q)
    assert len(result) == 0         # The "Spencer" patient node is nowhere to be found



def test_update_data_node(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a "doctor" data node
    GraphSchema.create_namespace(name="doctor", prefix ="doc-")
    uri = GraphSchema.reserve_next_uri(namespace="doctor")
    internal_id = GraphSchema.create_data_node(class_name="doctor",
                                               properties={"name": "Dr. Watson", "specialty": "pediatrics"},
                                               new_uri=uri)

    # The doctor is changing specialty...
    count = GraphSchema.update_data_node(data_node=internal_id, set_dict={"specialty": "ob/gyn"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson", "specialty": "ob/gyn", "_CLASS": "doctor"}]


    # Completely drop the specialty field
    count = GraphSchema.update_data_node(data_node=internal_id, set_dict={"specialty": ""}, drop_blanks = True)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson", "_CLASS": "doctor"}]


    # Turn the name value blank, but don't drop the field
    count = GraphSchema.update_data_node(data_node=internal_id, set_dict={"name": ""}, drop_blanks = False)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "", "_CLASS": "doctor"}]


    # Set the name, this time locating the record by its URI
    count = GraphSchema.update_data_node(data_node=uri, set_dict={"name": "Prof. Fleming"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "_CLASS": "doctor"}]


    # Add 2 extra fields: notice the junk leading/trailing blanks in the string
    count = GraphSchema.update_data_node(data_node=uri, set_dict={"location": "     San Francisco     ", "retired": False})

    assert count == 2
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_CLASS": "doctor"}]


    # A vacuous "change" that doesn't actually do anything
    count = GraphSchema.update_data_node(data_node=uri, set_dict={})

    assert count == 0
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_CLASS": "doctor"}]


    # A "change" that doesn't actually change anything, but nonetheless is counted as 1 property set
    count = GraphSchema.update_data_node(data_node=uri, set_dict={"location": "San Francisco"})
    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_CLASS": "doctor"}]


    # A "change" that causes a field of blanks to get dropped
    count = GraphSchema.update_data_node(data_node=uri, set_dict={"name": "        "}, drop_blanks = True)
    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "location": "San Francisco", "retired": False, "_CLASS": "doctor"}]



def test_add_data_node_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.add_data_node_merge(class_name="I_dont_exist",
                                        properties={"junk": 123})     # No such class exists

    class_internal_id , _ = GraphSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        GraphSchema.add_data_node_merge(class_name="No data nodes allowed",
                                        properties={"junk": 123})   # The Class doesn't allow data nodes

    class_internal_id , class_schema_uri = GraphSchema.create_class("Car", strict=True)
    assert GraphSchema.count_data_nodes_of_class("Car") == 0

    with pytest.raises(Exception):
        GraphSchema.add_data_node_merge(class_name="Car", properties={})  # Properties are required

    with pytest.raises(Exception):
        # "color" is not a registered property of the Class "Car"
        GraphSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})

    GraphSchema.add_properties_to_class(class_node = class_internal_id, property_list = ["color"])


    # Successfully adding the first data point
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]


    with pytest.raises(Exception):
        GraphSchema.add_data_node_merge(class_name="Car",
                                        properties={"make": "A property not currently allowed"})   # Trying to set a non-allowed property


    # The merging will use the already-existing data point, since the properties match up
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == False    # No new node was created

    assert GraphSchema.count_data_nodes_of_class("Car") == 1     # STILL at 1 datapoint

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]   # Same as before


    # Successfully adding a new (2nd) data point
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car",
                                                              properties={"color": "red"})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]


    # Again expand the allowed class properties
    GraphSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        GraphSchema.add_data_node_merge(class_name="Car",
                                        properties={"color": "white", "make": "Toyota"})   # Trying to set a non-allowed property

    # Successfully adding a 3rd data point
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car",
                                                              properties={"color": "blue", "year": 2023})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2023, 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]


    # Successfully adding a 4th data point
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car",
                                                              properties={"color": "blue", "year": 2000})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}})  
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2000, 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]
    # We can have 2 red blue because they differ in the other attribute (i.e. the year)


    # Nothing gets added now, because a "blue, 2000" car already exists
    _ , status = GraphSchema.add_data_node_merge(class_name="Car",
                                                 properties={"color": "blue", "year": 2000})
    assert status == False    # No new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 4     # UNCHANGED


    # Likewise, nothing gets added now, because a "red" car already exists
    _ , status = GraphSchema.add_data_node_merge(class_name="Car",
                                                 properties={"color": "red"})
    assert status == False    # No new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 4     # UNCHANGED


    # By contrast, a new data node gets added now, because the "mileage" field will now be kept, and there's no "red car from 1999"
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car",
                                                              properties={"color": "red", "year": 1999})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 5     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}})  
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]


    # Attempting to re-add the "red, 1999" car will have no effect...
    _ , status = GraphSchema.add_data_node_merge(class_name="Car",
                                                 properties={"color": "red", "year": 1999})
    assert status == False    # No new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 5     # UNCHANGED


    GraphSchema.add_properties_to_class(class_node=class_internal_id, property_list=["make"])
    # ... but there's no car "red, 1999, Toyota"
    new_datanode_id, status = GraphSchema.add_data_node_merge(class_name="Car",
                                                              properties={"color": "red", "year": 1999, "make": "Toyota"})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 6     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_CLASS`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'make': 'Toyota', 'internal_id': new_datanode_id, 'node_labels': ['Car'], '_CLASS': "Car"}]]


    # Now, set up an irregular scenario where there's a database node that will match the attributes and labels
    # of a Data Node to add, but is not itself a Data Node (it lacks a SCHEMA relationship to its Class)
    # This node will be ignored by the Schema layer, because it's not managed by it - and we can add just fine
    # a Data Node for a "yellow car"
    db.create_node(labels="Car", properties={"color": "yellow"})
    _, status = GraphSchema.add_data_node_merge(class_name="Car", properties={"color": "yellow"})
    assert status == True    # A new node was created
    assert GraphSchema.count_data_nodes_of_class("Car") == 7     # Increased



def test_add_data_column_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        # No such class exists
        GraphSchema.add_data_column_merge(class_name="Car", property_name="color", value_list=["white"])

    GraphSchema.create_class_with_properties("Car", properties=["color", "year"],
                                             strict=True)
    assert GraphSchema.count_data_nodes_of_class("Car") == 0

    with pytest.raises(Exception):
        GraphSchema.add_data_column_merge(class_name="Car", property_name=123, value_list=["white"])      # property_name isn't a string

    with pytest.raises(Exception):
        GraphSchema.add_data_column_merge(class_name="Car", property_name="color", value_list="white")    # value_list isn't a list

    with pytest.raises(Exception):
        GraphSchema.add_data_column_merge(class_name="Car", property_name="color", value_list=[])    # value_list is empty


    # Expand the Schema
    result = GraphSchema.add_data_column_merge(class_name="Car",
                                               property_name="color", value_list=["red", "white", "blue"])

    with pytest.raises(Exception):
        GraphSchema.add_data_column_merge(class_name="Car",
                                          property_name="UNKNOWN", value_list=[1, 2])     # Property not in Schema Class

    # Successfully add 3 data points
    assert len(result["new_nodes"]) == 3
    assert len(result["old_nodes"]) == 0
    assert GraphSchema.count_data_nodes_of_class("Car") == 3


    # Only 1 of the following 3 data points isn't already in the database
    result = GraphSchema.add_data_column_merge(class_name="Car",
                                               property_name="color", value_list=["red", "green", "blue"])
    assert len(result["new_nodes"]) == 1
    assert len(result["old_nodes"]) == 2
    assert GraphSchema.count_data_nodes_of_class("Car") == 4

    id_green_car = result["new_nodes"][0]
    data_point = GraphSchema.get_single_data_node(node_id=id_green_car)
    assert data_point["color"] == "green"


    # Successfully add the 2 distinct data points, from the 3 below, using a different field
    result = GraphSchema.add_data_column_merge(class_name="Car",
                                               property_name="year", value_list=[2003, 2022, 2022])
    assert len(result["new_nodes"]) == 2
    assert len(result["old_nodes"]) == 1
    assert GraphSchema.count_data_nodes_of_class("Car") == 6



def test_register_existing_data_point(db):
    pass    # TODO



def test_delete_data_nodes(db):
    db.empty_dbase()

    result = GraphSchema.delete_data_nodes(node_id = 1)     # Non-existing node (database just got cleared)
    assert result == 0

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create new data nodes
    doctor_internal_id = GraphSchema.create_data_node(class_name="doctor",
                                                      properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    patient_internal_id = GraphSchema.create_data_node(class_name="patient",
                                                       properties={"name": "Val", "age": 22})

    GraphSchema.create_data_node(class_name="result", properties={"biomarker": "insulin ", "value": 10})
    GraphSchema.create_data_node(class_name="result", properties={"biomarker": "bilirubin ", "value": 1})

    doctor = GraphSchema.get_single_data_node(node_id=doctor_internal_id)
    assert doctor == {'name': 'Dr. Preeti', 'specialty': 'sports medicine'}

    patient = GraphSchema.get_single_data_node(node_id=patient_internal_id)
    assert patient == {'name': 'Val', 'age': 22}

    assert GraphSchema.count_data_nodes_of_class("result") == 2


    # Now delete some of the data nodes we created
    with pytest.raises(Exception):
        GraphSchema.delete_data_nodes(node_id = -1)    # Invalid node ID

    result = GraphSchema.delete_data_nodes(node_id=doctor_internal_id)
    assert result == 1
    doctor = GraphSchema.get_single_data_node(node_id=doctor_internal_id)
    assert doctor is None       # The doctor got deleted

    result = GraphSchema.delete_data_nodes(node_id='Liz', id_key='name')  # Non-existent node
    assert result == 0
    patient = GraphSchema.get_single_data_node(node_id=patient_internal_id)
    assert patient == {'name': 'Val', 'age': 22}        # Still there

    result = GraphSchema.delete_data_nodes(node_id='Val', id_key='name')  # Correct node
    assert result == 1
    patient = GraphSchema.get_single_data_node(node_id=patient_internal_id)
    assert patient is None      # The patient got deleted

    result = GraphSchema.delete_data_nodes(class_name="result", node_id='LDL', id_key='biomarker')
    assert result == 0          # No matches
    assert GraphSchema.count_data_nodes_of_class("result") == 2   # Still there

    result = GraphSchema.delete_data_nodes(class_name="result")
    assert result == 2          # Both results got deleted
    assert GraphSchema.count_data_nodes_of_class("result") == 0   # No results found



def test_add_data_relationship_hub(db):
    db.empty_dbase()

    # Set up the Schema
    GraphSchema.create_class_with_properties("City", properties=["name"])
    GraphSchema.create_class_with_properties("State", properties=["name"])

    # Set up the Data Nodes (2 cities and a state)
    berkeley = GraphSchema.create_data_node(class_name="City", properties = {"name": "Berkeley"})
    san_diego = GraphSchema.create_data_node(class_name="City", properties = {"name": "San Diego"})
    california = GraphSchema.create_data_node(class_name="State", properties = {"name": "California"})

    with pytest.raises(Exception):
        # Trying to create a data relationship not yet declared in the Schema
        GraphSchema.add_data_relationship_hub(center_id=california, periphery_ids=[berkeley, san_diego], periphery_class="City",
                                              rel_name="LOCATED_IN", rel_dir="IN")

    # Declare the "LOCATED_IN" relationship in the Schema
    GraphSchema.create_class_relationship(from_class="City", to_class="State", rel_name="LOCATED_IN")

    number_rels = GraphSchema.add_data_relationship_hub(center_id=california, periphery_ids=[berkeley, san_diego], periphery_class="City",
                                                        rel_name="LOCATED_IN", rel_dir="IN")
    assert number_rels == 2

    # Verify that the "hub" (with 2 cities "LOCATED_IN" the state) is present
    q = '''
        MATCH p=(:City {name: "San Diego"})-[:LOCATED_IN]->
                (:State {name: "California"})
                <-[:LOCATED_IN]-(:City {name: "Berkeley"})
        RETURN COUNT(p) AS number_paths
        '''
    assert db.query(q, single_cell="number_paths") == 1


    # Add more Data Nodes
    nevada = GraphSchema.create_data_node(class_name="State", properties = {"name": "Nevada"})
    oregon = GraphSchema.create_data_node(class_name="State", properties = {"name": "Oregon"})

    with pytest.raises(Exception):
        # Trying to create a data relationship not yet declared in the Schema
        GraphSchema.add_data_relationship_hub(center_id=california, periphery_ids=[nevada, oregon], periphery_class="State",
                                              rel_name="BORDERS_WITH", rel_dir="OUT")

    # Declare the "BORDERS_WITH" relationship in the Schema
    GraphSchema.create_class_relationship(from_class="State", to_class="State", rel_name="BORDERS_WITH")

    number_rels = GraphSchema.add_data_relationship_hub(center_id=california,
                                                        periphery_ids=[nevada, oregon], periphery_class="State",
                                                        rel_name="BORDERS_WITH", rel_dir="OUT")
    assert number_rels == 2

    # Verify that the "hub" with the 3 states is present
    q = '''
        MATCH p=(:State {name: "Nevada"})<-[:BORDERS_WITH]-
        (:State {name: "California"})
        -[:BORDERS_WITH]->(:State {name: "Oregon"})
        RETURN COUNT(p) AS number_paths
    '''
    assert db.query(q, single_cell="number_paths") == 1



def test_add_data_relationship(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        GraphSchema.add_data_relationship(from_id=123, to_id=456, rel_name="junk")  # No such nodes exist

    neo_uri_1 = db.create_node("random A")
    neo_uri_2 = db.create_node("random B")
    with pytest.raises(Exception):
        GraphSchema.add_data_relationship(from_id=neo_uri_1, to_id=neo_uri_2, rel_name="junk") # Not data nodes with a Schema

    _ , person_class_uri = GraphSchema.create_class("Person", strict=True)
    person_internal_id = GraphSchema.create_data_node(class_name="Person", new_uri="julian")

    _ , car_class_uri = GraphSchema.create_class("Car")
    car_internal_id = GraphSchema.create_data_node(class_name="Car", properties={"color": "white"})

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")

    # Add the "DRIVE" relationship between the Classes
    GraphSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="DRIVES")


    with pytest.raises(Exception):
        GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="")  # Lacks relationship name

    with pytest.raises(Exception):
        GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name=None)  # Lacks relationship name

    with pytest.raises(Exception):
        GraphSchema.add_data_relationship(from_id=car_internal_id, to_id=person_internal_id, rel_name="DRIVES")  # Wrong direction

    # Now, adding the data relationship will work
    GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")
    assert db.links_exist(match_from=person_internal_id, match_to=car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Attempting to add it again
        GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        GraphSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="SOME_OTHER_NAME")


    # Now add reverse a relationship between the Classes
    GraphSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_DRIVEN_BY")

    # Add that same reverse relationship between the data nodes
    GraphSchema.add_data_relationship(from_id=car_internal_id, to_id=person_internal_id, rel_name="IS_DRIVEN_BY")
    assert db.links_exist(match_from=car_internal_id, match_to=person_internal_id, rel_name="IS_DRIVEN_BY")

    # Now add a relationship using URI's instead of internal database ID's
    red_car_internal_id = GraphSchema.create_data_node(class_name="Car", properties={"color": "red"}, new_uri="new_car")
    GraphSchema.add_data_relationship(from_id="julian", to_id="new_car", id_type="uri", rel_name="DRIVES")
    assert db.links_exist(match_from=person_internal_id, match_to=red_car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        GraphSchema.add_data_relationship(from_id="julian", to_id="new_car", id_type="uri", rel_name="PAINTS")



def test_remove_data_relationship(db):
    pass    # TODO



def test_class_of_data_point(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        GraphSchema.class_of_data_node(node_id=123)  # No such data node exists

    internal_id = db.create_node("random")
    with pytest.raises(Exception):
        GraphSchema.class_of_data_node(node_id=internal_id)     # It's not a data node

    GraphSchema.create_class("Person")
    uri = GraphSchema.reserve_next_uri()      # Obtain (and reserve) the next auto-increment value
    GraphSchema.create_data_node(class_name="Person", new_uri=uri)

    assert GraphSchema.class_of_data_node(node_id=uri, id_key="uri") == "Person"
    assert GraphSchema.class_of_data_node(node_id=uri, id_key="uri", labels="Person") == "Person"

    # Now locate thru the internal database ID
    internal_id = GraphSchema.get_data_node_id(uri)
    #print("neo_uri: ", neo_uri)
    assert GraphSchema.class_of_data_node(node_id=internal_id) == "Person"

    GraphSchema.create_class("Extra")
    # Create a forbidden scenario with a data node having 2 Schema classes
    q = f'''
        MATCH (n {{uri: '{uri}' }})
        SET n.`_CLASS` = 666
        '''
    #db.debug_print(q, {}, "test")
    db.update_query(q)
    with pytest.raises(Exception):
        GraphSchema.class_of_data_node(node_id=uri, id_key="uri")    # Data node is associated to a non-string class name




#############   DATA IMPORT   ###########

# See separate file


#############   EXPORT SCHEMA   ###########


###############   URI'S   ###############

def test_namespace_exists(db):
    db.empty_dbase()

    assert not GraphSchema.namespace_exists("image")
    GraphSchema.create_namespace(name="junk")
    assert not GraphSchema.namespace_exists("image")

    GraphSchema.create_namespace(name="image")
    assert GraphSchema.namespace_exists("image")



def test_create_namespace(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.create_namespace(name=123)

    with pytest.raises(Exception):
        GraphSchema.create_namespace(name="")

    GraphSchema.create_namespace(name="photo")
    q = "MATCH (n:`Schema Autoincrement`) RETURN n"
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["n"] == {"namespace": "photo", "next_count": 1}

    with pytest.raises(Exception):
        GraphSchema.create_namespace(name="photo")    # Already exists


    GraphSchema.create_namespace(name="note", prefix="n-", suffix=".new")
    q = "MATCH (n:`Schema Autoincrement` {namespace: 'note'}) RETURN n"
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["n"] == {"namespace": "note", "next_count": 1, "prefix": "n-", "suffix": ".new"}



def test_reserve_next_uri(db):
    db.empty_dbase()

    GraphSchema.create_namespace(name="data_node")   # Accept default blank prefix/suffix
    assert GraphSchema.reserve_next_uri(namespace="data_node") == "1"   # Accept default blank prefix/suffix
    assert GraphSchema.reserve_next_uri("data_node") == "2"
    assert GraphSchema.reserve_next_uri("data_node") == "3"
    assert GraphSchema.reserve_next_uri(namespace="data_node", prefix="i-") == "i-4"        # Force a prefix
    assert GraphSchema.reserve_next_uri(namespace="data_node", suffix=".jpg") == "5.jpg"    # Force a suffix
    assert GraphSchema.reserve_next_uri("data_node") == "6"
    assert GraphSchema.reserve_next_uri() == "7"    # default namespace

    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace="notes")   # Namespace doesn't exist yet

    GraphSchema.create_namespace(name="notes", prefix="n-")
    assert GraphSchema.reserve_next_uri(namespace="notes") == "n-1"
    assert GraphSchema.reserve_next_uri(namespace="notes", prefix="n-") == "n-2"    # Redundant specification of prefix
    assert GraphSchema.reserve_next_uri(namespace="notes") == "n-3"                 # No need to specify the prefix (stored)

    GraphSchema.create_namespace(name="schema_node", prefix="schema-")
    assert GraphSchema.reserve_next_uri(namespace="schema_node") == "schema-1"
    assert GraphSchema.reserve_next_uri(namespace="schema_node") == "schema-2"

    GraphSchema.create_namespace(name="documents", prefix="d-", suffix="")
    assert GraphSchema.reserve_next_uri("documents", prefix="d-", suffix="") == "d-1"
    assert GraphSchema.reserve_next_uri("documents", prefix="d-") == "d-2"
    assert GraphSchema.reserve_next_uri("documents", prefix="doc.", suffix=".new") == "doc.3.new"

    GraphSchema.create_namespace(name="images", prefix="i_", suffix=".jpg")
    assert GraphSchema.reserve_next_uri("images", prefix="i_", suffix=".jpg") == "i_1.jpg"
    assert GraphSchema.reserve_next_uri("images", prefix="i_") == "i_2.jpg"
    assert GraphSchema.reserve_next_uri("documents") == "d-4"     # It remembers the original prefix
    assert GraphSchema.reserve_next_uri("documents", suffix="/view") == "d-5/view"
    assert GraphSchema.reserve_next_uri("documents") == "d-6"
    assert GraphSchema.reserve_next_uri("documents", prefix=None, suffix=None) == "d-7"

    with pytest.raises(Exception):
        assert GraphSchema.reserve_next_uri(123)    # Not a string

    with pytest.raises(Exception):
        assert GraphSchema.reserve_next_uri("       ")
    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace=123)

    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace="     ")

    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace="schema_node", prefix=666)

    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace="schema_node", suffix=["what is this"])



def test_advance_autoincrement(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        GraphSchema.reserve_next_uri(namespace="a")   # Namespace doesn't exist yet

    GraphSchema.create_namespace("a")
    GraphSchema.create_namespace("schema", suffix=".test")
    GraphSchema.create_namespace("documents", prefix="d-")
    GraphSchema.create_namespace("image", prefix="im-", suffix="-large")

    assert GraphSchema.advance_autoincrement("a") == (1, "", "")
    assert GraphSchema.advance_autoincrement("a") == (2, "", "")
    assert GraphSchema.advance_autoincrement("schema") == (1, "", ".test")
    assert GraphSchema.advance_autoincrement("schema") == (2, "", ".test")
    assert GraphSchema.advance_autoincrement("a") == (3, "", "")
    assert GraphSchema.advance_autoincrement("documents") == (1, "d-", "")
    assert GraphSchema.advance_autoincrement("documents") == (2, "d-", "")

    # The following line will "reserve" the values 3 and 4
    assert GraphSchema.advance_autoincrement("documents", advance=2) == (3, "d-", "")
    assert GraphSchema.advance_autoincrement("documents") == (5, "d-", "")

    # The following line will "reserve" the values 1 thru 10
    assert GraphSchema.advance_autoincrement("image", advance=10) == (1, "im-", "-large")
    assert GraphSchema.advance_autoincrement("image") == (11, "im-", "-large")
    assert GraphSchema.advance_autoincrement("          image   ") == (12, "im-", "-large") # Leading/trailing blanks are ignored

    with pytest.raises(Exception):
        assert GraphSchema.advance_autoincrement(123)    # Not a string

    with pytest.raises(Exception):
        assert GraphSchema.advance_autoincrement("        ")

    with pytest.raises(Exception):
        assert GraphSchema.advance_autoincrement(namespace ="a", advance ="not an integer")

    with pytest.raises(Exception):
        assert GraphSchema.advance_autoincrement(namespace ="a", advance = 0)  # Advance isn't >= 1





###############   UTILITY  METHODS   ###############

def test_is_valid_schema_uri(db):
    db.empty_dbase()
    _ , uri = GraphSchema.create_class("Records")
    assert GraphSchema.is_valid_schema_uri(uri)

    assert not GraphSchema.is_valid_schema_uri("")
    assert not GraphSchema.is_valid_schema_uri("      ")
    assert not GraphSchema.is_valid_schema_uri("abc")
    assert not GraphSchema.is_valid_schema_uri(123)
    assert not GraphSchema.is_valid_schema_uri(None)

    assert GraphSchema.is_valid_schema_uri("schema-123")
    assert not GraphSchema.is_valid_schema_uri("schema-")
    assert not GraphSchema.is_valid_schema_uri("schema-zzz")
    assert not GraphSchema.is_valid_schema_uri("schema123")



def test__prepare_data_node_labels(db):
    with pytest.raises(Exception):
        GraphSchema._prepare_data_node_labels(class_name=123)     # Bad name

    with pytest.raises(Exception):
        GraphSchema._prepare_data_node_labels(class_name="  Leading_Trailing_Blanks  ")

    assert GraphSchema._prepare_data_node_labels(class_name="Car") == ["Car"]

    with pytest.raises(Exception):
        GraphSchema._prepare_data_node_labels(class_name="Car", extra_labels=123)  # Bad extra_labels

    assert GraphSchema._prepare_data_node_labels(class_name="Car", extra_labels=" BA ") == ["Car", "BA"]

    assert GraphSchema._prepare_data_node_labels(class_name="Car", extra_labels=[" Motor Vehicle"]) \
           == ["Car", "Motor Vehicle"]

    assert GraphSchema._prepare_data_node_labels(class_name="Car", extra_labels=(" Motor Vehicle", "  Object    ")) \
           == ["Car", "Motor Vehicle", "Object"]

    assert GraphSchema._prepare_data_node_labels(class_name="Car", extra_labels=[" Motor Vehicle", "  Object    ", "Motor Vehicle"]) \
           == ["Car", "Motor Vehicle", "Object"]



def test_prepare_match_cypher_clause():
    result = GraphSchema.prepare_match_cypher_clause(node_id=123)
    assert result[0] == ""
    assert result[1] == "WHERE id(dn) = $node_id"
    assert result[2] == {"node_id": 123}

    result = GraphSchema.prepare_match_cypher_clause(node_id="c-88", id_key="uri")
    assert result[0] == ""
    assert result[1] == "WHERE dn.`uri` = $node_id"
    assert result[2] == {"node_id": "c-88"}

    result = GraphSchema.prepare_match_cypher_clause(node_id=3, id_key="dimension")
    assert result[0] == ""
    assert result[1] == "WHERE dn.`dimension` = $node_id"
    assert result[2] == {"node_id": 3}

    result = GraphSchema.prepare_match_cypher_clause(class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE dn.`_CLASS` = $class_name"
    assert result[2] == {"class_name": "Car"}

    result = GraphSchema.prepare_match_cypher_clause(node_id=123, class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE id(dn) = $node_id AND dn.`_CLASS` = $class_name"
    assert result[2] == {"node_id": 123, "class_name": "Car"}

    result = GraphSchema.prepare_match_cypher_clause(node_id="c-88", id_key="uri", class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE dn.`uri` = $node_id AND dn.`_CLASS` = $class_name"
    assert result[2] == {"node_id": "c-88", "class_name": "Car"}

    with pytest.raises(Exception):
        GraphSchema.prepare_match_cypher_clause()     # No arguments

    with pytest.raises(Exception):
        GraphSchema.prepare_match_cypher_clause(id_key="uri") # Missing arg `node_id`

    with pytest.raises(Exception):
        GraphSchema.prepare_match_cypher_clause(node_id=123, id_key=456)  # id_key, if present, must be a str