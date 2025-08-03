# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from utilities.comparisons import compare_unordered_lists, compare_recordsets
from brainannex import NeoAccess, NeoSchema
import neo4j.time


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE SCHEMAS for the testing  **************

def create_sample_schema_1():
    # Schema with patient/result/doctor Classes (each with some Properties),
    # and relationships between the Classes: HAS_RESULT, IS_ATTENDED_BY (both originating from "patient"

    patient_id, _  = NeoSchema.create_class_with_properties(name="patient",
                                                            properties=["name", "age", "balance"], strict=True)

    result_id, _  = NeoSchema.create_class_with_properties(name="result",
                                                           properties=["biomarker", "value"], strict=False)

    doctor_id, _  = NeoSchema.create_class_with_properties(name="doctor",
                                                           properties=["name", "specialty"], strict=False)

    NeoSchema.create_class_relationship(from_class="patient", to_class="result", rel_name="HAS_RESULT")
    NeoSchema.create_class_relationship(from_class="patient", to_class="doctor", rel_name="IS_ATTENDED_BY")

    return {"patient": patient_id, "result": result_id, "doctor": doctor_id}



def create_sample_schema_2():
    # Class "quotes" with relationship named "in_category" to Class "Category";
    # each Class has some properties
    _, sch_1 = NeoSchema.create_class_with_properties(name="quotes",
                                                      properties=["quote", "attribution", "verified"])

    _, sch_2 = NeoSchema.create_class_with_properties(name="Category",
                                                      properties=["name", "remarks"])

    NeoSchema.create_class_relationship(from_class="quotes", to_class="Category", rel_name="in_category")

    return {"quotes": sch_1, "category": "sch_2"}




#############   CLASS-related   #############

def test_create_class(db):
    db.empty_dbase()

    _ , french_class_uri = NeoSchema.create_class("French Vocabulary")
    match_specs = db.match(labels="CLASS")   # All Class nodes
    result = db.get_nodes(match_specs)
    assert result == [{'name': 'French Vocabulary', 'uri': french_class_uri, 'strict': False}]

    _ , class_A_uri = NeoSchema.create_class("A", strict=True)
    result = db.get_nodes(match_specs)
    expected = [{'name': 'French Vocabulary', 'uri': french_class_uri, 'strict': False},
                {'name': 'A', 'uri': class_A_uri, 'strict': True}]
    assert compare_recordsets(result, expected)

    with pytest.raises(Exception):
        assert NeoSchema.create_class("A", strict=False)  # A class by that name already exists



def test_get_class_internal_id(db):
    db.empty_dbase()
    A_neo_uri, _ = NeoSchema.create_class("A")
    assert NeoSchema.get_class_internal_id("A") == A_neo_uri

    B_neo_uri, _ = NeoSchema.create_class("B")
    assert NeoSchema.get_class_internal_id("A") == A_neo_uri
    assert NeoSchema.get_class_internal_id("B") == B_neo_uri

    with pytest.raises(Exception):
        assert NeoSchema.get_class_internal_id("NON-EXISTENT CLASS")



def test_get_class_uri(db):
    db.empty_dbase()
    _ , class_A_uri = NeoSchema.create_class("A")
    assert NeoSchema.get_class_uri("A") == class_A_uri

    _ , class_B_uri = NeoSchema.create_class("B")
    assert NeoSchema.get_class_uri("A") == class_A_uri
    assert NeoSchema.get_class_uri("B") == class_B_uri

    with pytest.raises(Exception):
        assert NeoSchema.get_class_uri("NON-EXISTENT CLASS")



def test_get_class_uri_by_internal_id(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.get_class_uri_by_internal_id(999)   # Non-existent class

    class_A_neo_uri , class_A_uri = NeoSchema.create_class("A")
    assert NeoSchema.get_class_uri_by_internal_id(class_A_neo_uri) == class_A_uri

    class_B_neo_uri , class_B_uri = NeoSchema.create_class("B")
    assert NeoSchema.get_class_uri_by_internal_id(class_A_neo_uri) == class_A_uri
    assert NeoSchema.get_class_uri_by_internal_id(class_B_neo_uri) == class_B_uri



def test_class_uri_exists(db):
    db.empty_dbase()
    assert not NeoSchema.class_uri_exists("schema-123")

    with pytest.raises(Exception):
        assert NeoSchema.class_uri_exists(123)  # Not a string

    _ , class_A_uri = NeoSchema.create_class("A")
    assert NeoSchema.class_uri_exists(class_A_uri)



def test_class_name_exists(db):
    db.empty_dbase()

    assert not NeoSchema.class_name_exists("A")
    NeoSchema.create_class("A")
    assert NeoSchema.class_name_exists("A")

    with pytest.raises(Exception):
        assert NeoSchema.class_uri_exists("B")

    with pytest.raises(Exception):
        assert NeoSchema.class_uri_exists(123)



def test_get_class_name_by_schema_uri(db):
    db.empty_dbase()
    _ , class_A_uri = NeoSchema.create_class("A")
    assert NeoSchema.get_class_name_by_schema_uri(class_A_uri) == "A"

    _ , class_B_uri = NeoSchema.create_class("B")
    assert NeoSchema.get_class_name_by_schema_uri(class_A_uri) == "A"
    assert NeoSchema.get_class_name_by_schema_uri(class_B_uri) == "B"

    with pytest.raises(Exception):
        assert NeoSchema.get_class_name_by_schema_uri("schema-XYZ")

    with pytest.raises(Exception):
        assert NeoSchema.get_class_name_by_schema_uri(123)


def test_get_class_name(db):
    db.empty_dbase()
    class_A_neoid , _ = NeoSchema.create_class("A")
    assert NeoSchema.get_class_name(class_A_neoid) == "A"

    class_B_neoid , _ = NeoSchema.create_class("B")
    assert NeoSchema.get_class_name(class_A_neoid) == "A"
    assert NeoSchema.get_class_name(class_B_neoid) == "B"

    with pytest.raises(Exception):
        NeoSchema.get_class_name(2345)                    # No such Class exists

    with pytest.raises(Exception):
        NeoSchema.get_class_name(-1)                      # Invalid internal dbase id

    with pytest.raises(Exception):
        NeoSchema.get_class_name("I'm not an integer!")   # Invalid internal dbase id



def test_get_class_attributes(db):
    db.empty_dbase()

    class_A_neoid , class_A_uri = NeoSchema.create_class("A")
    assert NeoSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'uri': class_A_uri, 'strict': False}

    class_B_neoid , class_B_uri = NeoSchema.create_class("B", no_datanodes=True)
    assert NeoSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'uri': class_A_uri, 'strict': False}
    assert NeoSchema.get_class_attributes(class_B_neoid) == {'name': 'B', 'uri': class_B_uri, 'strict': False, 'no_datanodes': True}

    with pytest.raises(Exception):
        NeoSchema.get_class_attributes(2345)                    # No such Class exists
        NeoSchema.get_class_attributes(-1)                      # Invalid id
        NeoSchema.get_class_attributes("I'm not an integer!")   # Invalid id



def test_get_all_classes(db):
    db.empty_dbase()

    class_list = NeoSchema.get_all_classes()
    assert class_list == []

    NeoSchema.create_class("p")
    class_list = NeoSchema.get_all_classes()
    assert class_list == ['p']

    NeoSchema.create_class("A")
    NeoSchema.create_class("c")

    class_list = NeoSchema.get_all_classes()
    assert class_list == ['A', 'c', 'p']



