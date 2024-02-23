# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema, SchemaCache


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
                                                            property_list=["name", "age", "balance"])

    result_id, _  = NeoSchema.create_class_with_properties(name="result",
                                                           property_list=["biomarker", "value"])

    doctor_id, _  = NeoSchema.create_class_with_properties(name="doctor",
                                                           property_list=["name", "specialty"])

    NeoSchema.create_class_relationship(from_class="patient", to_class="result", rel_name="HAS_RESULT")
    NeoSchema.create_class_relationship(from_class="patient", to_class="doctor", rel_name="IS_ATTENDED_BY")

    return {"patient": patient_id, "result": result_id, "doctor": doctor_id}



def create_sample_schema_2():
    # Class "quotes" with relationship named "in_category" to Class "categories";
    # each Class has some properties
    _, sch_1 = NeoSchema.create_class_with_properties(name="quotes",
                                                      property_list=["quote", "attribution", "verified"])

    _, sch_2 = NeoSchema.create_class_with_properties(name="categories",
                                                      property_list=["name", "remarks"])

    NeoSchema.create_class_relationship(from_class="quotes", to_class="categories", rel_name="in_category")

    return {"quotes": sch_1, "categories": "sch_2"}




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

    q = f'''MATCH 
        (from :CLASS {{name:"French Vocabulary", uri: '{french_uri}'}})
        -[:INSTANCE_OF]
        ->(to :CLASS {{name:"Foreign Vocabulary", uri: '{foreign_uri}'}})
        <-[:INSTANCE_OF]-(:CLASS {{name:"German Vocabulary"}})
        WHERE id(from) = {french_id} AND id(to) = {foreign_id}
        RETURN count(from) AS number_found
        '''

    assert db.query(q, single_cell="number_found") == 1



def test_rename_class_rel(db):
    pass    # TODO



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
    NeoSchema.add_data_point_OLD(class_name="quotes",
                                 data_dict={"quote": "Comparison is the thief of joy"})

    NeoSchema.delete_class("categories")    # No problem in deleting this Class with no attached data nodes
    assert NeoSchema.class_name_exists("quotes")
    assert not NeoSchema.class_name_exists("categories")

    with pytest.raises(Exception):
        NeoSchema.delete_class("quotes")    # But cannot by default delete Classes with data nodes

    NeoSchema.delete_class("quotes", safe_delete=False)     # Over-ride default protection mechanism

    q = '''
    MATCH (d :quotes)
    WHERE NOT EXISTS ((d)-[:SCHEMA]->())
    RETURN count(d) AS number_orphaned
    '''
    assert db.query(q, single_cell="number_orphaned") == 1  # Now there's an "orphaned" data node



def test_is_strict_class(db):
    db.empty_dbase()

    internal_id , _ = NeoSchema.create_class("I am strict", strict=True)
    assert NeoSchema.is_strict_class(internal_id)

    internal_id , _ = NeoSchema.create_class("I am lax", strict=False)
    assert not NeoSchema.is_strict_class(internal_id)



def test_allows_data_nodes(db):
    db.empty_dbase()

    int_id_yes , _ = NeoSchema.create_class("French Vocabulary")
    assert NeoSchema.allows_data_nodes(class_name="French Vocabulary") == True
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_yes) == True

    int_id_no , _ = NeoSchema.create_class("Vocabulary", no_datanodes = True)
    assert NeoSchema.allows_data_nodes(class_name="Vocabulary") == False
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_no) == False

    # Tests using Schema Caching
    schema_cache = SchemaCache()
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_yes, schema_cache=schema_cache) == True
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_no, schema_cache=schema_cache) == False
    # Repeat
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_yes, schema_cache=schema_cache) == True
    assert NeoSchema.allows_data_nodes(class_internal_id=int_id_no, schema_cache=schema_cache) == False



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

    assert NeoSchema.get_class_relationships(class_name="patient", link_dir="OUT") == ["HAS_RESULT", "IS_ATTENDED_BY"]
    assert NeoSchema.get_class_relationships(class_name="patient", link_dir="IN") == []

    assert NeoSchema.get_class_relationships(class_name="doctor", link_dir="OUT") == []
    assert NeoSchema.get_class_relationships(class_name="doctor", link_dir="IN") == ["IS_ATTENDED_BY"]

    assert NeoSchema.get_class_relationships(class_name="result", link_dir="OUT") == []
    assert NeoSchema.get_class_relationships(class_name="result", link_dir="IN") == ["HAS_RESULT"]

    #TODO: test the omit_instance argument




#############   PROPERTIES-RELATED   #############