def test_rename_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.rename_class(old_name="some name", new_name="some name")

    with pytest.raises(Exception):
        NeoSchema.rename_class(old_name="some name", new_name="")

    with pytest.raises(Exception):
        NeoSchema.rename_class(old_name="some name", new_name="    bad name    ")

    with pytest.raises(Exception):
        NeoSchema.rename_class(old_name="Car", new_name="Vehicle")  # Doesn't exist

    internal_id, _ = NeoSchema.create_class_with_properties("Car", strict=True,
                                properties=["color"])

    result = NeoSchema.rename_class(old_name="Car", new_name="Vehicle")
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
    data_node_id = NeoSchema.create_data_node(class_name="Vehicle", properties={"color": "white"},
                                              extra_labels="West Coast")

    result = NeoSchema.rename_class(old_name="Vehicle", new_name="Recreational Vehicle")
    assert result == 1      # 1 Data Nodes was affected

    q = f'''
        MATCH (n :`Recreational Vehicle`:`West Coast`) 
        WHERE id(n) = {data_node_id} AND n.`_SCHEMA` = "Recreational Vehicle" AND n.color = "white"
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
    french_id , french_uri  = NeoSchema.create_class("French Vocabulary")
    foreign_id, foreign_uri = NeoSchema.create_class("Foreign Vocabulary")

    # Blank or None name will also raise an Exception
    with pytest.raises(Exception):
        assert NeoSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="")
    with pytest.raises(Exception):
        assert NeoSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name=None)

    NeoSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="INSTANCE_OF")

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
        assert NeoSchema.create_class_relationship(from_class=french_id, to_class=foreign_id, rel_name="INSTANCE_OF")


    NeoSchema.create_class("German Vocabulary")
    # Mixing names and internal database ID's
    NeoSchema.create_class_relationship(from_class="German Vocabulary", to_class=foreign_id, rel_name="INSTANCE_OF")

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


    _, course_uri = NeoSchema.create_class("Course")
    NeoSchema.create_class_relationship(from_class="Foreign Vocabulary", to_class="Course",
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
    NeoSchema.create_class("A")
    NeoSchema.create_class("B")

    with pytest.raises(Exception):
        NeoSchema.class_relationship_exists(from_class="", to_class="B", rel_name="whatever name")

    with pytest.raises(Exception):
        NeoSchema.class_relationship_exists(from_class="A", to_class="", rel_name="whatever name")

    with pytest.raises(Exception):
        NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="")

    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="owns")

    NeoSchema.create_class_relationship(from_class="A", to_class="B", rel_name="owns")

    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="owns")

    assert not NeoSchema.class_relationship_exists(from_class="B", to_class="A", rel_name="owns")   # Reverse direction

    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="sells")  # Different link

    NeoSchema.create_class("SA")
    NeoSchema.create_class_relationship(from_class="A", to_class="SA", rel_name="INSTANCE_OF")
    NeoSchema.create_class_relationship(from_class="SA", to_class="B", rel_name="sells")

    # A "sells" relationship now exists (indirectly) from "A" to "B" because "A" was made an instance of "SA"
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="sells")

    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="builds")

    NeoSchema.create_class("SSA")
    NeoSchema.create_class_relationship(from_class="SA", to_class="SSA", rel_name="INSTANCE_OF")
    NeoSchema.create_class_relationship(from_class="SSA", to_class="B", rel_name="builds")

    # A "builds" relationship now exists (indirectly) from "A" to "B" because we can go thru "SSA"
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="builds")


    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="does business with")

    NeoSchema.create_class("SB")
    NeoSchema.create_class_relationship(from_class="B", to_class="SB", rel_name="INSTANCE_OF")
    NeoSchema.create_class_relationship(from_class="SSA", to_class="SB", rel_name="does business with")

    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="does business with")


    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="loans out")
    NeoSchema.create_class_relationship(from_class="A", to_class="B", rel_name="loans out", use_link_node=True)
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="loans out")

    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="friends with")
    NeoSchema.create_class_relationship(from_class="SA", to_class="SB", rel_name="friends with", use_link_node=True)
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="friends with")



def test_delete_class_relationship(db):
    db.empty_dbase()
    _ , class_A_uri = NeoSchema.create_class("A")
    _ , class_B_uri = NeoSchema.create_class("B")

    with pytest.raises(Exception):
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name=None)
    with pytest.raises(Exception):
        NeoSchema.delete_class_relationship(from_class="", to_class="B", rel_name="some name")
    with pytest.raises(Exception):
        NeoSchema.delete_class_relationship(from_class="A", to_class=None, rel_name="some name")
    with pytest.raises(Exception):
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create a relationship, and then immediately delete it
    NeoSchema.create_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    n_del = NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert n_del == 1
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    with pytest.raises(Exception):  # Attempting to re-delete it, will cause error
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create 2 different relationships between the same classes, then delete each relationship at a time
    NeoSchema.create_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    NeoSchema.create_class_relationship(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="BOGUS_RELATIONSHIP")

    n_del = NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert n_del == 1
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")

    n_del = NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="LINKED_TO")
    assert n_del == 1
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="LINKED_TO")



def test_unlink_classes(db):
    db.empty_dbase()
    person, _ = NeoSchema.create_class(name="Person")
    car, _ = NeoSchema.create_class(name="Car")

    # Create links in both directions between our 2 Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    q = "MATCH (:CLASS {name: 'Person'}) -[r]- (:CLASS {name: 'Car'}) RETURN count(r) AS n_rel"
    assert db.query(q, single_cell="n_rel") == 2

    assert NeoSchema.unlink_classes(class1="Person", class2="Car") == 2     # Use class names
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert NeoSchema.unlink_classes(class1="Person", class2=car) == 2       # Use class name and internal ID
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert NeoSchema.unlink_classes(class1=person, class2="Car") == 2       # Use internal ID and class name
    assert db.query(q, single_cell="n_rel") == 0


    # Re-create links in both directions between our 2 Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="OWNS")
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_OWNED_BY")

    assert NeoSchema.unlink_classes(class1=person, class2=car) == 2      # Use internal IDs
    assert db.query(q, single_cell="n_rel") == 0



def test_delete_class(db):
    db.empty_dbase()

    # Nonexistent classes
    with pytest.raises(Exception):
        NeoSchema.delete_class("I_dont_exist")

    with pytest.raises(Exception):
        NeoSchema.delete_class("I_dont_exist", safe_delete=False)


    # Classes with no properties and no relationships
    NeoSchema.create_class("French Vocabulary")
    NeoSchema.create_class("German Vocabulary")

    NeoSchema.delete_class("French Vocabulary", safe_delete=False)
    # French should be gone; but German still there
    assert not NeoSchema.class_name_exists("French Vocabulary")
    assert NeoSchema.class_name_exists("German Vocabulary")

    NeoSchema.delete_class("German Vocabulary")
    # Both classes gone
    assert not NeoSchema.class_name_exists("French Vocabulary")
    assert not NeoSchema.class_name_exists("German Vocabulary")

    with pytest.raises(Exception):
        NeoSchema.delete_class("German Vocabulary")     # Was already deleted


    # Interlinked Classes with properties, but no data nodes
    db.empty_dbase()
    create_sample_schema_1()    # Schema with patient/result/doctor
    NeoSchema.delete_class("doctor")
    assert NeoSchema.class_name_exists("patient")
    assert NeoSchema.class_name_exists("result")
    assert not NeoSchema.class_name_exists("doctor")
    # The Class "patient" is still linked to the Class "result"
    assert NeoSchema.get_linked_class_names(class_name="patient", rel_name="HAS_RESULT") == ["result"]

    NeoSchema.delete_class("patient")
    assert not NeoSchema.class_name_exists("patient")
    assert NeoSchema.class_name_exists("result")
    assert not NeoSchema.class_name_exists("doctor")

    NeoSchema.delete_class("result")
    assert not NeoSchema.class_name_exists("patient")
    assert not NeoSchema.class_name_exists("result")
    assert not NeoSchema.class_name_exists("doctor")


    # Interlinked Classes with properties; one of the Classes has an attached data node
    db.empty_dbase()
    create_sample_schema_2()    # Schema with quotes and categories
    NeoSchema.create_data_node(class_name="quotes",
                               properties={"quote": "Comparison is the thief of joy"})

    NeoSchema.delete_class("Category")    # No problem in deleting this Class with no attached data nodes
    assert NeoSchema.class_name_exists("quotes")
    assert not NeoSchema.class_name_exists("Category")

    with pytest.raises(Exception):
        NeoSchema.delete_class("quotes")    # But cannot by default delete Classes with data nodes

    NeoSchema.delete_class("quotes", safe_delete=False)     # Over-ride default protection mechanism

    q = '''
    MATCH (d :quotes)
    WHERE d.`_SCHEMA` IS NOT NULL
    RETURN count(d) AS number_orphaned
    '''
    assert db.query(q, single_cell="number_orphaned") == 1  # Now there's an "orphaned" data node



def test_is_link_allowed(db):
    db.empty_dbase()

    NeoSchema.create_class("strict", strict=True)
    NeoSchema.create_class("lax1", strict=False)
    NeoSchema.create_class("lax2", strict=False)

    assert NeoSchema.is_link_allowed("belongs to", from_class="lax1", to_class="lax2")  # Anything goes, if both Classes are lax!

    with pytest.raises(Exception):   # Classes that doesn't exist
        NeoSchema.is_link_allowed("belongs to", from_class="nonexistent", to_class="lax2")

    with pytest.raises(Exception):
        assert not NeoSchema.is_link_allowed("belongs to", from_class="lax1", to_class="nonexistent")

    assert not NeoSchema.is_link_allowed("belongs to", from_class="lax1", to_class="strict")

    NeoSchema.create_class_relationship(from_class="lax1", to_class="strict",
                                        rel_name="belongs to")

    assert  NeoSchema.is_link_allowed("belongs to", from_class="lax1", to_class="strict")

    assert  not NeoSchema.is_link_allowed("works for", from_class="strict", to_class="lax2")

    NeoSchema.create_class_relationship(from_class="strict", to_class="lax2",
                                        rel_name="works for", use_link_node=True)

    assert  NeoSchema.is_link_allowed("works for", from_class="strict", to_class="lax2")


    # Now check situations involving "INSTANCE_OF" relationships
    NeoSchema.create_class("ancestor", strict=True)
    NeoSchema.create_class_relationship(from_class="ancestor", to_class="lax2",
                                        rel_name="supplied by")
    assert NeoSchema.is_link_allowed("supplied by", from_class="ancestor", to_class="lax2")
    assert not NeoSchema.is_link_allowed("supplied by", from_class="strict", to_class="lax2")
    NeoSchema.create_class_relationship(from_class="strict", to_class="ancestor",
                                        rel_name="INSTANCE_OF")
    assert NeoSchema.is_link_allowed("supplied by", from_class="strict", to_class="lax2")   # Now allowed thru 'ISTANCE_OF` ancestry



def test_is_strict_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.is_strict_class("I dont exist")

    NeoSchema.create_class("I am strict", strict=True)
    assert NeoSchema.is_strict_class("I am strict")

    NeoSchema.create_class("I am lax", strict=False)
    assert not NeoSchema.is_strict_class("I am lax")

    db.create_node(labels="CLASS", properties={"name": "Damaged_class"})
    assert not NeoSchema.is_strict_class("Damaged_class")   # Sloppily-create Class node lacking a "strict" attribute




def test_is_strict_class_fast(db):
    db.empty_dbase()

    internal_id , _ = NeoSchema.create_class("I am strict", strict=True)
    assert NeoSchema.is_strict_class_fast(internal_id)

    internal_id , _ = NeoSchema.create_class("I am lax", strict=False)
    assert not NeoSchema.is_strict_class_fast(internal_id)



def test_allows_data_nodes(db):
    db.empty_dbase()

    int_id_yes , _ = NeoSchema.create_class("French Vocabulary")
    assert NeoSchema.allows_data_nodes(class_name="French Vocabulary") == True
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_yes) == True

    int_id_no , _ = NeoSchema.create_class("Vocabulary", no_datanodes = True)
    assert NeoSchema.allows_data_nodes(class_name="Vocabulary") == False
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_no) == False




def test_get_class_instances(db):
    pass    # TODO



def test_get_related_class_names(db):
    pass    # TODO



def test_get_class_relationships(db):
    db.empty_dbase()

    assert NeoSchema.get_class_relationships(class_name="I_dont_exist") == {"in": [], "out": []}

    NeoSchema.create_class(name="Loner")
    assert NeoSchema.get_class_relationships(class_name="Loner") == {"in": [], "out": []}
    assert NeoSchema.get_class_relationships(class_name="Loner", link_dir="OUT") == []
    assert NeoSchema.get_class_relationships(class_name="Loner", link_dir="IN") == []

    create_sample_schema_1()    # Schema with patient/result/doctor

    result = NeoSchema.get_class_relationships(class_name="patient", link_dir="OUT")
    assert compare_unordered_lists(result, ["HAS_RESULT", "IS_ATTENDED_BY"])
    assert NeoSchema.get_class_relationships(class_name="patient", link_dir="IN") == []

    assert NeoSchema.get_class_relationships(class_name="doctor", link_dir="OUT") == []
    assert NeoSchema.get_class_relationships(class_name="doctor", link_dir="IN") == ["IS_ATTENDED_BY"]

    assert NeoSchema.get_class_relationships(class_name="result", link_dir="OUT") == []
    assert NeoSchema.get_class_relationships(class_name="result", link_dir="IN") == ["HAS_RESULT"]

    #TODO: test the omit_instance argument




#############   PROPERTIES-RELATED   #############


def test_get_class_properties(db):
    db.empty_dbase()

    NeoSchema.create_class_with_properties("My first class", properties=["A", "B", "C"])
    neo_uri = NeoSchema.get_class_internal_id("My first class")
    props = NeoSchema.get_class_properties(neo_uri)
    assert props == ["A", "B", "C"]
    props = NeoSchema.get_class_properties("My first class")
    assert props == ["A", "B", "C"]

    neo_uri, _ = NeoSchema.create_class("My BIG class")
    props = NeoSchema.get_class_properties(neo_uri)
    assert props == []
    props = NeoSchema.get_class_properties("My BIG class")
    assert props == []

    NeoSchema.add_properties_to_class(class_node=neo_uri, property_list = ["X", "Y"])
    props = NeoSchema.get_class_properties(neo_uri)
    assert props == ["X", "Y"]
    props = NeoSchema.get_class_properties(class_node="My BIG class")
    assert props == ["X", "Y"]

    NeoSchema.add_properties_to_class(class_node=neo_uri, property_list = ["Z"])
    props = NeoSchema.get_class_properties(neo_uri)
    assert props == ["X", "Y", "Z"]


    # Make "My first class" an instance of "My BIG class"
    NeoSchema.create_class_relationship(from_class="My first class", to_class="My BIG class", rel_name="INSTANCE_OF")

    props = NeoSchema.get_class_properties("My first class", include_ancestors=False)
    assert props == ["A", "B", "C"]

    props = NeoSchema.get_class_properties("My first class", include_ancestors=True)
    assert compare_unordered_lists(props, ["A", "B", "C", "X", "Y", "Z"])

    with pytest.raises(Exception):
        NeoSchema.get_class_properties("My first class", sort_by_path_len="meaningless")

    props = NeoSchema.get_class_properties("My first class", include_ancestors=True, sort_by_path_len="ASC")
    assert props == ["A", "B", "C", "X", "Y", "Z"]

    props = NeoSchema.get_class_properties("My first class", include_ancestors=True, sort_by_path_len="DESC")
    assert props == ["X", "Y", "Z", "A", "B", "C"]


    # Set Property "Y" to be a "system" one
    NeoSchema.set_property_attribute(class_name="My BIG class", prop_name="Y",
                                     attribute_name="system", attribute_value=True)

    props = NeoSchema.get_class_properties("My BIG class")
    assert props == ["X", "Y", "Z"]

    props = NeoSchema.get_class_properties("My BIG class", exclude_system=True)
    assert props == ["X", "Z"]

    props = NeoSchema.get_class_properties("My first class", include_ancestors=True,
                                           sort_by_path_len="ASC", exclude_system=True)
    assert props == ["A", "B", "C", "X", "Z"]

    props = NeoSchema.get_class_properties("My first class", include_ancestors=True,
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

    assert not NeoSchema.is_property_allowed(property_name="cost", class_name="I_dont_exist")

    NeoSchema.create_class_with_properties("My Lax class", ["A", "B"], strict=False)
    _, strict_uri = NeoSchema.create_class_with_properties("My Strict class", ["X", "Y"], strict=True)

    assert NeoSchema.is_property_allowed(property_name="A", class_name="My Lax class")
    assert NeoSchema.is_property_allowed(property_name="B", class_name="My Lax class")
    assert NeoSchema.is_property_allowed(property_name="anything goes in a nonstrict class", class_name="My Lax class")

    assert NeoSchema.is_property_allowed(property_name="X", class_name="My Strict class")
    assert NeoSchema.is_property_allowed(property_name="Y", class_name="My Strict class")
    assert not NeoSchema.is_property_allowed(property_name="some other field", class_name="My Strict class")

    NeoSchema.add_properties_to_class(class_uri=strict_uri, property_list=["some other field"])   # Now it will be declared!

    assert NeoSchema.is_property_allowed(property_name="some other field", class_name="My Strict class")


    _ , german_uri = NeoSchema.create_class_with_properties("German Vocabulary", ["German"], strict=True)
    assert NeoSchema.is_property_allowed(property_name="German", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")

    # "notes" and "English" are Properties of the more general "Foreign Vocabulary" Class,
    # of which "German Vocabulary" is an instance
    _ , foreign_uri = NeoSchema.create_class_with_properties("Foreign Vocabulary", ["English", "notes"], strict=True)
    NeoSchema.create_class_relationship(from_class="German Vocabulary", to_class="Foreign Vocabulary", rel_name="INSTANCE_OF")

    assert NeoSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")

    _ , content_uri = NeoSchema.create_class_with_properties("Content Item", ["uri"], strict=True)
    NeoSchema.create_class_relationship(from_class="Foreign Vocabulary", to_class="Content Item", rel_name="INSTANCE_OF")

    assert NeoSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")   # "uri" is now available thru ancestry
    assert NeoSchema.is_property_allowed(property_name="uri", class_name="Foreign Vocabulary")

    assert not NeoSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    # Properties "New_1", "New_2", "New_3" will be added, respectively,
    # to the Classes "German Vocabulary", "Foreign Vocabulary" and "Content Item"
    NeoSchema.add_properties_to_class(class_uri=german_uri, property_list=["New_1"])
    assert NeoSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    NeoSchema.add_properties_to_class(class_uri=foreign_uri, property_list=["New_2"])
    assert NeoSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    NeoSchema.add_properties_to_class(class_uri=content_uri, property_list=["New_3"])
    assert NeoSchema.is_property_allowed(property_name="New_1", class_name="German Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="New_2", class_name="German Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="New_3", class_name="German Vocabulary")

    assert not NeoSchema.is_property_allowed(property_name="New_1", class_name="Foreign Vocabulary")    # "New_1" was added to "German Vocabulary"
    assert NeoSchema.is_property_allowed(property_name="New_2", class_name="Foreign Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="New_3", class_name="Foreign Vocabulary")

    assert not NeoSchema.is_property_allowed(property_name="New_1", class_name="Content Item")
    assert not NeoSchema.is_property_allowed(property_name="New_2", class_name="Content Item")      # New_2" was added to "Foreign Vocabulary"
    assert NeoSchema.is_property_allowed(property_name="New_3", class_name="Content Item")



def test_allowable_props(db):
    db.empty_dbase()

    lax_int_uri, lax_schema_uri = NeoSchema.create_class_with_properties("My Lax class", ["A", "B"], strict=False)
    strict_int_uri, strict_schema_uri = NeoSchema.create_class_with_properties("My Strict class", ["A", "B"], strict=True)


    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped


    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123}  # "C" got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_internal_id=strict_int_uri,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=False)


    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"X": 666, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {}      # Everything got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_internal_id=strict_int_uri,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=False)





#############   SCHEMA-CODE  RELATED   ###########

def test_get_schema_code(db):
    pass    # TODO



def test_get_schema_uri(db):
    db.empty_dbase()
    _ , schema_uri_i = NeoSchema.create_class("My_class", code="i")
    _ , schema_uri_n = NeoSchema.create_class("My_other_class", code="n")

    assert NeoSchema.get_schema_uri(schema_code="i") == schema_uri_i
    assert NeoSchema.get_schema_uri(schema_code="n") == schema_uri_n
    assert NeoSchema.get_schema_uri(schema_code="x") == ""



################   DATA NODES : READING   ##############

def test_all_properties(db):
    pass    # TODO

def test_get_data_node_internal_id(db):
    pass    # TODO

def test_get_data_node_id(db):
    pass    # TODO

def test_data_node_exists(db):
    pass    # TODO

def test_data_link_exists(db):
    pass    # TODO

def test_get_data_link_properties(db):
    pass    # TODO



def test_get_data_node(db):
    db.empty_dbase()

    NeoSchema.create_class(name="Car")
    db_id = NeoSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white"})

    result = NeoSchema.get_data_node(class_name="Car", node_id=db_id)
    assert result == {'color': 'white', 'make': 'Toyota'}

    result = NeoSchema.get_data_node(class_name="Car", node_id=db_id, hide_schema=False)
    assert result == {'_SCHEMA': 'Car', 'color': 'white', 'make': 'Toyota'}

    # Now try it on a generic database node that is NOT a Data Node
    db_id = db.create_node(labels="Car", properties={"make": "BMW", "color": "red"})
    result = NeoSchema.get_data_node(class_name="Car", node_id=db_id)
    assert result is None



def test_get_nodes_by_filter(db):
    db.empty_dbase()

    assert NeoSchema.get_nodes_by_filter() == []

    db.create_node(labels="Car", properties={"color": "yellow", "year": 1999})      # A GENERIC node (not a Data Node)

    assert NeoSchema.get_nodes_by_filter() == [{"color": "yellow", "year": 1999}]

    assert NeoSchema.get_nodes_by_filter(labels="Car") == [{"color": "yellow", "year": 1999}]

    assert NeoSchema.get_nodes_by_filter(labels="Car", key_name="") == [{"color": "yellow", "year": 1999}]

    with pytest.raises(Exception):
        NeoSchema.get_nodes_by_filter(labels="Car", key_name="some_key_name")   # Key name but no value

    result = NeoSchema.get_nodes_by_filter(labels="Car", key_name="color", key_value="yellow")
    assert result == [{"color": "yellow", "year": 1999}]

    result = NeoSchema.get_nodes_by_filter(labels="Car", key_name="color", key_value="lavender")
    assert result == []

    result = NeoSchema.get_nodes_by_filter(labels="Plane", key_name="color", key_value="yellow")
    assert result == []

    result = NeoSchema.get_nodes_by_filter(class_name="Car", key_name="color", key_value="yellow")
    assert result == []


    # Create a Schema
    NeoSchema.create_class_with_properties(name="Car", properties=["color", "year", "make"], strict=True)

    NeoSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "grey"})

    result = NeoSchema.get_nodes_by_filter(class_name="Elephant")
    assert result == []

    result = NeoSchema.get_nodes_by_filter(class_name="Car")    # This locates 1 node
    assert result == [{'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = NeoSchema.get_nodes_by_filter(labels="Car")        # This locates 2 nodes
    expected = [{"_SCHEMA": "Car", "color": "grey", "make": "Toyota"},
                {"color": "yellow", "year": 1999}
               ]
    assert compare_recordsets(result, expected)

    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="toyota")
    assert result == []     # Case-sensitive


    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="Toy")
    assert result == []

    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="Toy", string_match="ENDS WITH")
    assert result == []

    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="yota", string_match="ENDS WITH")
    assert result == [{'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="Toy", string_match="STARTS WITH")
    assert result == [{'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="Toy", string_match="CONTAINS")
    assert result == [{'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'}]

    # Add a 3rd car
    NeoSchema.create_data_node(class_name="Car", properties={"make": "Chevrolet", "color": "pink", "year": 1955})

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="year")
    assert result == [{'_SCHEMA': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'},
                      {'color': 'yellow', 'year': 1999},
                      {'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'}
                     ]          # The record with no date will be at the end, when sorting in ascending order

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="  year    DESC    ")
    assert result == [{'_SCHEMA': 'Car', 'color': 'grey', 'make': 'Toyota'},
                      {'color': 'yellow', 'year': 1999},
                      {'_SCHEMA': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'}
                     ]          #  The record with no date will be at the end, when sorting in descending order


    # Add a 4th car
    NeoSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white", "year": 1988})

     # Add a 5th car
    NeoSchema.create_data_node(class_name="Car", properties={"make": "Chevrolet", "color": "green", "year": 1970})

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC")
    assert result == [  {'make': 'Chevrolet', 'year': 1970,'_SCHEMA': 'Car', 'color': 'green' },
                        {'make': 'Chevrolet', 'year': 1955, '_SCHEMA': 'Car', 'color': 'pink'},
                        {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_SCHEMA': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999}]

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC", limit=4)
    assert result == [  {'make': 'Chevrolet', 'year': 1970,'_SCHEMA': 'Car', 'color': 'green' },
                        {'make': 'Chevrolet', 'year': 1955, '_SCHEMA': 'Car', 'color': 'pink'},
                        {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_SCHEMA': 'Car', 'color': 'white'}]

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="make, year DESC", skip=2)
    assert result == [  {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'},
                        {'make': 'Toyota','year': 1988, '_SCHEMA': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999}]

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="   make   , year   DESC   ", skip=2, limit=1)
    assert result == [  {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'}]

    # Add a 6th car; notice the lower case
    NeoSchema.create_data_node(class_name="Car", properties={"make": "fiat", "color": "blue", "year": 1970})

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="make, year")
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_SCHEMA': 'Car', 'color': 'pink'},
                        {'make': 'Chevrolet', 'year': 1970,'_SCHEMA': 'Car', 'color': 'green' },
                        {'make': 'Toyota', 'year': 1988, '_SCHEMA': 'Car', 'color': 'white'},
                        {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'},
                        {'make': 'fiat', 'year': 1970, '_SCHEMA': 'Car', 'color': 'blue'},
                        {'color': 'yellow', 'year': 1999}]   # "fiat" comes after "Toyota" due to capitalization

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="make, year", ignore_case=["make"])
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_SCHEMA': 'Car', 'color': 'pink'},
                        {'make': 'Chevrolet', 'year': 1970,'_SCHEMA': 'Car', 'color': 'green' },
                        {'make': 'fiat', 'year': 1970, '_SCHEMA': 'Car', 'color': 'blue'},
                        {'make': 'Toyota', 'year': 1988, '_SCHEMA': 'Car', 'color': 'white'},
                        {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'},
                        {'color': 'yellow', 'year': 1999}]  # The "fiat" is now alphabetized regardless of case


    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="year, make DESC", ignore_case=["make"])
    assert result == [  {'make': 'Chevrolet', 'year': 1955, '_SCHEMA': 'Car', 'color': 'pink'},
                        {'make': 'fiat', 'year': 1970, '_SCHEMA': 'Car', 'color': 'blue'},
                        {'make': 'Chevrolet', 'year': 1970,'_SCHEMA': 'Car', 'color': 'green' },
                        {'make': 'Toyota', 'year': 1988, '_SCHEMA': 'Car', 'color': 'white'},
                        {'color': 'yellow', 'year': 1999},
                        {'make': 'Toyota', '_SCHEMA': 'Car', 'color': 'grey'}]

    # Add a 7th car; notice the blank in the new field name
    db.create_node(labels="Car", properties={"year": 2003, "decommission year": 2025})      # A GENERIC node (not a Data Node)

    result = NeoSchema.get_nodes_by_filter(labels="Car", order_by="decommission year, make, year", ignore_case=["make"], limit=2)
    assert result == [{'decommission year': 2025, 'year': 2003},
                      {'_SCHEMA': 'Car', 'color': 'pink', 'year': 1955, 'make': 'Chevrolet'}]

    with pytest.raises(Exception):
        # Trying to sort by a property (field) name unregistered with the Schema
        NeoSchema.get_nodes_by_filter(class_name="Car", key_name="color", key_value="yellow",
                                      order_by="SOME_UNKNOWN_FIELD")


    # Add an 8th car, using a date as a field value
    db.create_node(labels="Car", properties={"color": "red", "make": "Honda",
                                             "bought_on": neo4j.time.Date(2019, 6, 1),
                                             "certified": neo4j.time.DateTime(2019, 1, 31, 18, 59, 35)
                                             })
    result = NeoSchema.get_nodes_by_filter(key_name="make", key_value="Honda")  # Retrieve that latest node
    assert result == [{'color': 'red', 'make': 'Honda',
                       'bought_on': '2019/06/01', 'certified': '2019/01/31'}]



def test__process_order_by():
    s = "John DESC, Alice, Bob desc, Carol"
    result = NeoSchema._process_order_by(s)
    assert result == "n.`John` DESC, n.`Alice`, n.`Bob` DESC, n.`Carol`"

    s = "make, built year, make, decommission year DESC"
    result = NeoSchema._process_order_by(s)
    assert result == "n.`make`, n.`built year`, n.`make`, n.`decommission year` DESC"

    s = "  A B    C desc  ,   D desc,E,F G  "
    result = NeoSchema._process_order_by(s, dummy_node_name="node")
    assert result == "node.`A B    C` DESC, node.`D` DESC, node.`E`, node.`F G`"

    s="Alice DESC,Bob,   Carol   DESC   ,Disc Number    "
    result = NeoSchema._process_order_by(s, ignore_case = ["Carol"])
    assert result == "n.`Alice` DESC, n.`Bob`, toLower(n.`Carol`) DESC, n.`Disc Number`"



def test_search_data_node(db):
    db.empty_dbase()

    NeoSchema.create_class(name="Car")

    # Create a data node without uri field
    db_id = NeoSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white"})

    result = NeoSchema.search_data_node(internal_id=db_id)
    assert result == {'color': 'white', 'make': 'Toyota'}

    result = NeoSchema.search_data_node(internal_id=db_id, hide_schema=False)
    assert result == {'_SCHEMA': 'Car', 'color': 'white', 'make': 'Toyota'}

    result = NeoSchema.search_data_node(internal_id=99999)
    assert result is None   # Not found

    result = NeoSchema.search_data_node(uri="I don't exist")
    assert result is None   # Not found


    # Now try it on a generic database node that is NOT a Data Node
    db_id = db.create_node(labels="Car", properties={"make": "BMW", "color": "red"})
    result = NeoSchema.search_data_node(internal_id=db_id)
    assert result is None


    # Create data node with uri field
    NeoSchema.create_data_node(class_name="Car",
                               properties={"make": "Honda", "color": "blue"}, new_uri="car-1")

    with pytest.raises(Exception):
        NeoSchema.search_data_node()

    result = NeoSchema.search_data_node(uri="car-1")
    assert result == {'make': 'Honda', 'color': 'blue', 'uri': 'car-1'}



def test_locate_node(db):
    pass    # TODO



def test_get_all_data_nodes_of_class(db):
    db.empty_dbase()

    result= NeoSchema.get_all_data_nodes_of_class("Car")
    assert result == []

    NeoSchema.create_class(name="Car")
    
    result= NeoSchema.get_all_data_nodes_of_class("Car")
    assert result == []

    # Add a generic database node that is NOT a Data Node (with same label)
    db.create_node(labels="Car", properties={"make": "BMW", "color": "red"})
    result = NeoSchema.get_all_data_nodes_of_class(class_name="Car")
    assert result == []

    # Create a data node without uri field
    db_id_car1 = NeoSchema.create_data_node(class_name="Car", properties={"make": "Toyota", "color": "white"})

    result= NeoSchema.get_all_data_nodes_of_class(class_name="Car")
    assert result == [{'color': 'white', 'make': 'Toyota', 'internal_id': db_id_car1, 'neo4j_labels': ['Car']}]

    result= NeoSchema.get_all_data_nodes_of_class(class_name="Car", hide_schema=False)
    assert result == [{'_SCHEMA': 'Car', 'color': 'white', 'make': 'Toyota', 'internal_id': db_id_car1, 'neo4j_labels': ['Car']}]


    result= NeoSchema.get_all_data_nodes_of_class(class_name="Boat")
    assert result == []

    # Create a data node without uri field
    NeoSchema.create_class(name="Boat")
    db_id_boat1 = NeoSchema.create_data_node(class_name="Boat", properties={"make": "C&C", "type": "sloop"})

    result= NeoSchema.get_all_data_nodes_of_class(class_name="Boat")
    assert result == [{'make': 'C&C', 'type': 'sloop', 'internal_id': db_id_boat1, 'neo4j_labels': ['Boat']}]

    # Create a data node with uri field
    db_id_car2 = NeoSchema.create_data_node(class_name="Car", properties={"make": "Fiat", "color": "blue"}, new_uri="cincilla")

    result= NeoSchema.get_all_data_nodes_of_class(class_name="Car")

    expected = [{'make': 'Toyota', 'color': 'white', 'internal_id': db_id_car1, 'neo4j_labels': ['Car']},
                {'make': 'Fiat', 'color': 'blue', 'internal_id': db_id_car2, 'neo4j_labels': ['Car'], 'uri': 'cincilla'}
               ]

    assert compare_recordsets(result, expected)



def test_class_of_data_node(db):
    pass    # TODO

def test_data_nodes_of_class(db):
    pass    # TODO



def test_count_data_nodes_of_class(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.count_data_nodes_of_class("unknown")   # Non-existent Class

    NeoSchema.create_class("Some class")

    assert NeoSchema.count_data_nodes_of_class("Some class") == 0

    NeoSchema.create_data_node(class_name="Some class")
    assert NeoSchema.count_data_nodes_of_class("Some class") == 1

    NeoSchema.create_data_node(class_name="Some class")
    assert NeoSchema.count_data_nodes_of_class("Some class") == 2


    NeoSchema.create_class("Another class")

    assert NeoSchema.count_data_nodes_of_class("Another class") == 0

    NeoSchema.create_data_node(class_name="Another class")
    assert NeoSchema.count_data_nodes_of_class("Another class") == 1

    assert NeoSchema.count_data_nodes_of_class("Some class") == 2   # Where we left it off



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
        NeoSchema.create_data_node(class_name="nonexistent",
                                   properties={"name": "who cares?"})

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="doctor", properties="NOT a dict")


    # Create a 1st "doctor" data node
    internal_id = NeoSchema.create_data_node(class_name="doctor",
                                             properties={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                             extra_labels = None,
                                             new_uri=None, silently_drop=False)

    q = '''
        MATCH (dn :doctor {name: "Dr. Preeti", specialty: "sports medicine", `_SCHEMA`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'dn': {'specialty': 'sports medicine', 'name': 'Dr. Preeti', '_SCHEMA': "doctor"}}


    # Create a 2nd "doctor" data node, this time assigning an extra label and storing a URI
    uri = "doc-1"
    internal_id = NeoSchema.create_data_node(class_name="doctor",
                                             properties={"name": "Dr. Watson", "specialty": "genetics"},
                                             extra_labels = "Nobelist",
                                             new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:Nobelist {name: "Dr. Watson", specialty: "genetics", `_SCHEMA`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'dn': {'specialty': 'genetics', 'name': 'Dr. Watson', 'uri': uri, '_SCHEMA': "doctor"}}


    # Create a 3rd "doctor" data node, this time assigning 2 extra labels and also assigning a URI
    uri = "d-123"
    internal_id = NeoSchema.create_data_node(class_name="doctor",
                                             properties={"name": "Dr. Lewis", "specialty": "radiology"},
                                             extra_labels = ["retired", "person"],
                                             new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:retired:person {name: "Dr. Lewis", specialty: "radiology", `_SCHEMA`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'dn': {'specialty': 'radiology', 'name': 'Dr. Lewis', 'uri': uri, '_SCHEMA': "doctor"}}


    # Create a 4th "doctor" data node, this time using a tuple rather than a list to assign 2 extra labels
    uri = "d-999"
    internal_id = NeoSchema.create_data_node(class_name="doctor",
                                             properties={"name": "Dr. Clark", "specialty": "pediatrics"},
                                             extra_labels = ("retired", "person"),
                                             new_uri=uri, silently_drop=False)

    q = '''
        MATCH (dn :doctor:retired:person {name: "Dr. Clark", specialty: "pediatrics", `_SCHEMA`: "doctor"}) 
        WHERE id(dn) = $internal_id
        RETURN dn
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'dn': {'specialty': 'pediatrics', 'name': 'Dr. Clark', 'uri': uri, '_SCHEMA': "doctor"}}



def test_create_data_node_2(db):
    db.empty_dbase()

    # Using a class of type "strict"
    NeoSchema.create_class_with_properties(name="person",
                                           properties=["name", "age"], strict=True)


    # Create a "person" data node, attempting to set a property not declared in the Schema; this will fail
    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="person",
                                   properties={"name": "Joe", "address": "extraneous undeclared field"},
                                   extra_labels = None, new_uri=None,
                                   silently_drop=False)

    # To prevent a failure, we can ask to silently drop any undeclared property
    internal_id = NeoSchema.create_data_node(class_name="person",
                                             properties={"age": 22, "address": "extraneous undeclared field"},
                                             extra_labels = None, new_uri=None,
                                             silently_drop=True)
    q = '''
        MATCH (p :person {age: 22, `_SCHEMA`: "person"}) 
        WHERE id(p) = $internal_id
        RETURN p
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'p': {'age': 22, '_SCHEMA': "person"}}      # Notice that the address never made it into the database


    # Switch a new class, of type "lenient"
    NeoSchema.create_class_with_properties(name="car",
                                           properties=["brand"], strict=False)

    # Because the class is "lenient", data nodes may be created with undeclared properties
    internal_id = NeoSchema.create_data_node(class_name="car",
                                             properties={"brand": "Toyota", "color": "white"},
                                             extra_labels = None, new_uri=None,
                                             silently_drop=False)
    q = '''
        MATCH (c :car {brand: "Toyota", color: "white", `_SCHEMA`: "car"}) 
        WHERE id(c) = $internal_id
        RETURN c
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'c': {"brand": "Toyota", "color": "white", '_SCHEMA': "car"}}  # The color, though undeclared in the Schema, got set



def test_create_data_node_3(db):
    db.empty_dbase()

    NeoSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="No data nodes allowed")   # The Class doesn't allow data nodes


    class_internal_id , class_schema_uri = NeoSchema.create_class("Car", strict=True)

    assert NeoSchema.count_data_nodes_of_class("Car") == 0

    # Successfully adding the first data node
    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car")
    assert NeoSchema.count_data_nodes_of_class("Car") == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]   # No other properties were set


    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="Car",
                                   properties={"color": "No properties allowed"},
                                   silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 2nd data node
    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car",
                                                          properties={"color": "No properties allowed"},
                                                          silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class("Car") == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]   # No other properties were set


    # Successfully adding a 3rd data point
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["color"]) # Expand the allow class properties

    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car",
                                                          properties={"color": "white"})

    assert NeoSchema.count_data_nodes_of_class("Car") == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], 'color': 'white', '_SCHEMA': "Car"}]]   # This time the properties got set


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="Car",
                                   properties={"color": "white", "make": "Toyota"},
                                   silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 4th data point
    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car",
                                                          properties={"color": "red", "make": "VW"},
                                                          silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class("Car") == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], 'color': 'red', '_SCHEMA': "Car"}]]   # The "color" got set, while the "make" got dropped


    # Successfully adding a 5th data point
    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car",
                                                          properties={"color": "blue", "make": "Fiat", "year": 2000},
                                                          silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class("Car") == 5

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], 'color': 'blue', 'year': 2000, '_SCHEMA': "Car"}]]
    # The "color" and "year" got set, while the "make" got dropped


    # Successfully adding a 6th data point
    new_datanode_internal_id = NeoSchema.create_data_node(class_name="Car",
                                                          properties={"color": "green", "year": 2022},
                                                          silently_drop=False)

    assert NeoSchema.count_data_nodes_of_class("Car") == 6

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_internal_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_internal_id, 'neo4j_labels': ['Car'], 'color': 'green', 'year': 2022, '_SCHEMA': "Car"}]]
    # All properties got set



def test_create_data_node_4(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

     # Create a new data point, and get its Neo4j ID
    doctor_internal_id = NeoSchema.create_data_node(class_name="doctor",
                                                    properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Jill", "age": 22, "balance": 145.50},
                                   links={}
                                   )   # links must be a list


    # Create a new data node for a "patient", linked to the existing "doctor" data point (OUT-bound relationship)
    patient_internal_id = NeoSchema.create_data_node(class_name="patient",
                                                     properties={"name": "Jill", "age": 22, "balance": 145},
                                                     links=[{"internal_id": doctor_internal_id, "rel_name": "IS_ATTENDED_BY", "rel_dir": "OUT"}]
                                                     )

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145, `_SCHEMA`:"patient"})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine", `_SCHEMA`:"doctor"})
        WHERE id(d) = $doctor_internal_id AND id(p) = $patient_internal_id
        RETURN p, d
        '''
    result = db.query(q, data_binding={"doctor_internal_id": doctor_internal_id, "patient_internal_id": patient_internal_id})
    assert len(result) == 1


    # Create a new data node for a "result", linked to the existing "patient" data node;
    #   this time, also assign a "uri" to the new data node, and it's an IN-bound relationship
    result_internal_id = NeoSchema.create_data_node(class_name="result",
                                                    properties={"biomarker": "glucose", "value": 99},
                                                    links=[{"internal_id": patient_internal_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                    new_uri= "RESULT-1")
    q = '''
        MATCH 
        (p :patient {name: "Jill", age: 22, balance: 145, `_SCHEMA`:"patient"})
        -[:HAS_RESULT]->
        (r :result {biomarker: "glucose", value: 99, `_SCHEMA`:"result"})
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
    result2_internal_id = NeoSchema.create_data_node(class_name="result",
                                                     properties={"biomarker": "cholesterol", "value": 180},
                                                     links=[{"internal_id": patient_internal_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                     new_uri="RESULT-2")
    q = '''
        MATCH 
        (r1 :result {biomarker: "glucose", value: 99, `_SCHEMA`:"result"})
        <-[:HAS_RESULT]-
        (p :patient {name: "Jill", age: 22, balance: 145, `_SCHEMA`:"patient"})
        -[:HAS_RESULT]->
        (r2 :result {biomarker: "cholesterol", value: 180, `_SCHEMA`:"result"})
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
    patient_internal_id_2 = NeoSchema.create_data_node(class_name="patient",
                                                       properties={"name": "Jack", "age": 99, "balance": 8000},
                                                       links=[{"internal_id": doctor_internal_id,
                                                     "rel_name": "IS_ATTENDED_BY",
                                                     "rel_dir": "OUT",
                                                     "rel_attrs": {"since": 1999}
                                                    }]
                                                       )

    q = '''
        MATCH (p :patient {name: "Jack", age: 99, balance: 8000, `_SCHEMA`:"patient"})
        -[r :IS_ATTENDED_BY]-> 
        (d :doctor {name:"Dr. Preeti", specialty:"sports medicine", `_SCHEMA`:"doctor"})
        WHERE id(d) = $doctor_internal_id AND id(p) = $patient_internal_id
            AND r.since = 1999
        RETURN p, d
        '''
    result = db.query(q, data_binding={"doctor_internal_id": doctor_internal_id, "patient_internal_id": patient_internal_id_2})
    assert len(result) == 1


    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Spencer", "age": 55, "balance": 1200},
                                   links=[{"internal_id": -1,             # No such node exists
                                                     "rel_name": "IS_ATTENDED_BY"
                                                    }]
                                   )

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Spencer", "age": 55, "balance": 1200},
                                   links=666  # Not a list
                                   )

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Spencer", "age": 55, "balance": 1200},
                                   links=[{}]  # Missing required keys
                                   )

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Spencer", "age": 55, "balance": 1200},
                                   links=[{"internal_id": doctor_internal_id}]  # Missing required keys
                                   )

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_name="patient",
                                   properties={"name": "Spencer", "age": 55, "balance": 1200},
                                   links=[{"internal_id": doctor_internal_id,
                                                     "rel_name": "IS_ATTENDED_BY",
                                                     "unexpected_key": 666}]  # Unexpected key
                                   )

    assert NeoSchema.count_data_nodes_of_class("patient") == 2      # The 3rd patient node didn't get created by any of the failed calls

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
    NeoSchema.create_namespace(name="doctor", prefix ="doc-")
    uri = NeoSchema.reserve_next_uri(namespace="doctor")
    internal_id = NeoSchema.create_data_node(class_name="doctor",
                                             properties={"name": "Dr. Watson", "specialty": "pediatrics"},
                                             new_uri=uri)

    # The doctor is changing specialty...
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"specialty": "ob/gyn"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson", "specialty": "ob/gyn", "_SCHEMA": "doctor"}]


    # Completely drop the specialty field
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"specialty": ""}, drop_blanks = True)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson", "_SCHEMA": "doctor"}]


    # Turn the name value blank, but don't drop the field
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"name": ""}, drop_blanks = False)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "", "_SCHEMA": "doctor"}]


    # Set the name, this time locating the record by its URI
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"name": "Prof. Fleming"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "_SCHEMA": "doctor"}]


    # Add 2 extra fields: notice the junk leading/trailing blanks in the string
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"location": "     San Francisco     ", "retired": False})

    assert count == 2
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_SCHEMA": "doctor"}]


    # A vacuous "change" that doesn't actually do anything
    count = NeoSchema.update_data_node(data_node=uri, set_dict={})

    assert count == 0
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_SCHEMA": "doctor"}]


    # A "change" that doesn't actually change anything, but nonetheless is counted as 1 property set
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"location": "San Francisco"})
    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False, "_SCHEMA": "doctor"}]


    # A "change" that causes a field of blanks to get dropped
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"name": "        "}, drop_blanks = True)
    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "location": "San Francisco", "retired": False, "_SCHEMA": "doctor"}]



def test_add_data_node_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="I_dont_exist",
                                      properties={"junk": 123})     # No such class exists

    class_internal_id , _ = NeoSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="No data nodes allowed",
                                      properties={"junk": 123})   # The Class doesn't allow data nodes

    class_internal_id , class_schema_uri = NeoSchema.create_class("Car", strict=True)
    assert NeoSchema.count_data_nodes_of_class("Car") == 0

    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car", properties={})  # Properties are required

    with pytest.raises(Exception):
        # "color" is not a registered property of the Class "Car"
        NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})

    NeoSchema.add_properties_to_class(class_node = class_internal_id, property_list = ["color"])


    # Successfully adding the first data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]


    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car",
                                      properties={"make": "A property not currently allowed"})   # Trying to set a non-allowed property


    # The merging will use the already-existing data point, since the properties match up
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == False    # No new node was created

    assert NeoSchema.count_data_nodes_of_class("Car") == 1     # STILL at 1 datapoint

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]   # Same as before


    # Successfully adding a new (2nd) data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car",
                                      properties={"color": "white", "make": "Toyota"})   # Trying to set a non-allowed property

    # Successfully adding a 3rd data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "blue", "year": 2023})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2023, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]


    # Successfully adding a 4th data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "blue", "year": 2000})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}})  
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2000, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]
    # We can have 2 red blue because they differ in the other attribute (i.e. the year)


    # Nothing gets added now, because a "blue, 2000" car already exists
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "blue", "year": 2000})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 4     # UNCHANGED


    # Likewise, nothing gets added now, because a "red" car already exists
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "red"})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 4     # UNCHANGED


    # By contrast, a new data node gets added now, because the "mileage" field will now be kept, and there's no "red car from 1999"
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red", "year": 1999})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 5     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}})  
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]


    # Attempting to re-add the "red, 1999" car will have no effect...
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "red", "year": 1999})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 5     # UNCHANGED


    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["make"])
    # ... but there's no car "red, 1999, Toyota"
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red", "year": 1999, "make": "Toyota"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 6     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car {{`_SCHEMA`: "Car"}}) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'make': 'Toyota', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], '_SCHEMA': "Car"}]]


    # Now, set up an irregular scenario where there's a database node that will match the attributes and labels
    # of a Data Node to add, but is not itself a Data Node (it lacks a SCHEMA relationship to its Class)
    # This node will be ignored by the Schema layer, because it's not managed by it - and we can add just fine
    # a Data Node for a "yellow car"
    db.create_node(labels="Car", properties={"color": "yellow"})
    _, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "yellow"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class("Car") == 7     # Increased