def test_get_class_properties(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.create_class_with_properties(111)    # Invalid class name

    NeoSchema.create_class_with_properties("My first class", property_list=["A", "B", "C"])
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
        # Meaningless combination of arguments
        NeoSchema.get_class_properties("My first class", include_ancestors=False, sort_by_path_len="ASC")

    with pytest.raises(Exception):
        NeoSchema.get_class_properties("My first class", include_ancestors=True, sort_by_path_len="meaningless")

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


    NeoSchema.create_class_with_properties("German Vocabulary", ["German"], strict=True)
    assert NeoSchema.is_property_allowed(property_name="German", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")

    # "notes" and "English" are Properties of the more general "Foreign Vocabulary" Class,
    # of which "German Vocabulary" is an instance
    NeoSchema.create_class_with_properties("Foreign Vocabulary", ["English", "notes"], strict=True)
    NeoSchema.create_class_relationship(from_class="German Vocabulary", to_class="Foreign Vocabulary", rel_name="INSTANCE_OF")

    assert NeoSchema.is_property_allowed(property_name="notes", class_name="German Vocabulary")
    assert NeoSchema.is_property_allowed(property_name="English", class_name="German Vocabulary")
    assert not NeoSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")

    NeoSchema.create_class_with_properties("Content Item", ["uri"], strict=True)
    NeoSchema.create_class_relationship(from_class="Foreign Vocabulary", to_class="Content Item", rel_name="INSTANCE_OF")

    assert NeoSchema.is_property_allowed(property_name="uri", class_name="German Vocabulary")   # "uri" is now available thru ancestry



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


    # Repeating, using the SchemaCache
    schema_cache = SchemaCache()

    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri, schema_cache=schema_cache,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri, schema_cache=schema_cache,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped


    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123}  # "C" got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_internal_id=strict_int_uri, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=False)


    d = NeoSchema.allowable_props(class_internal_id=lax_int_uri, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"X": 666, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_internal_id=strict_int_uri, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {}      # Everything got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_internal_id=strict_int_uri, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=False)

    # Check the internal data structure of the schema cache
    cached_data = schema_cache.get_all_cached_class_data(lax_int_uri)
    assert cached_data["class_attributes"] == {"name": "My Lax class", "uri": lax_schema_uri, "strict": False}
    cached_data = schema_cache.get_all_cached_class_data(strict_int_uri)
    assert cached_data["class_attributes"] == {"name": "My Strict class", "uri": strict_schema_uri, "strict": True}



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



#############   DATA POINTS   ###########

def test_all_properties(db):
    pass    # TODO


def test_fetch_data_point(db):
    pass    # TODO



def test_data_points_of_class(db):
    pass    # TODO



def test_count_data_points_of_class(db):

    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.count_data_nodes_of_class(666)   # Non-existent Class

    class_internal_id_1 , _ = NeoSchema.create_class("Some class")

    assert NeoSchema.count_data_nodes_of_class(class_internal_id_1) == 0

    NeoSchema.create_data_node(class_node=class_internal_id_1)
    assert NeoSchema.count_data_nodes_of_class(class_internal_id_1) == 1

    NeoSchema.create_data_node(class_node=class_internal_id_1)
    assert NeoSchema.count_data_nodes_of_class(class_internal_id_1) == 2


    class_internal_id_2 , _ = NeoSchema.create_class("Another class")

    assert NeoSchema.count_data_nodes_of_class(class_internal_id_2) == 0

    NeoSchema.create_data_node(class_node=class_internal_id_2)
    assert NeoSchema.count_data_nodes_of_class(class_internal_id_2) == 1

    assert NeoSchema.count_data_nodes_of_class(class_internal_id_1) == 2   # Where we left it off



def test_data_points_lacking_schema(db):
    pass    # TODO



def test_get_data_point_uri(db):
    pass    # TODO



def test_create_data_node_1(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a 1st "doctor" data node
    internal_id = NeoSchema.create_data_node(class_node="doctor",
                                             properties={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                             extra_labels = None,
                                             new_uri=None, silently_drop=False)

    q = '''
        MATCH (d :doctor {name: "Dr. Preeti", specialty: "sports medicine"}) 
        -[:SCHEMA]-> (:CLASS {name: "doctor"})
        WHERE id(d) = $internal_id
        RETURN d
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'d': {'specialty': 'sports medicine', 'name': 'Dr. Preeti'}}


    # Create a 2nd "doctor" data node, this time assigning an extra label and storing a URI
    uri = "doc-1"
    internal_id = NeoSchema.create_data_node(class_node="doctor",
                                             properties={"name": "Dr. Watson", "specialty": "genetics"},
                                             extra_labels = "Nobelist",
                                             new_uri=uri, silently_drop=False)

    q = '''
        MATCH (d :doctor:Nobelist {name: "Dr. Watson", specialty: "genetics"}) 
        -[:SCHEMA]-> (:CLASS {name: "doctor"})
        WHERE id(d) = $internal_id
        RETURN d
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'d': {'specialty': 'genetics', 'name': 'Dr. Watson', 'uri': uri}}


    # Create a 3rd "doctor" data node, this time assigning 2 extra labels and also assigning a URI
    uri = "d-123"
    internal_id = NeoSchema.create_data_node(class_node="doctor",
                                                    properties={"name": "Dr. Lewis", "specialty": "radiology"},
                                                    extra_labels = ["retired", "person"],
                                                    new_uri=uri, silently_drop=False)

    q = '''
        MATCH (d :doctor:retired:person {name: "Dr. Lewis", specialty: "radiology"}) 
        -[:SCHEMA]-> (:CLASS {name: "doctor"})
        WHERE id(d) = $internal_id
        RETURN d
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'d': {'specialty': 'radiology', 'name': 'Dr. Lewis', 'uri': uri}}


    # Create a 4th "doctor" data node, this time using a tuple rather than a list to assign 2 extra labels
    uri = "d-999"
    internal_id = NeoSchema.create_data_node(class_node="doctor",
                                                properties={"name": "Dr. Clark", "specialty": "pediatrics"},
                                                extra_labels = ("retired", "person"),
                                                new_uri=uri, silently_drop=False)

    q = '''
        MATCH (d :doctor:retired:person {name: "Dr. Clark", specialty: "pediatrics"}) 
        -[:SCHEMA]-> (:CLASS {name: "doctor"})
        WHERE id(d) = $internal_id
        RETURN d
        '''
    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1

    assert result[0] == {'d': {'specialty': 'pediatrics', 'name': 'Dr. Clark', 'uri': uri}}



def test_create_data_node_2(db):
    db.empty_dbase()

    # Using a class of type "strict"
    NeoSchema.create_class_with_properties(name="person",
                                           property_list=["name", "age"], strict=True)

    # Create a "person" data node, attempting to set a property not declared in the Schema; this will fail
    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_node="person",
                                   properties={"name": "Joe", "address": "extraneous undeclared field"},
                                   extra_labels = None, new_uri=None,
                                   silently_drop=False)

    # To prevent a failure, we can ask to silently drop any undeclared property
    internal_id = NeoSchema.create_data_node(class_node="person",
                                             properties={"age": 22, "address": "extraneous undeclared field"},
                                             extra_labels = None, new_uri=None,
                                             silently_drop=True)
    q = '''
        MATCH (p :person {age: 22}) 
        -[:SCHEMA]-> (:CLASS {name: 'person'})
        WHERE id(p) = $internal_id
        RETURN p
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'p': {'age': 22}}      # Notice that the address never made it into the database


    # Switch a new class, of type "lenient"
    NeoSchema.create_class_with_properties(name="car",
                                           property_list=["brand"], strict=False)

    # Because the class is "lenient", data nodes may be created with undeclared properties
    internal_id = NeoSchema.create_data_node(class_node="car",
                                             properties={"brand": "Toyota", "color": "white"},
                                             extra_labels = None, new_uri=None,
                                             silently_drop=False)
    q = '''
        MATCH (c :car {brand: "Toyota", color: "white"}) 
        -[:SCHEMA]-> (:CLASS {name: 'car'})
        WHERE id(c) = $internal_id
        RETURN c
        '''

    result = db.query(q, data_binding={"internal_id": internal_id})
    assert len(result) == 1
    assert result[0] == {'c': {"brand": "Toyota", "color": "white"}}  # The color, though undeclared in the Schema, got set



def test_create_data_node_3(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_node=123)     # No such class exists

    class_internal_id , _ = NeoSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_node=class_internal_id)   # The Class doesn't allow data nodes


    class_internal_id , class_schema_uri = NeoSchema.create_class("Car", strict=True)

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 0

    # Successfully adding the first data point
    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id)
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car']}]]   # No other properties were set


    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_node=class_internal_id,
                                   properties={"color": "No properties allowed"},
                                   silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 2nd data point
    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id,
                                                    properties={"color": "No properties allowed"},
                                                    silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car']}]]   # No other properties were set


    # Successfully adding a 3rd data point
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["color"]) # Expand the allow class properties

    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id,
                                                    properties={"color": "white"})

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car'], 'color': 'white'}]]   # This time the properties got set


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.create_data_node(class_node=class_internal_id,
                                   properties={"color": "white", "make": "Toyota"},
                                   silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 4th data point
    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id,
                                                    properties={"color": "red", "make": "VW"},
                                                    silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car'], 'color': 'red'}]]   # The "color" got set, while the "make" got dropped


    # Successfully adding a 5th data point
    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id,
                                                    properties={"color": "blue", "make": "Fiat", "year": 2000},
                                                    silently_drop=True)

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 5

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car'], 'color': 'blue', 'year': 2000}]]
    # The "color" and "year" got set, while the "make" got dropped


    # Successfully adding a 6th data point
    new_datanode_uri = NeoSchema.create_data_node(class_node=class_internal_id,
                                                    properties={"color": "green", "year": 2022},
                                                    silently_drop=False)

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 6

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_uri}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_uri, 'neo4j_labels': ['Car'], 'color': 'green', 'year': 2022}]]
    # All properties got set