def test_add_data_column_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        # No such class exists
        NeoSchema.add_data_column_merge(class_name="Car", property_name="color", value_list=["white"])

    NeoSchema.create_class_with_properties("Car", properties=["color", "year"],
                                           strict=True)
    assert NeoSchema.count_data_nodes_of_class("Car") == 0

    with pytest.raises(Exception):
        NeoSchema.add_data_column_merge(class_name="Car", property_name=123, value_list=["white"])      # property_name isn't a string

    with pytest.raises(Exception):
        NeoSchema.add_data_column_merge(class_name="Car", property_name="color", value_list="white")    # value_list isn't a list

    with pytest.raises(Exception):
        NeoSchema.add_data_column_merge(class_name="Car", property_name="color", value_list=[])    # value_list is empty


    # Expand the Schema
    result = NeoSchema.add_data_column_merge(class_name="Car",
                                             property_name="color", value_list=["red", "white", "blue"])

    with pytest.raises(Exception):
        NeoSchema.add_data_column_merge(class_name="Car",
                                        property_name="UNKNOWN", value_list=[1, 2])     # Property not in Schema Class

    # Successfully add 3 data points
    assert len(result["new_nodes"]) == 3
    assert len(result["old_nodes"]) == 0
    assert NeoSchema.count_data_nodes_of_class("Car") == 3


    # Only 1 of the following 3 data points isn't already in the database
    result = NeoSchema.add_data_column_merge(class_name="Car",
                                             property_name="color", value_list=["red", "green", "blue"])
    assert len(result["new_nodes"]) == 1
    assert len(result["old_nodes"]) == 2
    assert NeoSchema.count_data_nodes_of_class("Car") == 4

    id_green_car = result["new_nodes"][0]
    data_point = NeoSchema.search_data_node(internal_id=id_green_car)
    assert data_point["color"] == "green"


    # Successfully add the 2 distinct data points, from the 3 below, using a different field
    result = NeoSchema.add_data_column_merge(class_name="Car",
                                             property_name="year", value_list=[2003, 2022, 2022])
    assert len(result["new_nodes"]) == 2
    assert len(result["old_nodes"]) == 1
    assert NeoSchema.count_data_nodes_of_class("Car") == 6



def test_register_existing_data_point(db):
    pass    # TODO



def test_delete_data_nodes(db):
    db.empty_dbase()

    result = NeoSchema.delete_data_nodes(node_id = 1)     # Non-existing node (database just got cleared)
    assert result == 0

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create new data nodes
    doctor_internal_id = NeoSchema.create_data_node(class_name="doctor",
                                                    properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    patient_internal_id = NeoSchema.create_data_node(class_name="patient",
                                                     properties={"name": "Val", "age": 22})

    NeoSchema.create_data_node(class_name="result", properties={"biomarker": "insulin ", "value": 10})
    NeoSchema.create_data_node(class_name="result", properties={"biomarker": "bilirubin ", "value": 1})

    doctor = NeoSchema.search_data_node(internal_id=doctor_internal_id)
    assert doctor == {'name': 'Dr. Preeti', 'specialty': 'sports medicine'}

    patient = NeoSchema.search_data_node(internal_id=patient_internal_id)
    assert patient == {'name': 'Val', 'age': 22}

    assert NeoSchema.count_data_nodes_of_class("result") == 2


    # Now delete some of the data nodes we created
    with pytest.raises(Exception):
        NeoSchema.delete_data_nodes(node_id = -1)    # Invalid node ID

    result = NeoSchema.delete_data_nodes(node_id=doctor_internal_id)
    assert result == 1
    doctor = NeoSchema.search_data_node(internal_id=doctor_internal_id)
    assert doctor is None       # The doctor got deleted

    result = NeoSchema.delete_data_nodes(node_id='Liz', id_key='name')  # Non-existent node
    assert result == 0
    patient = NeoSchema.search_data_node(internal_id=patient_internal_id)
    assert patient == {'name': 'Val', 'age': 22}        # Still there

    result = NeoSchema.delete_data_nodes(node_id='Val', id_key='name')  # Correct node
    assert result == 1
    patient = NeoSchema.search_data_node(internal_id=patient_internal_id)
    assert patient is None      # The patient got deleted

    result = NeoSchema.delete_data_nodes(class_name="result", node_id='LDL', id_key='biomarker')
    assert result == 0          # No matches
    assert NeoSchema.count_data_nodes_of_class("result") == 2   # Still there

    result = NeoSchema.delete_data_nodes(class_name="result")
    assert result == 2          # Both results got deleted
    assert NeoSchema.count_data_nodes_of_class("result") == 0   # No results found



def test_add_data_relationship_hub(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties("City", properties=["name"])
    NeoSchema.create_class_with_properties("State", properties=["name"])

    # Set up the Data Nodes (2 cities and a state)
    berkeley = NeoSchema.create_data_node(class_name="City", properties = {"name": "Berkeley"})
    san_diego = NeoSchema.create_data_node(class_name="City", properties = {"name": "San Diego"})
    california = NeoSchema.create_data_node(class_name="State", properties = {"name": "California"})

    with pytest.raises(Exception):
        # Trying to create a data relationship not yet declared in the Schema
        NeoSchema.add_data_relationship_hub(center_id=california, periphery_ids=[berkeley, san_diego], periphery_class="City",
                                            rel_name="LOCATED_IN", rel_dir="IN")

    # Declare the "LOCATED_IN" relationship in the Schema
    NeoSchema.create_class_relationship(from_class="City", to_class="State", rel_name="LOCATED_IN")

    number_rels = NeoSchema.add_data_relationship_hub(center_id=california, periphery_ids=[berkeley, san_diego], periphery_class="City",
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
    nevada = NeoSchema.create_data_node(class_name="State", properties = {"name": "Nevada"})
    oregon = NeoSchema.create_data_node(class_name="State", properties = {"name": "Oregon"})

    with pytest.raises(Exception):
        # Trying to create a data relationship not yet declared in the Schema
        NeoSchema.add_data_relationship_hub(center_id=california, periphery_ids=[nevada, oregon], periphery_class="State",
                                            rel_name="BORDERS_WITH", rel_dir="OUT")

    # Declare the "BORDERS_WITH" relationship in the Schema
    NeoSchema.create_class_relationship(from_class="State", to_class="State", rel_name="BORDERS_WITH")

    number_rels = NeoSchema.add_data_relationship_hub(center_id=california,
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
        NeoSchema.add_data_relationship(from_id=123, to_id=456, rel_name="junk")  # No such nodes exist

    neo_uri_1 = db.create_node("random A")
    neo_uri_2 = db.create_node("random B")
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=neo_uri_1, to_id=neo_uri_2, rel_name="junk") # Not data nodes with a Schema

    _ , person_class_uri = NeoSchema.create_class("Person", strict=True)
    person_internal_id = NeoSchema.create_data_node(class_name="Person", new_uri="julian")

    _ , car_class_uri = NeoSchema.create_class("Car")
    car_internal_id = NeoSchema.create_data_node(class_name="Car", properties={"color": "white"})

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")

    # Add the "DRIVE" relationship between the Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="DRIVES")


    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name=None)  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=car_internal_id, to_id=person_internal_id, rel_name="DRIVES")  # Wrong direction

    # Now, adding the data relationship will work
    NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")
    assert db.links_exist(match_from=person_internal_id, match_to=car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship(from_id=person_internal_id, to_id=car_internal_id, rel_name="SOME_OTHER_NAME")


    # Now add reverse a relationship between the Classes
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_DRIVEN_BY")

    # Add that same reverse relationship between the data nodes
    NeoSchema.add_data_relationship(from_id=car_internal_id, to_id=person_internal_id, rel_name="IS_DRIVEN_BY")
    assert db.links_exist(match_from=car_internal_id, match_to=person_internal_id, rel_name="IS_DRIVEN_BY")

    # Now add a relationship using URI's instead of internal database ID's
    red_car_internal_id = NeoSchema.create_data_node(class_name="Car", properties={"color": "red"}, new_uri="new_car")
    NeoSchema.add_data_relationship(from_id="julian", to_id="new_car", id_type="uri", rel_name="DRIVES")
    assert db.links_exist(match_from=person_internal_id, match_to=red_car_internal_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship(from_id="julian", to_id="new_car", id_type="uri", rel_name="PAINTS")



def test_remove_data_relationship(db):
    pass    # TODO



def test_class_of_data_point(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.class_of_data_node(node_id=123)  # No such data node exists

    internal_id = db.create_node("random")
    with pytest.raises(Exception):
        NeoSchema.class_of_data_node(node_id=internal_id)     # It's not a data node

    NeoSchema.create_class("Person")
    uri = NeoSchema.reserve_next_uri()      # Obtain (and reserve) the next auto-increment value
    NeoSchema.create_data_node(class_name="Person", new_uri=uri)

    assert NeoSchema.class_of_data_node(node_id=uri, id_key="uri") == "Person"
    assert NeoSchema.class_of_data_node(node_id=uri, id_key="uri", labels="Person") == "Person"

    # Now locate thru the internal database ID
    internal_id = NeoSchema.get_data_node_id(uri)
    #print("neo_uri: ", neo_uri)
    assert NeoSchema.class_of_data_node(node_id=internal_id) == "Person"

    NeoSchema.create_class("Extra")
    # Create a forbidden scenario with a data node having 2 Schema classes
    q = f'''
        MATCH (n {{uri: '{uri}' }})
        SET n.`_SCHEMA` = 666
        '''
    #db.debug_print(q, {}, "test")
    db.update_query(q)
    with pytest.raises(Exception):
        NeoSchema.class_of_data_node(node_id=uri, id_key="uri")    # Data node is associated to a non-string class name




#############   DATA IMPORT   ###########

# See separate file


#############   EXPORT SCHEMA   ###########


###############   URI'S   ###############

def test_namespace_exists(db):
    db.empty_dbase()

    assert not NeoSchema.namespace_exists("image")
    NeoSchema.create_namespace(name="junk")
    assert not NeoSchema.namespace_exists("image")

    NeoSchema.create_namespace(name="image")
    assert NeoSchema.namespace_exists("image")



def test_create_namespace(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.create_namespace(name=123)

    with pytest.raises(Exception):
        NeoSchema.create_namespace(name="")

    NeoSchema.create_namespace(name="photo")
    q = "MATCH (n:`Schema Autoincrement`) RETURN n"
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["n"] == {"namespace": "photo", "next_count": 1}

    with pytest.raises(Exception):
        NeoSchema.create_namespace(name="photo")    # Already exists


    NeoSchema.create_namespace(name="note", prefix="n-", suffix=".new")
    q = "MATCH (n:`Schema Autoincrement` {namespace: 'note'}) RETURN n"
    result = db.query(q)
    assert len(result) == 1
    assert result[0]["n"] == {"namespace": "note", "next_count": 1, "prefix": "n-", "suffix": ".new"}



def test_reserve_next_uri(db):
    db.empty_dbase()

    NeoSchema.create_namespace(name="data_node")   # Accept default blank prefix/suffix
    assert NeoSchema.reserve_next_uri(namespace="data_node") == "1"   # Accept default blank prefix/suffix
    assert NeoSchema.reserve_next_uri("data_node") == "2"
    assert NeoSchema.reserve_next_uri("data_node") == "3"
    assert NeoSchema.reserve_next_uri(namespace="data_node", prefix="i-") == "i-4"        # Force a prefix
    assert NeoSchema.reserve_next_uri(namespace="data_node", suffix=".jpg") == "5.jpg"    # Force a suffix
    assert NeoSchema.reserve_next_uri("data_node") == "6"
    assert NeoSchema.reserve_next_uri() == "7"    # default namespace

    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace="notes")   # Namespace doesn't exist yet

    NeoSchema.create_namespace(name="notes", prefix="n-")
    assert NeoSchema.reserve_next_uri(namespace="notes") == "n-1"
    assert NeoSchema.reserve_next_uri(namespace="notes", prefix="n-") == "n-2"    # Redundant specification of prefix
    assert NeoSchema.reserve_next_uri(namespace="notes") == "n-3"                 # No need to specify the prefix (stored)

    NeoSchema.create_namespace(name="schema_node", prefix="schema-")
    assert NeoSchema.reserve_next_uri(namespace="schema_node") == "schema-1"
    assert NeoSchema.reserve_next_uri(namespace="schema_node") == "schema-2"

    NeoSchema.create_namespace(name="documents", prefix="d-", suffix="")
    assert NeoSchema.reserve_next_uri("documents", prefix="d-", suffix="") == "d-1"
    assert NeoSchema.reserve_next_uri("documents", prefix="d-") == "d-2"
    assert NeoSchema.reserve_next_uri("documents", prefix="doc.", suffix=".new") == "doc.3.new"

    NeoSchema.create_namespace(name="images", prefix="i_", suffix=".jpg")
    assert NeoSchema.reserve_next_uri("images", prefix="i_", suffix=".jpg") == "i_1.jpg"
    assert NeoSchema.reserve_next_uri("images", prefix="i_") == "i_2.jpg"
    assert NeoSchema.reserve_next_uri("documents") == "d-4"     # It remembers the original prefix
    assert NeoSchema.reserve_next_uri("documents", suffix="/view") == "d-5/view"
    assert NeoSchema.reserve_next_uri("documents") == "d-6"
    assert NeoSchema.reserve_next_uri("documents", prefix=None, suffix=None) == "d-7"

    with pytest.raises(Exception):
        assert NeoSchema.reserve_next_uri(123)    # Not a string

    with pytest.raises(Exception):
        assert NeoSchema.reserve_next_uri("       ")
    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace=123)

    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace="     ")

    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace="schema_node", prefix=666)

    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace="schema_node", suffix=["what is this"])