def test_update_data_node(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a "doctor" data node
    uri = NeoSchema.reserve_next_uri(prefix ="doc-", namespace="doctor")
    internal_id = NeoSchema.create_data_node(class_node="doctor",
                                             properties={"name": "Dr. Watson", "specialty": "pediatrics"},
                                             new_uri=uri)

    # The doctor is changing specialty...
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"specialty": "ob/gyn"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson", "specialty": "ob/gyn"}]


    # Completely drop the specialty field
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"specialty": ""}, drop_blanks = True)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": "Dr. Watson"}]


    # Turn the name value blank, but don't drop the field
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"name": ""}, drop_blanks = False)

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "name": ""}]


    # Change the URI field      (TODO: in the future, this will happen automatically, and "uri" will become "uri"
    count = NeoSchema.update_data_node(data_node=internal_id, set_dict={"uri": uri})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "uri": uri, "name": ""}]


    # Set the name, this time locating the record by its URI
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"name": "Prof. Fleming"})

    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "uri": uri, "name": "Prof. Fleming"}]


    # Add 2 extra fields
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"location": "San Francisco", "retired": False})

    assert count == 2
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "uri": uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False}]


    # A vacuous "change" that doesn't actually do anything
    count = NeoSchema.update_data_node(data_node=uri, set_dict={})

    assert count == 0
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "uri": uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False}]


    # A "change" that doesn't actually change anything, but nonetheless is counted as 1 property set
    count = NeoSchema.update_data_node(data_node=uri, set_dict={"location": "San Francisco"})
    assert count == 1
    result = db.get_nodes(match=internal_id,
                          return_internal_id=False, return_labels=False)
    assert result == [{'uri': uri, "uri": uri, "name": "Prof. Fleming", "location": "San Francisco", "retired": False}]