def test_advance_autoincrement(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.reserve_next_uri(namespace="a")   # Namespace doesn't exist yet

    NeoSchema.create_namespace("a")
    NeoSchema.create_namespace("schema", suffix=".test")
    NeoSchema.create_namespace("documents", prefix="d-")
    NeoSchema.create_namespace("image", prefix="im-", suffix="-large")

    assert NeoSchema.advance_autoincrement("a") == (1, "", "")
    assert NeoSchema.advance_autoincrement("a") == (2, "", "")
    assert NeoSchema.advance_autoincrement("schema") == (1, "", ".test")
    assert NeoSchema.advance_autoincrement("schema") == (2, "", ".test")
    assert NeoSchema.advance_autoincrement("a") == (3, "", "")
    assert NeoSchema.advance_autoincrement("documents") == (1, "d-", "")
    assert NeoSchema.advance_autoincrement("documents") == (2, "d-", "")

    # The following line will "reserve" the values 3 and 4
    assert NeoSchema.advance_autoincrement("documents", advance=2) == (3, "d-", "")
    assert NeoSchema.advance_autoincrement("documents") == (5, "d-", "")

    # The following line will "reserve" the values 1 thru 10
    assert NeoSchema.advance_autoincrement("image", advance=10) == (1, "im-", "-large")
    assert NeoSchema.advance_autoincrement("image") == (11, "im-", "-large")
    assert NeoSchema.advance_autoincrement("          image   ") == (12, "im-", "-large") # Leading/trailing blanks are ignored

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(123)    # Not a string

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement("        ")

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(namespace ="a", advance ="not an integer")

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(namespace ="a", advance = 0)  # Advance isn't >= 1





###############   UTILITY  METHODS   ###############

def test_is_valid_schema_uri(db):
    db.empty_dbase()
    _ , uri = NeoSchema.create_class("Records")
    assert NeoSchema.is_valid_schema_uri(uri)

    assert not NeoSchema.is_valid_schema_uri("")
    assert not NeoSchema.is_valid_schema_uri("      ")
    assert not NeoSchema.is_valid_schema_uri("abc")
    assert not NeoSchema.is_valid_schema_uri(123)
    assert not NeoSchema.is_valid_schema_uri(None)

    assert NeoSchema.is_valid_schema_uri("schema-123")
    assert not NeoSchema.is_valid_schema_uri("schema-")
    assert not NeoSchema.is_valid_schema_uri("schema-zzz")
    assert not NeoSchema.is_valid_schema_uri("schema123")



def test__prepare_data_node_labels(db):
    with pytest.raises(Exception):
        NeoSchema._prepare_data_node_labels(class_name=123)     # Bad name

    with pytest.raises(Exception):
        NeoSchema._prepare_data_node_labels(class_name="  Leading_Trailing_Blanks  ")

    assert NeoSchema._prepare_data_node_labels(class_name="Car") == ["Car"]

    with pytest.raises(Exception):
        NeoSchema._prepare_data_node_labels(class_name="Car", extra_labels=123)  # Bad extra_labels

    assert NeoSchema._prepare_data_node_labels(class_name="Car", extra_labels=" BA ") == ["Car", "BA"]

    assert NeoSchema._prepare_data_node_labels(class_name="Car", extra_labels=[" Motor Vehicle"]) \
           == ["Car", "Motor Vehicle"]

    assert NeoSchema._prepare_data_node_labels(class_name="Car", extra_labels=(" Motor Vehicle", "  Object    ")) \
           == ["Car", "Motor Vehicle", "Object"]

    assert NeoSchema._prepare_data_node_labels(class_name="Car", extra_labels=[" Motor Vehicle", "  Object    ", "Motor Vehicle"]) \
           == ["Car", "Motor Vehicle", "Object"]



def test_prepare_match_cypher_clause():
    result = NeoSchema.prepare_match_cypher_clause(node_id=123)
    assert result[0] == ""
    assert result[1] == "WHERE id(dn) = $node_id"
    assert result[2] == {"node_id": 123}

    result = NeoSchema.prepare_match_cypher_clause(node_id="c-88", id_key="uri")
    assert result[0] == ""
    assert result[1] == "WHERE dn.`uri` = $node_id"
    assert result[2] == {"node_id": "c-88"}

    result = NeoSchema.prepare_match_cypher_clause(node_id=3, id_key="dimension")
    assert result[0] == ""
    assert result[1] == "WHERE dn.`dimension` = $node_id"
    assert result[2] == {"node_id": 3}

    result = NeoSchema.prepare_match_cypher_clause(class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE dn.`_SCHEMA` = $class_name"
    assert result[2] == {"class_name": "Car"}

    result = NeoSchema.prepare_match_cypher_clause(node_id=123, class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE id(dn) = $node_id AND dn.`_SCHEMA` = $class_name"
    assert result[2] == {"node_id": 123, "class_name": "Car"}

    result = NeoSchema.prepare_match_cypher_clause(node_id="c-88", id_key="uri", class_name="Car")
    assert result[0] == ":`Car`"
    assert result[1] == "WHERE dn.`uri` = $node_id AND dn.`_SCHEMA` = $class_name"
    assert result[2] == {"node_id": "c-88", "class_name": "Car"}

    with pytest.raises(Exception):
        NeoSchema.prepare_match_cypher_clause()     # No arguments

    with pytest.raises(Exception):
        NeoSchema.prepare_match_cypher_clause(id_key="uri") # Missing arg `node_id`

    with pytest.raises(Exception):
        NeoSchema.prepare_match_cypher_clause(node_id=123, id_key=456)  # id_key, if present, must be a str