def test_add_data_point_with_links(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its Neo4j ID
    doctor_neo_uri = NeoSchema.add_data_node_with_links(class_name="doctor",
                                                       properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    q = '''
        MATCH (d:doctor {name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]->(c:CLASS {name: "doctor"})
        WHERE id(d) = $doctor_neo_uri
        RETURN d, c
        '''
    result = db.query(q, data_binding={"doctor_neo_uri": doctor_neo_uri})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c"]["name"] == "doctor"
    assert record["d"] == {"name":"Dr. Preeti", "specialty":"sports medicine"}

    with pytest.raises(Exception):
        NeoSchema.add_data_node_with_links(class_name="patient",
                                           properties={"name": "Jill", "age": 22, "balance": 145.50},
                                           links={}
                                           )   # links must be a list
        NeoSchema.add_data_node_with_links(class_name="patient",
                                           properties="NOT a dict",
                                           links={}
                                           )   # properties must be a dict
        NeoSchema.add_data_node_with_links(class_name="",
                                           properties={},
                                           links={}
                                           )   # class_name cannot be empty

    # Create a new data point for a "patient", linked to the existing "doctor" data point
    patient_neo_uri = NeoSchema.add_data_node_with_links(class_name="patient",
                                                        properties={"name": "Jill", "age": 22, "balance": 145.50},
                                                        links=[{"internal_id": doctor_neo_uri, "rel_name": "IS_ATTENDED_BY", "rel_dir": "OUT"}]
                                                        )

    q = '''
        MATCH (cp:CLASS {name: "patient"})<-[:SCHEMA]
        - (p :patient {name: "Jill", age: 22, balance: 145.50})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine"})
        -[:SCHEMA]->(cd:CLASS {name: "doctor"})<-[:IS_ATTENDED_BY]-(cp)
        WHERE id(d) = $doctor_neo_uri AND id(p) = $patient_neo_uri
        RETURN p, d, cp, cd
        '''
    result = db.query(q, data_binding={"doctor_neo_uri": doctor_neo_uri, "patient_neo_uri": patient_neo_uri})
    assert len(result) == 1


    # Create a new data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of an autoincrement "uri" to the new data node
    result_neo_uri = NeoSchema.add_data_node_with_links(class_name="result",
                                                       properties={"biomarker": "glucose", "value": 99.0},
                                                       links=[{"internal_id": patient_neo_uri, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                       assign_uri= True)

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r :result {biomarker: "glucose", value: 99.0})
        WHERE id(p) = $patient_neo_uri AND id(r) = $result_neo_uri
        RETURN p, cp, cr, r
        '''
    result = db.query(q, data_binding={"patient_neo_uri": patient_neo_uri,
                                       "result_neo_uri": result_neo_uri
                                       })
    assert len(result) == 1
    record = result[0]
    assert record['r']['uri'] == "1"  # The first auto-increment value


    # Create a 2nd data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of specific "uri" to the new data node
    result2_neo_uri = NeoSchema.add_data_node_with_links(class_name="result",
                                                        properties={"biomarker": "cholesterol", "value": 180.0},
                                                        links=[{"internal_id": patient_neo_uri, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                        new_uri="my-uri")
    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r2 :result {biomarker: "cholesterol", value: 180.0})
        WHERE id(p) = $patient_neo_uri AND id(r2) = $result_neo_uri
        RETURN p, cp, cr, r2
        '''
    result = db.query(q, data_binding={"patient_neo_uri": patient_neo_uri,
                                       "result_neo_uri": result2_neo_uri
                                       })
    assert len(result) == 1
    print(result)
    record = result[0]
    assert record['r2']['uri'] == "my-uri"      # The specific "uri" that was passed



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
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 0

    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car", properties={})  # Properties are required

    with pytest.raises(Exception):
        # "color" is not a registered property of the Class "Car"
        NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})

    NeoSchema.add_properties_to_class(class_node = class_internal_id, property_list = ["color"])


    # Successfully adding the first data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]


    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car",
                                      properties={"make": "A property not currently allowed"})   # Trying to set a non-allowed property


    # The merging will use the already-existing data point, since the properties match up
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "white"})
    assert status == False    # No new node was created

    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 1     # STILL at 1 datapoint

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'white', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]   # Same as before


    # Successfully adding a new (2nd) data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.add_data_node_merge(class_name="Car",
                                      properties={"color": "white", "make": "Toyota"})   # Trying to set a non-allowed property

    # Successfully adding a 3rd data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "blue", "year": 2023})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2023, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]


    # Successfully adding a 4th data point
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "blue", "year": 2000})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'blue', 'year': 2000, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]
    # We can have 2 red blue because they differ in the other attribute (i.e. the year)


    # Nothing gets added now, because a "blue, 2000" car already exists
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "blue", "year": 2000})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 4     # UNCHANGED


    # Likewise, nothing gets added now, because a "red" car already exists
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "red"})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 4     # UNCHANGED


    # By contrast, a new data node gets added now, because the "mileage" field will now be kept, and there's no "red car from 1999"
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red", "year": 1999})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 5     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]


    # Attempting to re-add the "red, 1999" car will have no effect...
    _ , status = NeoSchema.add_data_node_merge(class_name="Car",
                                               properties={"color": "red", "year": 1999})
    assert status == False    # No new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 5     # UNCHANGED


    NeoSchema.add_properties_to_class(class_node=class_internal_id, property_list=["make"])
    # ... but there's no car "red, 1999, Toyota"
    new_datanode_id, status = NeoSchema.add_data_node_merge(class_name="Car",
                                                            properties={"color": "red", "year": 1999, "make": "Toyota"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 6     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'color': 'red', 'year': 1999, 'make': 'Toyota', 'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]


    # Now, set up an irregular scenario where there's a database node that will match the attributes and labels
    # of a Data Node to add, but is not itself a Data Node (it lacks a SCHEMA relationship to its Class)
    # This node will be ignored by the Schema layer, because it's not managed by it - and we can add just fine
    # a Data Node for a "yellow car"
    db.create_node(labels="Car", properties={"color": "yellow"})
    _, status = NeoSchema.add_data_node_merge(class_name="Car", properties={"color": "yellow"})
    assert status == True    # A new node was created
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 7     # Increased



def test_add_data_column_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        # No such class exists
        NeoSchema.add_data_column_merge(class_name="Car", property_name="color", value_list=["white"])

    class_internal_id , class_schema_uri = NeoSchema.create_class_with_properties("Car",
                                                                                 property_list=["color", "year"],
                                                                                 strict=True)
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 0

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
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 3


    # Only 1 of the following 3 data points isn't already in the database
    result = NeoSchema.add_data_column_merge(class_name="Car",
                                             property_name="color", value_list=["red", "green", "blue"])
    assert len(result["new_nodes"]) == 1
    assert len(result["old_nodes"]) == 2
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 4

    id_green_car = result["new_nodes"][0]
    data_point = NeoSchema.fetch_data_node(internal_id=id_green_car, labels="Car")
    assert data_point["color"] == "green"


    # Successfully add the 2 distinct data points, from the 3 below, using a different field
    result = NeoSchema.add_data_column_merge(class_name="Car",
                                             property_name="year", value_list=[2003, 2022, 2022])
    assert len(result["new_nodes"]) == 2
    assert len(result["old_nodes"]) == 1
    assert NeoSchema.count_data_nodes_of_class(class_internal_id) == 6



def test_add_data_point_fast_OBSOLETE(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its Neo4j ID
    doctor_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE(class_name="doctor",
                                                           properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    q = '''
        MATCH (d:doctor {name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]->(c:CLASS {name: "doctor"})
        WHERE id(d) = $doctor_neo_uri
        RETURN d, c
        '''
    result = db.query(q, data_binding={"doctor_neo_uri": doctor_neo_uri})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c"]["name"] == "doctor"
    assert record["d"] == {"name":"Dr. Preeti", "specialty":"sports medicine"}


    # Create a new data point for a "patient", linked to the existing "doctor" data point
    patient_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE(class_name="patient",
                                                            properties={"name": "Jill", "age": 22, "balance": 145.50},
                                                            connected_to_neo_id = doctor_neo_uri,
                                                            rel_name= "IS_ATTENDED_BY", rel_dir="OUT")

    q = '''
        MATCH (cp:CLASS {name: "patient"})<-[:SCHEMA]
        - (p :patient {name: "Jill", age: 22, balance: 145.50})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine"})
        -[:SCHEMA]->(cd:CLASS {name: "doctor"})<-[:IS_ATTENDED_BY]-(cp)
        WHERE id(d) = $doctor_neo_uri AND id(p) = $patient_neo_uri
        RETURN p, d, cp, cd
        '''
    result = db.query(q, data_binding={"doctor_neo_uri": doctor_neo_uri, "patient_neo_uri": patient_neo_uri})
    assert len(result) == 1


    # Create a new data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of an autoincrement "uri" to the new data node
    result_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE(class_name="result",
                                                           properties={"biomarker": "glucose", "value": 99.0},
                                                           connected_to_neo_id = patient_neo_uri,
                                                           rel_name= "HAS_RESULT", rel_dir="IN",
                                                           assign_uri= True)

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r :result {biomarker: "glucose", value: 99.0})
        WHERE id(p) = $patient_neo_uri AND id(r) = $result_neo_uri
        RETURN p, cp, cr, r
        '''
    result = db.query(q, data_binding={"patient_neo_uri": patient_neo_uri,
                                       "result_neo_uri": result_neo_uri
                                       })
    assert len(result) == 1
    #print(result)
    record = result[0]
    assert record['r']['uri'] == "1"  # The first auto-increment value


    # Create a 2nd data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of specific "uri" to the new data node
    result2_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE(class_name="result",
                                                            properties={"biomarker": "cholesterol", "value": 180.0},
                                                            connected_to_neo_id = patient_neo_uri,
                                                            rel_name="HAS_RESULT", rel_dir="IN",
                                                            new_uri="my=uri")
    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r2 :result {biomarker: "cholesterol", value: 180.0})
        WHERE id(p) = $patient_neo_uri AND id(r2) = $result_neo_uri
        RETURN p, cp, cr, r2
        '''
    result = db.query(q, data_binding={"patient_neo_uri": patient_neo_uri,
                                       "result_neo_uri": result2_neo_uri
                                       })
    assert len(result) == 1
    print(result)
    record = result[0]
    assert record['r2']['uri'] == "my=uri"      # The specific "uri" that was passed



def test_add_data_point(db):
    #TODO: also test the connected_to_uri arguments
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its uri
    doctor_data_uri = NeoSchema.add_data_point_OLD(class_name="doctor",
                                                  data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                                  return_uri=True)

    # Create a new data point, and this time get its Neo4j ID
    result_neo_uri = NeoSchema.add_data_point_OLD(class_name="result",
                                                 data_dict={"biomarker": "glucose", "value": 99.0},
                                                 return_uri=False)

    q = '''
        MATCH (d:doctor {uri: $doctor, name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]-(c1:CLASS)
            -[*]-
            (c2:CLASS)<-[:SCHEMA]-(r:result {biomarker: "glucose", value: 99.0})
        WHERE id(r) = $result_neo_uri
        RETURN d, c1, c2, r
        '''

    #db.debug_print(q, data_binding={"doctor": doctor_data_uri, "result_neo_uri": result_neo_uri}, force_output=True)

    result = db.query(q, data_binding={"doctor": doctor_data_uri, "result_neo_uri": result_neo_uri})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c1"]["name"] == "doctor"
    assert record["c2"]["name"] == "result"



def test_add_and_link_data_point(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    doctor_neo_uri = NeoSchema.add_data_point_OLD(class_name="doctor",
                                                 data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                                 return_uri=False)

    result_neo_uri = NeoSchema.add_data_point_OLD(class_name="result",
                                                 data_dict={"biomarker": "glucose", "value": 99.0},
                                                 return_uri=False)

    patient_neo_uri = NeoSchema.add_and_link_data_point_OBSOLETE(class_name="patient",
                                                                properties={"name": "Jill", "age": 19, "balance": 312.15},
                                                                connected_to_list = [ (doctor_neo_uri, "IS_ATTENDED_BY") , (result_neo_uri, "HAS_RESULT") ])

    # Traverse a loop in the graph, from the patient data node, back to itself - going thru data and schema nodes
    q = '''
        MATCH (p:patient {name: "Jill", age: 19, balance: 312.15})-[:IS_ATTENDED_BY]->
              (d:doctor {name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]-(c1:CLASS)
              -[*]-
              (c2:CLASS)<-[:SCHEMA]-(r:result {biomarker: "glucose", value: 99.0})
              <-[:HAS_RESULT]-(p)
        WHERE id(p) = $patient AND id(d) = $doctor AND id(r) = $result
        RETURN d, c1, c2, r
        '''

    data_binding = {"patient": patient_neo_uri, "doctor": doctor_neo_uri, "result": result_neo_uri}
    #db.debug_print(q, data_binding=data_binding, force_output=True)
    result = db.query(q, data_binding=data_binding)
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c1"]["name"] == "doctor"
    assert record["c2"]["name"] == "result"


    # Attempt to sneak in a relationship not in the Schema
    with pytest.raises(Exception):
        NeoSchema.add_and_link_data_point_OBSOLETE(class_name="patient",
                                                   properties={"name": "Jill", "age": 19, "balance": 312.15},
                                                   connected_to_list = [ (doctor_neo_uri, "NOT_A_DECLARED_RELATIONSHIP") , (result_neo_uri, "HAS_RESULT") ])


    # Attempt to use a Class not in the Schema
    with pytest.raises(Exception):
        NeoSchema.add_and_link_data_point_OBSOLETE(class_name="NO_SUCH CLASS",
                                                   properties={"name": "Jill", "age": 19, "balance": 312.15},
                                                   connected_to_list = [ ])




def test_register_existing_data_point(db):
    pass    # TODO



def delete_data_node(db):
    pass



def test_delete_data_point(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.delete_data_node(node_id = 1)     # Non-existing node (database just got cleared)


    create_sample_schema_1()    # Schema with patient/result/doctor

    with pytest.raises(Exception):
        NeoSchema.delete_data_node(node_id = -1)    # Invalid node ID


    # Create new data nodes
    doctor_data_uri = NeoSchema.create_data_node(class_node="doctor",
                                                properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    patient_data_uri = NeoSchema.create_data_node(class_node="patient",
                                                 properties={"name": "Val", "age": 22})

    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor == {'name': 'Dr. Preeti', 'specialty': 'sports medicine'}

    patient = NeoSchema.fetch_data_node(internal_id=patient_data_uri)
    assert patient == {'name': 'Val', 'age': 22}

    NeoSchema.delete_data_node(node_id=doctor_data_uri)

    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor is None   # The doctor got deleted

    patient = NeoSchema.fetch_data_node(internal_id=patient_data_uri)
    assert patient == {'name': 'Val', 'age': 22}    # The patient is still there

    with pytest.raises(Exception):
        NeoSchema.delete_data_node(node_id=patient_data_uri, labels="not_present")   # Nothing gets deleted; hence, error

    with pytest.raises(Exception):
        NeoSchema.delete_data_node(node_id=patient_data_uri, labels=["patient", "extra label"])   # Nothing gets deleted; hence, error

    NeoSchema.delete_data_node(node_id=patient_data_uri, labels="patient")

    patient = NeoSchema.fetch_data_node(internal_id=patient_data_uri)
    assert patient is None    # The patient is now gone


    doctor_data_uri = NeoSchema.create_data_node(class_node="doctor", extra_labels="employee",
                                                properties={"name": "Dr. Preeti", "specialty": "sports medicine"})
    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor == {'name': 'Dr. Preeti', 'specialty': 'sports medicine'}

    NeoSchema.delete_data_node(node_id=doctor_data_uri, labels="employee")
    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor is None   # The doctor got deleted

    doctor_data_uri = NeoSchema.create_data_node(class_node="doctor", extra_labels=["doctor", "employee"],
                                                properties={"name": "Dr. Preeti", "specialty": "sports medicine"})
                                                # No harm in re-specifying the "doctor" label
    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor == {'name': 'Dr. Preeti', 'specialty': 'sports medicine'}

    NeoSchema.delete_data_node(node_id=doctor_data_uri, labels=["employee", "doctor"])
    doctor = NeoSchema.fetch_data_node(internal_id=doctor_data_uri)
    assert doctor is None       # The doctor got deleted



def test_add_data_relationship_hub(db):
    db.empty_dbase()

    # Set up the Schema
    NeoSchema.create_class_with_properties("City", property_list=["name"])
    NeoSchema.create_class_with_properties("State", property_list=["name"])

    # Set up the Data Nodes (2 cities and a state)
    berkeley = NeoSchema.create_data_node(class_node="City", properties = {"name": "Berkeley"})
    san_diego = NeoSchema.create_data_node(class_node="City", properties = {"name": "San Diego"})
    california = NeoSchema.create_data_node(class_node="State", properties = {"name": "California"})

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
    nevada = NeoSchema.create_data_node(class_node="State", properties = {"name": "Nevada"})
    oregon = NeoSchema.create_data_node(class_node="State", properties = {"name": "Oregon"})

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
        NeoSchema.add_data_relationship_OLD(from_id=123, to_id=456, rel_name="junk")  # No such nodes exist

    neo_uri_1 = db.create_node("random A")
    neo_uri_2 = db.create_node("random B")
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_OLD(from_id=neo_uri_1, to_id=neo_uri_2, rel_name="junk") # Not data nodes with a Schema

    _ , person_class_uri = NeoSchema.create_class("Person")
    person_uri = NeoSchema.add_data_point_OLD("Person")

    _ , car_class_uri = NeoSchema.create_class("Car")
    car_uri = NeoSchema.add_data_point_OLD("Car")

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name="DRIVES", id_type="uri")

    # Add the "DRIVE" relationship between the classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="DRIVES")

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name="", id_type="uri")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name=None, id_type="uri")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_OLD(from_id=car_uri, to_id=person_uri, rel_name="DRIVES", id_type="uri")  # Wrong direction

    # Now, finally, it'll work
    NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name="DRIVES", id_type="uri")

    # Verify the cycle of "DRIVES" relationships
    q = '''
    MATCH (c:Car {uri:$car_uri})<-[:DRIVES]-(p:Person {uri:$person_uri})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})-[:DRIVES]->(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_uri": car_uri, "person_uri": person_uri}, single_cell="number_cars")
    assert result == 1


    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name="DRIVES", id_type="uri")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship_OLD(from_id=person_uri, to_id=car_uri, rel_name="SOME_OTHER_NAME", id_type="uri")


    # Now add reverse a relationship, and this time use the Neo4j ID's to locate the nodes
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_DRIVEN_BY")

    neo_person_id = NeoSchema.get_data_node_id(person_uri)
    neo_car_id = NeoSchema.get_data_node_id(car_uri)
    NeoSchema.add_data_relationship_OLD(from_id=neo_car_id, to_id=neo_person_id, rel_name="IS_DRIVEN_BY")

    # Verify the cycle of "IS_DRIVEN_BY" relationships
    q = '''
    MATCH (c:Car {uri:$car_uri})-[:IS_DRIVEN_BY]->(p:Person {uri:$person_uri})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})<-[:IS_DRIVEN_BY]-(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_uri": car_uri, "person_uri": person_uri}, single_cell="number_cars")
    assert result == 1

    # Verify that the cycle of "DRIVES" relationships is also still there
    q = '''
    MATCH (c:Car {uri:$car_uri})<-[:DRIVES]-(p:Person {uri:$person_uri})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})-[:DRIVES]->(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_uri": car_uri, "person_uri": person_uri}, single_cell="number_cars")
    assert result == 1



def test_add_data_relationship_2(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=123, to_id=456, rel_name="junk")  # No such nodes exist

    neo_uri_1 = db.create_node("random A")
    neo_uri_2 = db.create_node("random B")
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=neo_uri_1, to_id=neo_uri_2, rel_name="junk") # Not data nodes with a Schema

    _ , person_class_uri = NeoSchema.create_class("Person")
    person_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE("Person")

    _ , car_class_uri = NeoSchema.create_class("Car")
    car_neo_uri = NeoSchema.add_data_point_fast_OBSOLETE("Car")

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name="DRIVES")

    # Add the "DRIVE" relationship between the Classes
    NeoSchema.create_class_relationship(from_class="Person", to_class="Car", rel_name="DRIVES")

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name="")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name=None)  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship(from_id=car_neo_uri, to_id=person_neo_uri, rel_name="DRIVES")  # Wrong direction

    # Now it works
    NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship(from_id=person_neo_uri, to_id=car_neo_uri, rel_name="SOME_OTHER_NAME")


    # Now add reverse a relationship between the Classes
    NeoSchema.create_class_relationship(from_class="Car", to_class="Person", rel_name="IS_DRIVEN_BY")

    # Add that same reverse relationship between the data points
    NeoSchema.add_data_relationship(from_id=car_neo_uri, to_id=person_neo_uri, rel_name="IS_DRIVEN_BY")



def test_remove_data_relationship(db):
    pass    # TODO



def test_locate_node(db):
    pass    # TODO



def test_class_of_data_point(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.class_of_data_node(node_id=123)  # No such data node exists

    internal_id = db.create_node("random")
    with pytest.raises(Exception):
        NeoSchema.class_of_data_node(node_id=internal_id)     # It's not a data node

    NeoSchema.create_class("Person")
    uri = NeoSchema.add_data_point_OLD("Person")

    assert NeoSchema.class_of_data_node(node_id=uri, id_type="uri") == "Person"
    assert NeoSchema.class_of_data_node(node_id=uri, id_type="uri", labels="Person") == "Person"

    # Now locate thru the internal database ID
    internal_id = NeoSchema.get_data_node_id(uri)
    #print("neo_uri: ", neo_uri)
    assert NeoSchema.class_of_data_node(node_id=internal_id) == "Person"

    NeoSchema.create_class("Extra")
    # Create a forbidden scenario with a data node having 2 Schema classes
    q = f'''
        MATCH (n {{uri: '{uri}' }}), (c :CLASS {{name: 'Extra'}})
        MERGE (n)-[:SCHEMA]->(c)
        '''
    #db.debug_print(q, {}, "test")
    db.update_query(q)
    with pytest.raises(Exception):
        assert NeoSchema.class_of_data_node(node_id=internal_id) == "Person"    # Data node is associated to multiple classes




#############   DATA IMPORT   ###########

# See separate file


#############   EXPORT SCHEMA   ###########


###############   URI'S   ###############

def test_advance_autoincrement(db):
    db.empty_dbase()
    assert NeoSchema.advance_autoincrement("a") == 1
    assert NeoSchema.advance_autoincrement("a") == 2
    assert NeoSchema.advance_autoincrement("schema") == 1
    assert NeoSchema.advance_autoincrement("schema") == 2
    assert NeoSchema.advance_autoincrement("a") == 3
    assert NeoSchema.advance_autoincrement("documents") == 1
    assert NeoSchema.advance_autoincrement("documents") == 2

    # The following line will "reserve" the values 3 and 4
    assert NeoSchema.advance_autoincrement("documents", advance=2) == 3
    assert NeoSchema.advance_autoincrement("documents") == 5

    # The following line will "reserve" the values 1 thru 10
    assert NeoSchema.advance_autoincrement("image", advance=10) == 1
    assert NeoSchema.advance_autoincrement("image") == 11
    assert NeoSchema.advance_autoincrement("          image   ") == 12 # Leading/trailing blanks are ignored

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(123)    # Not a string

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement("        ")

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(namespace ="a", advance ="not an integer")

    with pytest.raises(Exception):
        assert NeoSchema.advance_autoincrement(namespace ="a", advance = 0)  # Advance isn't >= 1



def test_reserve_next_uri(db):
    db.empty_dbase()
    assert NeoSchema.reserve_next_uri(namespace="data_node") == "1"   # Accept default blank prefix/suffix
    assert NeoSchema.reserve_next_uri("data_node") == "2"
    assert NeoSchema.reserve_next_uri("data_node") == "3"
    assert NeoSchema.reserve_next_uri(namespace="data_node", prefix="i-") == "i-4"        # Force a prefix
    assert NeoSchema.reserve_next_uri(namespace="data_node", suffix=".jpg") == "5.jpg"    # Force a suffix
    assert NeoSchema.reserve_next_uri("data_node") == "6"
    assert NeoSchema.reserve_next_uri() == "7"    # default namespace

    assert NeoSchema.reserve_next_uri(namespace="notes", prefix="n-") == "n-1"
    assert NeoSchema.reserve_next_uri(namespace="notes", prefix="n-") == "n-2"    # Redundant specification of prefix
    assert NeoSchema.reserve_next_uri(namespace="notes") == "n-3"                 # No need to specify the prefix (stored)

    assert NeoSchema.reserve_next_uri(namespace="schema_node", prefix="schema-") == "schema-1"
    assert NeoSchema.reserve_next_uri(namespace="schema_node") == "schema-2"

    assert NeoSchema.reserve_next_uri("documents", prefix="d-", suffix="") == "d-1"
    assert NeoSchema.reserve_next_uri("documents", prefix="d-") == "d-2"
    assert NeoSchema.reserve_next_uri("documents", prefix="doc.", suffix=".new") == "doc.3.new"
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





###############   PRIVATE  METHODS   ###############

def test_valid_schema_uri(db):
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





#####################   For class SchemaCache   #####################

def test_get_cached_class_data(db):
    db.empty_dbase()

    car_class_uri, _ = NeoSchema.create_class_with_properties("Cars", ["A", "B"], strict=False)
    schema_cache = SchemaCache()

    # Test "class_attributes" option
    class_attrs = NeoSchema.get_class_attributes(car_class_uri)
    assert class_attrs["name"] == "Cars"
    assert not class_attrs["strict"]

    assert schema_cache.get_cached_class_data(car_class_uri, request="class_attributes") == class_attrs
    # A 2nd identical run will use the previously-cached data
    assert schema_cache.get_cached_class_data(car_class_uri, request="class_attributes") == class_attrs


    # Test "class_properties" option
    car_class_properties = NeoSchema.get_class_properties(car_class_uri, include_ancestors=False)
    assert compare_unordered_lists(car_class_properties, ["A", "B"])

    assert schema_cache.get_cached_class_data(car_class_uri, request="class_properties") == car_class_properties
    # A 2nd identical run will use the previously-cached data
    assert schema_cache.get_cached_class_data(car_class_uri, request="class_properties") == car_class_properties


    # Add a related 2nd Class
    vehicle_class_uri, _ = NeoSchema.create_class_with_properties("Vehicles", ["C", "D", "E"], strict=True)

    NeoSchema.create_class_relationship(from_class="Cars", to_class="Vehicles", rel_name="type of")

    vehicle_class_properties = schema_cache.get_cached_class_data(vehicle_class_uri, request="class_properties")
    assert compare_unordered_lists(vehicle_class_properties, ["C", "D", "E"])

    # This time, a cached version will be used
    vehicle_class_properties = schema_cache.get_cached_class_data(vehicle_class_uri, request="class_properties")
    assert compare_unordered_lists(vehicle_class_properties, ["C", "D", "E"])

    assert schema_cache.get_cached_class_data(car_class_uri, request="class_properties") == car_class_properties # Still unchanged


    # Test "out_neighbors" option
    car_neighbors = schema_cache.get_cached_class_data(car_class_uri, request="out_neighbors")
    assert car_neighbors == {"type of": "Vehicles"}
    # A 2nd identical run will use the previously-cached data
    car_neighbors = schema_cache.get_cached_class_data(car_class_uri, request="out_neighbors")
    assert car_neighbors == {"type of": "Vehicles"}

    vehicle_neighbors = schema_cache.get_cached_class_data(vehicle_class_uri, request="out_neighbors")
    assert vehicle_neighbors == {}      # No outbound links exist for "Vehicles" class



def test_get_cached_class_data_2(db):   # Additional testing of get_cached_class_data()
    db.empty_dbase()
    cache = SchemaCache()

    assert cache._schema == {}

    neo_uri, schema_uri = NeoSchema.create_class("My first class", strict=False)

    cache.get_cached_class_data(class_id=neo_uri, request="class_attributes")
    expected_first_class = {"class_attributes":  {'name': 'My first class', 'uri': schema_uri, 'strict': False}
                            }
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class


    cache.get_cached_class_data(class_id=neo_uri, request="class_properties")
    expected_first_class = {"class_attributes":  {'name': 'My first class', 'uri': schema_uri, 'strict': False},
                            "class_properties":  []
                            }
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class


    cache.get_cached_class_data(class_id=neo_uri, request="out_neighbors")
    expected_first_class = {"class_attributes":  {'name': 'My first class', 'uri': schema_uri, 'strict': False},
                            "class_properties":  [],
                            "out_neighbors": {}
                            }
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class

    assert len(cache._schema) == 1


    # Expand the Schema
    schema_info = create_sample_schema_1()      # Schema with patient/result/doctor
                                                # Returns dict of the form {"patient": sch_1, "result": sch_2, "doctor": sch_3}
    patient_uri = schema_info["patient"]
    result_uri = schema_info["result"]
    doctor_uri = schema_info["doctor"]

    # Nothing changed in the schema cache from simply adding new Classes
    assert len(cache._schema) == 1
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class

    schema_uri_patient = NeoSchema.get_class_uri('patient')

    cache.get_cached_class_data(class_id=patient_uri, request="class_attributes")
    assert len(cache._schema) == 2
    expected_patient = {"class_attributes":  {'name': 'patient', 'uri': schema_uri_patient, 'strict': False}
                       }
    assert cache.get_all_cached_class_data(class_id=patient_uri) == expected_patient
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class     # Unchanged


    cache.get_cached_class_data(class_id=patient_uri, request="class_properties")
    expected_patient = {"class_attributes":  {'name': 'patient', 'uri': schema_uri_patient, 'strict': False},
                        "class_properties": ['name', 'age', 'balance']
                        }
    assert cache.get_all_cached_class_data(class_id=patient_uri) == expected_patient
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class     # Unchanged

    cache.get_cached_class_data(class_id=patient_uri, request="out_neighbors")
    expected_patient = {"class_attributes":  {'name': 'patient', 'uri': schema_uri_patient, 'strict': False},
                        "class_properties": ['name', 'age', 'balance'],
                        "out_neighbors": {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}
                        }
    assert cache.get_all_cached_class_data(class_id=patient_uri) == expected_patient
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class     # Unchanged

    schema_uri_result = NeoSchema.get_class_uri('result')

    cache.get_cached_class_data(class_id=result_uri, request="class_attributes")
    assert len(cache._schema) == 3
    expected_result = {"class_attributes":  {'name': 'result', 'uri': schema_uri_result, 'strict': False}
                      }
    assert cache.get_all_cached_class_data(class_id=result_uri) == expected_result
    assert cache.get_all_cached_class_data(class_id=patient_uri) == expected_patient     # Unchanged
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class     # Unchanged


    schema_uri_doctor = NeoSchema.get_class_uri('doctor')

    cache.get_cached_class_data(class_id=doctor_uri, request="class_attributes")
    assert len(cache._schema) == 4
    expected_doctor = {"class_attributes":  {'name': 'doctor', 'uri': schema_uri_doctor, 'strict': False}
                       }
    assert cache.get_all_cached_class_data(class_id=doctor_uri) == expected_doctor
    assert cache.get_all_cached_class_data(class_id=result_uri) == expected_result       # Unchanged
    assert cache.get_all_cached_class_data(class_id=patient_uri) == expected_patient     # Unchanged
    assert cache.get_all_cached_class_data(class_id=neo_uri) == expected_first_class     # Unchanged
