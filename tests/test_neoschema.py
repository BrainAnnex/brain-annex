# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists
from neoaccess import NeoAccess
#import neoaccess
from BrainAnnex.modules.utilities.comparisons import compare_recordsets
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema, SchemaCache, SchemaCacheExperimental


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE SCHEMAS for the testing  **************

def create_sample_schema_1():
    # Schema with patient/result/doctor Classes (each with some Properties),
    # and relationships between the Classes: HAS_RESULT, IS_ATTENDED_BY

    _, sch_1 = NeoSchema.create_class_with_properties(class_name="patient",
                                                      property_list=["name", "age", "balance"])

    _, sch_2 = NeoSchema.create_class_with_properties(class_name="result",
                                                      property_list=["biomarker", "value"])

    _, sch_3 = NeoSchema.create_class_with_properties(class_name="doctor",
                                                      property_list=["name", "specialty"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="HAS_RESULT")
    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_3, rel_name="IS_ATTENDED_BY")

    return {"patient": sch_1, "result": sch_2, "doctor": sch_3}



def create_sample_schema_2():
    # Class "quotes" with relationship named "in_category" to Class "categories";
    # each Class has some properties
    _, sch_1 = NeoSchema.create_class_with_properties(class_name="quotes",
                                                      property_list=["quote", "attribution", "verified"])

    _, sch_2 = NeoSchema.create_class_with_properties(class_name="categories",
                                                      property_list=["name", "remarks"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="in_category")

    return {"quotes": sch_1, "categories": "sch_2"}




#############   CLASS-related   #############

def test_create_class(db):
    db.empty_dbase()

    _ , french_class_id = NeoSchema.create_class("French Vocabulary")
    match = db.match(labels="CLASS")   # All Class nodes
    result = db.get_nodes(match)
    assert result == [{'name': 'French Vocabulary', 'schema_id': french_class_id, 'type': 'L'}]

    _ , class_A_id = NeoSchema.create_class("A", schema_type="S")
    result = db.get_nodes(match)
    expected = [{'name': 'French Vocabulary', 'schema_id': french_class_id, 'type': 'L'},
                {'name': 'A', 'schema_id': class_A_id, 'type': 'S'}]
    assert compare_recordsets(result, expected)

    with pytest.raises(Exception):
        assert NeoSchema.create_class("A", schema_type="L")  # A class by that name already exists; so, nothing gets created

    with pytest.raises(Exception):
        assert NeoSchema.create_class("B", schema_type="X")   # Non-existent schema_type that raises exception



def test_get_class_neo_id(db):
    db.empty_dbase()
    A_neo_id, _ = NeoSchema.create_class("A")
    assert NeoSchema.get_class_internal_id("A") == A_neo_id

    B_neo_id, _ = NeoSchema.create_class("B")
    assert NeoSchema.get_class_internal_id("A") == A_neo_id
    assert NeoSchema.get_class_internal_id("B") == B_neo_id

    with pytest.raises(Exception):
        assert NeoSchema.get_class_internal_id("NON-EXISTENT CLASS")



def test_get_class_id(db):
    db.empty_dbase()
    _ , class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_id("A") == class_A_id

    _ , class_B_id = NeoSchema.create_class("B")
    assert NeoSchema.get_class_id("A") == class_A_id
    assert NeoSchema.get_class_id("B") == class_B_id

    assert NeoSchema.get_class_id("NON-EXISTENT CLASS") == -1



def test_get_class_id_by_neo_id(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.get_class_id_by_neo_id(999)   # Non-existent class

    class_A_neo_id , class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_id_by_neo_id(class_A_neo_id) == class_A_id

    class_B_neo_id , class_B_id = NeoSchema.create_class("B")
    assert NeoSchema.get_class_id_by_neo_id(class_A_neo_id) == class_A_id
    assert NeoSchema.get_class_id_by_neo_id(class_B_neo_id) == class_B_id



def test_class_id_exists(db):
    db.empty_dbase()
    assert not NeoSchema.class_id_exists(123)

    with pytest.raises(Exception):
        assert NeoSchema.class_id_exists("not_a_number")

    _ , class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.class_id_exists(class_A_id)


def test_class_name_exists(db):
    db.empty_dbase()

    assert not NeoSchema.class_name_exists("A")
    NeoSchema.create_class("A")
    assert NeoSchema.class_name_exists("A")

    with pytest.raises(Exception):
        assert NeoSchema.class_id_exists(123)



def test_get_class_name(db):
    db.empty_dbase()
    _ , class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_name(class_A_id) == "A"

    _ , class_B_id = NeoSchema.create_class("B")
    assert NeoSchema.get_class_name(class_A_id) == "A"
    assert NeoSchema.get_class_name(class_B_id) == "B"

    assert NeoSchema.get_class_name(2345) == ""
    assert NeoSchema.get_class_name(-1) == ""


def test_get_class_name_by_neo_id(db):
    db.empty_dbase()
    class_A_neoid , _ = NeoSchema.create_class("A")
    assert NeoSchema.get_class_name_by_neo_id(class_A_neoid) == "A"

    class_B_neoid , _ = NeoSchema.create_class("B")
    assert NeoSchema.get_class_name_by_neo_id(class_A_neoid) == "A"
    assert NeoSchema.get_class_name_by_neo_id(class_B_neoid) == "B"

    with pytest.raises(Exception):
        NeoSchema.get_class_name_by_neo_id(2345)                    # No such Class exists
        NeoSchema.get_class_name_by_neo_id(-1)                      # Invalid id
        NeoSchema.get_class_name_by_neo_id("I'm not an integer!")   # Invalid id



def test_get_class_attributes(db):
    db.empty_dbase()
    class_A_neoid , class_A_id = NeoSchema.create_class("A")
    assert NeoSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'schema_id': class_A_id, 'type': 'L'}

    class_B_neoid , class_B_id = NeoSchema.create_class("B", no_datanodes=True)
    assert NeoSchema.get_class_attributes(class_A_neoid) == {'name': 'A', 'schema_id': class_A_id, 'type': 'L'}
    assert NeoSchema.get_class_attributes(class_B_neoid) == {'name': 'B', 'schema_id': class_B_id, 'type': 'L', 'no_datanodes': True}

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
    _ , french_class_id = NeoSchema.create_class("French Vocabulary")
    _ , foreign_class_id = NeoSchema.create_class("Foreign Vocabulary")
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
    db.empty_dbase()
    _ , class_A_id = NeoSchema.create_class("A")    # The returned value is the "Schema ID"
    _ , class_B_id = NeoSchema.create_class("B")

    with pytest.raises(Exception):
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name=None)
        NeoSchema.delete_class_relationship(from_class="", to_class="B", rel_name="some name")
        NeoSchema.delete_class_relationship(from_class="A", to_class=None, rel_name="some name")
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create a relationship, and then immediately delete it
    NeoSchema.create_class_relationship(from_id = class_A_id, to_id = class_B_id, rel_name="Friend with")
    assert NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    n_del = NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")
    assert n_del == 1
    assert not NeoSchema.class_relationship_exists(from_class="A", to_class="B", rel_name="Friend with")
    with pytest.raises(Exception):  # Attempting to re-delete it, will cause error
        NeoSchema.delete_class_relationship(from_class="A", to_class="B", rel_name="Friend with")

    # Create 2 different relationships between the same classes, then delete each relationship at a time
    NeoSchema.create_class_relationship(from_id = class_A_id, to_id = class_B_id, rel_name="Friend with")
    NeoSchema.create_class_relationship(from_id = class_A_id, to_id = class_B_id, rel_name="LINKED_TO")
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
    pass    # TODO



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
    NeoSchema.add_data_point(class_name="quotes",
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



def test_allows_data_nodes(db):
    db.empty_dbase()

    neo_id_yes , _ = NeoSchema.create_class("French Vocabulary")
    assert NeoSchema.allows_data_nodes(class_name="French Vocabulary") == True
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_yes) == True

    neo_id_no , _ = NeoSchema.create_class("Vocabulary", no_datanodes = True)
    assert NeoSchema.allows_data_nodes(class_name="Vocabulary") == False
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_no) == False

    # Tests using Schema Caching
    schema_cache = SchemaCacheExperimental()
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_yes, schema_cache=schema_cache) == True
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_no, schema_cache=schema_cache) == False
    # Repeat
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_yes, schema_cache=schema_cache) == True
    assert NeoSchema.allows_data_nodes(class_neo_id=neo_id_no, schema_cache=schema_cache) == False



def test_get_class_instances(db):
    pass    # TODO



def test_get_related_class_names(db):
    pass    # TODO



def test_get_class_relationships(db):
    pass    # TODO




#############   PROPERTIES-RELATED   #############


def test_get_class_properties_fast(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.create_class_with_properties(111)    # Invalid class name

    NeoSchema.create_class_with_properties("My first class", property_list=["A", "B", "C"])
    neo_id = NeoSchema.get_class_internal_id("My first class")
    props = NeoSchema.get_class_properties_fast(neo_id)
    assert props == ["A", "B", "C"]

    neo_id, schema_id = NeoSchema.create_class("Class with no properties")
    props = NeoSchema.get_class_properties_fast(neo_id)
    assert props == []

    NeoSchema.add_properties_to_class(class_internal_id=neo_id, property_list = ["X", "Y"])
    props = NeoSchema.get_class_properties_fast(neo_id)
    assert props == ["X", "Y"]

    NeoSchema.add_properties_to_class(class_internal_id=neo_id, property_list = ["Z"])
    props = NeoSchema.get_class_properties_fast(neo_id)
    assert props == ["X", "Y", "Z"]

    # TODO: more tests, especially for other args



def test_get_class_properties(db):
    pass    # TODO - will probably get phased out in favor of test_get_class_properties_fast()



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
    _ , schema_id_i = NeoSchema.create_class("My_class", code="i")
    _ , schema_id_n = NeoSchema.create_class("My_other_class", code="n")

    assert NeoSchema.get_schema_id(schema_code="i") == schema_id_i
    assert NeoSchema.get_schema_id(schema_code="n") == schema_id_n
    assert NeoSchema.get_schema_id(schema_code="x") == -1



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
        NeoSchema.count_data_points_of_class(666)   # Non-existent Class

    class_internal_id_1 , _ = NeoSchema.create_class("Some class")

    assert NeoSchema.count_data_points_of_class(class_internal_id_1) == 0

    NeoSchema.add_data_point_new(class_internal_id=class_internal_id_1)
    assert NeoSchema.count_data_points_of_class(class_internal_id_1) == 1

    NeoSchema.add_data_point_new(class_internal_id=class_internal_id_1)
    assert NeoSchema.count_data_points_of_class(class_internal_id_1) == 2


    class_internal_id_2 , _ = NeoSchema.create_class("Another class")

    assert NeoSchema.count_data_points_of_class(class_internal_id_2) == 0

    NeoSchema.add_data_point_new(class_internal_id=class_internal_id_2)
    assert NeoSchema.count_data_points_of_class(class_internal_id_2) == 1

    assert NeoSchema.count_data_points_of_class(class_internal_id_1) == 2   # Where we left it off



def test_data_points_lacking_schema(db):
    pass    # TODO



def test_get_data_point_id(db):
    pass    # TODO


def test_allowable_props(db):
    db.empty_dbase()

    lax_int_id, lax_schema_id = NeoSchema.create_class_with_properties("My Lax class", ["A", "B"], schema_type="L")
    strict_int_id, strict_schema_id = NeoSchema.create_class_with_properties("My Strict class", ["A", "B"], schema_type="S")


    d = NeoSchema.allowable_props(class_neo_id=lax_int_id,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped


    d = NeoSchema.allowable_props(class_neo_id=lax_int_id,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123}  # "C" got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_neo_id=strict_int_id,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=False)


    d = NeoSchema.allowable_props(class_neo_id=lax_int_id,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"X": 666, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {}      # Everything got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_neo_id=strict_int_id,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=False)


    # Repeating, using the SchemaCache
    schema_cache = SchemaCacheExperimental()

    d = NeoSchema.allowable_props(class_neo_id=lax_int_id, schema_cache=schema_cache,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id, schema_cache=schema_cache,
                                  requested_props={"A": 123}, silently_drop=True)
    assert d == {"A": 123}  # Nothing got dropped


    d = NeoSchema.allowable_props(class_neo_id=lax_int_id, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"A": 123}  # "C" got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_neo_id=strict_int_id, schema_cache=schema_cache,
                                  requested_props={"A": 123, "C": "trying to intrude"}, silently_drop=False)


    d = NeoSchema.allowable_props(class_neo_id=lax_int_id, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {"X": 666, "C": "trying to intrude"}  # Nothing got dropped, because "anything goes" with a "Lax" Class

    d = NeoSchema.allowable_props(class_neo_id=strict_int_id, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=True)
    assert d == {}      # Everything got silently dropped

    with pytest.raises(Exception):
        NeoSchema.allowable_props(class_neo_id=strict_int_id, schema_cache=schema_cache,
                                  requested_props={"X": 666, "C": "trying to intrude"}, silently_drop=False)

    # Check the cache itself
    assert schema_cache.get_cached_class_attrs(lax_int_id) == {"name": "My Lax class", "schema_id": lax_schema_id, "type": "L"}
    assert schema_cache.get_cached_class_attrs(strict_int_id) == {"name": "My Strict class", "schema_id": strict_schema_id, "type": "S"}




def test_schema_cache(db):      # TODO: move to its own section
    db.empty_dbase()

    internal_id, _ = NeoSchema.create_class_with_properties("My Lax class", ["A", "B"], schema_type="L")
    schema_cache = SchemaCacheExperimental()

    class_attrs = NeoSchema.get_class_attributes(internal_id)
    assert schema_cache.get_cached_class_attrs(internal_id) == class_attrs
    assert schema_cache.get_cached_class_attrs(internal_id) == class_attrs  # The 2nd run will use the previously-cached data



def test_add_data_point_with_links(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its Neo4j ID
    doctor_neo_id = NeoSchema.add_data_point_with_links(class_name="doctor",
                                                        properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    q = '''
        MATCH (d:doctor {name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]->(c:CLASS {name: "doctor"})
        WHERE id(d) = $doctor_neo_id
        RETURN d, c
        '''
    result = db.query(q, data_binding={"doctor_neo_id": doctor_neo_id})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c"]["name"] == "doctor"
    assert record["d"] == {"name":"Dr. Preeti", "specialty":"sports medicine"}

    with pytest.raises(Exception):
        NeoSchema.add_data_point_with_links(class_name="patient",
                                            properties={"name": "Jill", "age": 22, "balance": 145.50},
                                            links={}
                                            )   # links must be a list
        NeoSchema.add_data_point_with_links(class_name="patient",
                                            properties="NOT a dict",
                                            links={}
                                            )   # properties must be a dict
        NeoSchema.add_data_point_with_links(class_name="",
                                            properties={},
                                            links={}
                                            )   # class_name cannot be empty

    # Create a new data point for a "patient", linked to the existing "doctor" data point
    patient_neo_id = NeoSchema.add_data_point_with_links(class_name="patient",
                                                   properties={"name": "Jill", "age": 22, "balance": 145.50},
                                                   links=[{"internal_id": doctor_neo_id, "rel_name": "IS_ATTENDED_BY", "rel_dir": "OUT"}]
                                                    )

    q = '''
        MATCH (cp:CLASS {name: "patient"})<-[:SCHEMA]
        - (p :patient {name: "Jill", age: 22, balance: 145.50})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine"})
        -[:SCHEMA]->(cd:CLASS {name: "doctor"})<-[:IS_ATTENDED_BY]-(cp)
        WHERE id(d) = $doctor_neo_id AND id(p) = $patient_neo_id
        RETURN p, d, cp, cd
        '''
    result = db.query(q, data_binding={"doctor_neo_id": doctor_neo_id, "patient_neo_id": patient_neo_id})
    assert len(result) == 1


    # Create a new data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of an autoincrement "item_id" to the new data node
    result_neo_id = NeoSchema.add_data_point_with_links(class_name="result",
                                                  properties={"biomarker": "glucose", "value": 99.0},
                                                  links=[{"internal_id": patient_neo_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                  assign_item_id= True)

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r :result {biomarker: "glucose", value: 99.0})
        WHERE id(p) = $patient_neo_id AND id(r) = $result_neo_id
        RETURN p, cp, cr, r
        '''
    result = db.query(q, data_binding={"patient_neo_id": patient_neo_id,
                                       "result_neo_id": result_neo_id
                                       })
    assert len(result) == 1
    record = result[0]
    assert record['r']['item_id'] == 1  # The first auto-increment value


    # Create a 2nd data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of specific "item_id" to the new data node
    result2_neo_id = NeoSchema.add_data_point_with_links(class_name="result",
                                                        properties={"biomarker": "cholesterol", "value": 180.0},
                                                        links=[{"internal_id": patient_neo_id, "rel_name": "HAS_RESULT", "rel_dir": "IN"}],
                                                        new_item_id=9999)
    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r2 :result {biomarker: "cholesterol", value: 180.0})
        WHERE id(p) = $patient_neo_id AND id(r2) = $result_neo_id
        RETURN p, cp, cr, r2
        '''
    result = db.query(q, data_binding={"patient_neo_id": patient_neo_id,
                                       "result_neo_id": result2_neo_id
                                       })
    assert len(result) == 1
    print(result)
    record = result[0]
    assert record['r2']['item_id'] == 9999      # The specific "item_id" that was passed



def test_add_data_point_merge(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.add_data_point_merge(class_internal_id=123)     # No such class exists

    class_internal_id , _ = NeoSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        NeoSchema.add_data_point_merge(class_internal_id=class_internal_id)   # The Class doesn't allow data nodes

    class_internal_id , class_schema_id = NeoSchema.create_class("Car", schema_type="S")
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 0


    # Successfully adding the first data point
    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id)
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]   # No other properties were set


    with pytest.raises(Exception):
        NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                     properties={"color": "No properties allowed"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # The merging will use the already-existing data point, since we're only getting data nodes with no properties
    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                   properties={"color": "No properties allowed"},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 1     # STILL at 1 datapoint

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]   # No other properties were set


    # Successfully adding a new (2nd) data point
    NeoSchema.add_properties_to_class(class_internal_id=class_internal_id, property_list=["color"]) # Expand the allow class properties

    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                   properties={"color": "white"})

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'white'}]]   # This time the properties got set


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_internal_id=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                     properties={"color": "white", "make": "Toyota"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 3rd data point
    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                   properties={"color": "red", "make": "VW"},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'red'}]]   # The "color" got set, while the "make" got dropped


    # Successfully adding a 4th data point
    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                   properties={"color": "red", "make": "Fiat", "year": 2000},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'red', 'year': 2000}]]
    # The "color" and "year" got set, while the "make" got dropped.  We can have 2 red cars because they differ in the other attributes


    # Nothing gets added now, because a "red, 2000" car already exists
    NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                   properties={"color": "red", "year": 2000},
                                                   silently_drop=False)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 4     # UNCHANGED


    # Likewise, nothing gets added now, because a "red" car already exists (the "mileage" field isn't in the Schema and gets dropped)
    NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                     properties={"color": "red", "mileage": 12000},
                                                     silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 4     # UNCHANGED


    # By contrast, a new data node gets added now, because the "mileage" field will now be kept, and there's no "red car with 12,000 miles"
    NeoSchema.add_properties_to_class(class_internal_id=class_internal_id, property_list=["mileage"])
    new_datanode_id, _ = NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                                     properties={"color": "red", "mileage": 12000},
                                                     silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 5     # Increased

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'red', 'mileage': 12000}]]
    # All properties got set


    # Now, set up an irregular scenario where there's a database node that will match the attributes and labels
    # of a data node to add, but is not itself a data node (it lacks a SCHEMA relationship to its Class)
    db.create_node(labels="Car", properties={"color": "yellow"})
    with pytest.raises(Exception):
        NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                   properties={"color": "yellow"},
                                   silently_drop=True)

    # By contrast, the presence of a database node with same attributes, but different labels,
    # will not be considered a match
    db.create_node(labels="Boat", properties={"color": "purple"})
    NeoSchema.add_data_point_merge(class_internal_id=class_internal_id,
                                   properties={"color": "purple"},
                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 6     # Increased



def test_add_col_data_merge(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    with pytest.raises(Exception):
        NeoSchema.add_col_data_merge(class_internal_id=123, property_name="color", value_list=["white"])     # No such class exists

    class_internal_id , class_schema_id = NeoSchema.create_class_with_properties("Car",
                                                                                 property_list=["color", "year"],
                                                                                 schema_type="S")
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 0

    with pytest.raises(Exception):
        NeoSchema.add_col_data_merge(class_internal_id=class_internal_id, property_name=123, value_list=["white"])  # property_name isn't a string
        NeoSchema.add_col_data_merge(class_internal_id=class_internal_id, property_name="color", value_list="white")  # value_list isn't a list


    # Successfully add 3 data points
    result = NeoSchema.add_col_data_merge(class_internal_id=class_internal_id,
                                          property_name="color", value_list=["red", "white", "blue"])
    assert len(result["new_nodes"]) == 3
    assert len(result["old_nodes"]) == 0
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 3


    # Only 1 of the following 3 data points isn't already in the database
    result = NeoSchema.add_col_data_merge(class_internal_id=class_internal_id,
                                          property_name="color", value_list=["red", "green", "blue"])
    assert len(result["new_nodes"]) == 1
    assert len(result["old_nodes"]) == 2
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 4

    id_green_car = result["new_nodes"][0]
    data_point = NeoSchema.fetch_data_point(internal_id=id_green_car, labels="Car")
    assert data_point["color"] == "green"


    # Successfully add the 2 distinct data points, from the 3 below, using a different field
    result = NeoSchema.add_col_data_merge(class_internal_id=class_internal_id,
                                          property_name="year", value_list=[2003, 2022, 2022])
    assert len(result["new_nodes"]) == 2
    assert len(result["old_nodes"]) == 1
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 6


    with pytest.raises(Exception):
        NeoSchema.add_col_data_merge(class_internal_id=class_internal_id,
                                property_name="UNKNOWN", value_list=[1, 2])     # Property not in Schema Class



def test_add_data_point_new(db):
    db.empty_dbase()

    with pytest.raises(Exception):
        NeoSchema.add_data_point_new(class_internal_id=123)     # No such class exists

    class_internal_id , _ = NeoSchema.create_class("No data nodes allowed", no_datanodes = True)
    with pytest.raises(Exception):
        NeoSchema.add_data_point_new(class_internal_id=class_internal_id)   # The Class doesn't allow data nodes

    class_internal_id , class_schema_id = NeoSchema.create_class("Car", schema_type="S")

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 0

    # Successfully adding the first data point
    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id)
    assert NeoSchema.count_data_points_of_class(class_internal_id) == 1

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]   # No other properties were set


    with pytest.raises(Exception):
        NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                     properties={"color": "No properties allowed"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 2nd data point
    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                                   properties={"color": "No properties allowed"},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 2

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car']}]]   # No other properties were set


    # Successfully adding a 3rd data point
    NeoSchema.add_properties_to_class(class_internal_id=class_internal_id, property_list=["color"]) # Expand the allow class properties

    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                                   properties={"color": "white"})

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 3

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'white'}]]   # This time the properties got set


    # Again expand the allowed class properties
    NeoSchema.add_properties_to_class(class_internal_id=class_internal_id, property_list=["year"])

    with pytest.raises(Exception):
        NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                     properties={"color": "white", "make": "Toyota"},
                                     silently_drop=False)   # Trying to set a non-allowed property


    # Successfully adding a 4th data point
    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                                   properties={"color": "red", "make": "VW"},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 4

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'red'}]]   # The "color" got set, while the "make" got dropped


    # Successfully adding a 5th data point
    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                                   properties={"color": "blue", "make": "Fiat", "year": 2000},
                                                   silently_drop=True)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 5

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'blue', 'year': 2000}]]
    # The "color" and "year" got set, while the "make" got dropped


    # Successfully adding a 6th data point
    new_datanode_id = NeoSchema.add_data_point_new(class_internal_id=class_internal_id,
                                                   properties={"color": "green", "year": 2022},
                                                   silently_drop=False)

    assert NeoSchema.count_data_points_of_class(class_internal_id) == 6

    # Locate the data point just added
    q = f'''
    MATCH (n :Car)-[:SCHEMA]->(cl :CLASS) 
    WHERE id(n) = {new_datanode_id}
    RETURN n
    '''
    result = db.query_extended(q)
    assert len(result) == 1
    assert result == [[{'internal_id': new_datanode_id, 'neo4j_labels': ['Car'], 'color': 'green', 'year': 2022}]]
    # All properties got set



def test_add_data_point_fast(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its Neo4j ID
    doctor_neo_id = NeoSchema.add_data_point_fast_OBSOLETE(class_name="doctor",
                                                           properties={"name": "Dr. Preeti", "specialty": "sports medicine"})

    q = '''
        MATCH (d:doctor {name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]->(c:CLASS {name: "doctor"})
        WHERE id(d) = $doctor_neo_id
        RETURN d, c
        '''
    result = db.query(q, data_binding={"doctor_neo_id": doctor_neo_id})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c"]["name"] == "doctor"
    assert record["d"] == {"name":"Dr. Preeti", "specialty":"sports medicine"}


    # Create a new data point for a "patient", linked to the existing "doctor" data point
    patient_neo_id = NeoSchema.add_data_point_fast_OBSOLETE(class_name="patient",
                                                            properties={"name": "Jill", "age": 22, "balance": 145.50},
                                                            connected_to_neo_id = doctor_neo_id,
                                                            rel_name= "IS_ATTENDED_BY", rel_dir="OUT")

    q = '''
        MATCH (cp:CLASS {name: "patient"})<-[:SCHEMA]
        - (p :patient {name: "Jill", age: 22, balance: 145.50})-[:IS_ATTENDED_BY]
        -> (d :doctor {name:"Dr. Preeti", specialty:"sports medicine"})
        -[:SCHEMA]->(cd:CLASS {name: "doctor"})<-[:IS_ATTENDED_BY]-(cp)
        WHERE id(d) = $doctor_neo_id AND id(p) = $patient_neo_id
        RETURN p, d, cp, cd
        '''
    result = db.query(q, data_binding={"doctor_neo_id": doctor_neo_id, "patient_neo_id": patient_neo_id})
    assert len(result) == 1


    # Create a new data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of an autoincrement "item_id" to the new data node
    result_neo_id = NeoSchema.add_data_point_fast_OBSOLETE(class_name="result",
                                                           properties={"biomarker": "glucose", "value": 99.0},
                                                           connected_to_neo_id = patient_neo_id,
                                                           rel_name= "HAS_RESULT", rel_dir="IN",
                                                           assign_item_id= True)

    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r :result {biomarker: "glucose", value: 99.0})
        WHERE id(p) = $patient_neo_id AND id(r) = $result_neo_id
        RETURN p, cp, cr, r
        '''
    result = db.query(q, data_binding={"patient_neo_id": patient_neo_id,
                                       "result_neo_id": result_neo_id
                                       })
    assert len(result) == 1
    #print(result)
    record = result[0]
    assert record['r']['item_id'] == 1  # The first auto-increment value


    # Create a 2nd data point for a "result", linked to the existing "patient" data point;
    #   this time, request the assignment of specific "item_id" to the new data node
    result2_neo_id = NeoSchema.add_data_point_fast_OBSOLETE(class_name="result",
                                                            properties={"biomarker": "cholesterol", "value": 180.0},
                                                            connected_to_neo_id = patient_neo_id,
                                                            rel_name="HAS_RESULT", rel_dir="IN",
                                                            new_item_id=9999)
    q = '''
        MATCH (p :patient {name: "Jill", age: 22, balance: 145.50})-[:SCHEMA]->(cp:CLASS {name: "patient"})
        -[:HAS_RESULT]->(cr:CLASS {name: "result"})<-[:SCHEMA]-(r2 :result {biomarker: "cholesterol", value: 180.0})
        WHERE id(p) = $patient_neo_id AND id(r2) = $result_neo_id
        RETURN p, cp, cr, r2
        '''
    result = db.query(q, data_binding={"patient_neo_id": patient_neo_id,
                                       "result_neo_id": result2_neo_id
                                       })
    assert len(result) == 1
    print(result)
    record = result[0]
    assert record['r2']['item_id'] == 9999      # The specific "item_id" that was passed



def test_add_data_point(db):
    #TODO: also test the connected_to_id arguments
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    # Create a new data point, and get its item_id
    doctor_data_id = NeoSchema.add_data_point(class_name="doctor",
                                              data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                              return_item_ID=True)

    # Create a new data point, and this time get its Neo4j ID
    result_neo_id = NeoSchema.add_data_point(class_name="result",
                                             data_dict={"biomarker": "glucose", "value": 99.0},
                                             return_item_ID=False)

    q = '''
        MATCH (d:doctor {item_id: $doctor, name:"Dr. Preeti", specialty:"sports medicine"})-[:SCHEMA]-(c1:CLASS)
            -[*]-
            (c2:CLASS)<-[:SCHEMA]-(r:result {biomarker: "glucose", value: 99.0})
        WHERE id(r) = $result_neo_id
        RETURN d, c1, c2, r
        '''

    #db.debug_print(q, data_binding={"doctor": doctor_data_id, "result_neo_id": result_neo_id}, force_output=True)

    result = db.query(q, data_binding={"doctor": doctor_data_id, "result_neo_id": result_neo_id})
    #print("result:", result)
    assert len(result) == 1

    record = result[0]
    assert record["c1"]["name"] == "doctor"
    assert record["c2"]["name"] == "result"



def test_add_and_link_data_point(db):
    db.empty_dbase()

    create_sample_schema_1()    # Schema with patient/result/doctor

    doctor_neo_id = NeoSchema.add_data_point(class_name="doctor",
                                             data_dict={"name": "Dr. Preeti", "specialty": "sports medicine"},
                                             return_item_ID=False)

    result_neo_id = NeoSchema.add_data_point(class_name="result",
                                            data_dict={"biomarker": "glucose", "value": 99.0},
                                            return_item_ID=False)

    patient_neo_id = NeoSchema.add_and_link_data_point_OBSOLETE(class_name="patient",
                                                                properties={"name": "Jill", "age": 19, "balance": 312.15},
                                                                connected_to_list = [ (doctor_neo_id, "IS_ATTENDED_BY") , (result_neo_id, "HAS_RESULT") ])

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

    data_binding = {"patient": patient_neo_id, "doctor": doctor_neo_id, "result": result_neo_id}
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
                                                   connected_to_list = [ (doctor_neo_id, "NOT_A_DECLARED_RELATIONSHIP") , (result_neo_id, "HAS_RESULT") ])


    # Attempt to use a Class not in the Schema
    with pytest.raises(Exception):
        NeoSchema.add_and_link_data_point_OBSOLETE(class_name="NO_SUCH CLASS",
                                                   properties={"name": "Jill", "age": 19, "balance": 312.15},
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

    _ , person_class_id = NeoSchema.create_class("Person")
    person_id = NeoSchema.add_data_point("Person")

    _ , car_class_id = NeoSchema.create_class("Car")
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

    # Now, finally, it'll work
    NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="DRIVES", id_type="item_id")

    # Verify the cycle of "DRIVES" relationships
    q = '''
    MATCH (c:Car {item_id:$car_id})<-[:DRIVES]-(p:Person {item_id:$person_id})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})-[:DRIVES]->(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_id": car_id, "person_id": person_id}, single_cell="number_cars")
    assert result == 1


    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="DRIVES", id_type="item_id")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship(from_id=person_id, to_id=car_id, rel_name="SOME_OTHER_NAME", id_type="item_id")


    # Now add reverse a relationship, and this time use the Neo4j ID's to locate the nodes
    NeoSchema.create_class_relationship(from_id=car_class_id, to_id=person_class_id, rel_name="IS_DRIVEN_BY")

    neo_person_id = NeoSchema.get_data_point_id(person_id)
    neo_car_id = NeoSchema.get_data_point_id(car_id)
    NeoSchema.add_data_relationship(from_id=neo_car_id, to_id=neo_person_id, rel_name="IS_DRIVEN_BY")

    # Verify the cycle of "IS_DRIVEN_BY" relationships
    q = '''
    MATCH (c:Car {item_id:$car_id})-[:IS_DRIVEN_BY]->(p:Person {item_id:$person_id})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})<-[:IS_DRIVEN_BY]-(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_id": car_id, "person_id": person_id}, single_cell="number_cars")
    assert result == 1

    # Verify that the cycle of "DRIVES" relationships is also still there
    q = '''
    MATCH (c:Car {item_id:$car_id})<-[:DRIVES]-(p:Person {item_id:$person_id})
    -[:SCHEMA]->(cl1:CLASS {name:"Person"})-[:DRIVES]->(cl2:CLASS {name:"Car"})
    <-[:SCHEMA]-(c)
    RETURN COUNT(c) AS number_cars
    '''
    result = db.query(q, {"car_id": car_id, "person_id": person_id}, single_cell="number_cars")
    assert result == 1



def test_add_data_relationship_fast(db):
    db.empty_dbase()
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_fast(from_neo_id=123, to_neo_id=456, rel_name="junk")  # No such nodes exist

    neo_id_1 = db.create_node("random A")
    neo_id_2 = db.create_node("random B")
    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_fast(from_neo_id=neo_id_1, to_neo_id=neo_id_2, rel_name="junk") # Not data nodes with a Schema

    _ , person_class_id = NeoSchema.create_class("Person")
    person_neo_id = NeoSchema.add_data_point_fast_OBSOLETE("Person")

    _ , car_class_id = NeoSchema.create_class("Car")
    car_neo_id = NeoSchema.add_data_point_fast_OBSOLETE("Car")

    with pytest.raises(Exception):
        # No such relationship exists between their Classes
        NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name="DRIVES")

    # Add the "DRIVE" relationship between the Classes
    NeoSchema.create_class_relationship(from_id=person_class_id, to_id=car_class_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name="")  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name=None)  # Lacks relationship name

    with pytest.raises(Exception):
        NeoSchema.add_data_relationship_fast(from_neo_id=car_neo_id, to_neo_id=person_neo_id, rel_name="DRIVES")  # Wrong direction

    # Now it works
    NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Attempting to add it again
        NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name="DRIVES")

    with pytest.raises(Exception):
        # Relationship name not declared in the Schema
        NeoSchema.add_data_relationship_fast(from_neo_id=person_neo_id, to_neo_id=car_neo_id, rel_name="SOME_OTHER_NAME")


    # Now add reverse a relationship between the Classes
    NeoSchema.create_class_relationship(from_id=car_class_id, to_id=person_class_id, rel_name="IS_DRIVEN_BY")

    # Add that same reverse relationship between the data points
    NeoSchema.add_data_relationship_fast(from_neo_id=car_neo_id, to_neo_id=person_neo_id, rel_name="IS_DRIVEN_BY")



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




#############   DATA IMPORT   ###########

# See separate file


#############   EXPORT SCHEMA   ###########


###############   INTERNAL  METHODS   ###############

def test_valid_schema_id(db):
    db.empty_dbase()
    _ , result = NeoSchema.create_class("Records")
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



###############   For class "SchemaCache"   ###############

def test_cache_class_data(db):
    db.empty_dbase()
    cache = SchemaCache()

    with pytest.raises(Exception):
        cache.cache_class_data("My first class")        # Class doesn't yet exist in the Schema

    neo_id, schema_id = NeoSchema.create_class("My first class")

    cache.cache_class_data("My first class")

    internal = cache._schema
    assert len(internal) == 1
    assert internal == {'My first class':
                            {'neo_id': neo_id, 'properties': [], 'out_links': [], 'out_neighbors': {}}
                        }

    # Expand the Schema
    schema_info = create_sample_schema_1()      # Schema with patient/result/doctor
                                                # Returns dict of the form {"patient": sch_1, "result": sch_2, "doctor": sch_3}

    cache.cache_class_data("patient")
    cache.cache_class_data("doctor")
    cache.cache_class_data("result")
    with pytest.raises(Exception):
        cache.cache_class_data("I_DONT_EXIST")

    internal = cache._schema
    assert len(internal) == 4       # 4 Classes cached so far

    assert internal['My first class'] == {'neo_id': neo_id, 'properties': [], 'out_links': [], 'out_neighbors': {}}

    patient_neo_id = NeoSchema.get_class_internal_id("patient")
    patient_schema_id = schema_info["patient"]
    assert internal['patient']['neo_id'] == patient_neo_id
    #assert internal['patient']['schema_id'] == patient_schema_id
    assert internal['patient']['properties'] == ['name', 'age', 'balance']
    assert compare_unordered_lists(internal['patient']['out_links'] , ['HAS_RESULT', 'IS_ATTENDED_BY'])
    assert internal['patient']['out_neighbors'] == {'HAS_RESULT': 'result', 'IS_ATTENDED_BY': 'doctor'}

    doctor_neo_id = NeoSchema.get_class_internal_id("doctor")
    doctor_schema_id = schema_info["doctor"]
    assert internal['doctor']['neo_id'] == doctor_neo_id
    #assert internal['doctor']['schema_id'] == doctor_schema_id
    assert internal['doctor']['properties'] == ['name', 'specialty']
    assert internal['doctor']['out_links'] == []
    assert internal['doctor']['out_neighbors'] == {}

    result_neo_id = NeoSchema.get_class_internal_id("result")
    result_schema_id = schema_info["result"]
    assert internal['result']['neo_id'] == result_neo_id
    #assert internal['result']['schema_id'] == result_schema_id
    assert internal['result']['properties'] == ['biomarker', 'value']
    assert internal['result']['out_links'] == []
    assert internal['result']['out_neighbors'] == {}

    #print(internal)



def test_get_class_cached_data(db):
    db.empty_dbase()
    cache = SchemaCache()

    with pytest.raises(Exception):
        cache.get_class_cached_data("My first class")        # Class doesn't yet exist in the Schema

    neo_id , schema_id = NeoSchema.create_class("My first class")

    cache = SchemaCache()

    data = cache.get_class_cached_data("My first class")

    assert len(data) == 4
    assert data == {'neo_id': neo_id, 'properties': [], 'out_links': [], 'out_neighbors': {}}

    # Expand the Schema
    schema_info = create_sample_schema_1()      # Schema with patient/result/doctor
                                                # Returns dict of the form {"patient": sch_1, "result": sch_2, "doctor": sch_3}

    with pytest.raises(Exception):
        cache.get_class_cached_data("I_DONT_EXIST")


    assert cache.get_class_cached_data('My first class') == \
           {'neo_id': neo_id, 'properties': [], 'out_links': [], 'out_neighbors': {}}

    cached_data = cache.get_class_cached_data('patient')
    patient_neo_id = NeoSchema.get_class_internal_id("patient")
    patient_schema_id = schema_info["patient"]
    assert cached_data['neo_id'] == patient_neo_id
    #assert cached_data['schema_id'] == patient_schema_id
    assert cached_data['properties'] == ['name', 'age', 'balance']
    assert compare_unordered_lists(cached_data['out_links'] , ['HAS_RESULT', 'IS_ATTENDED_BY'])
    assert cached_data['out_neighbors'] == {'HAS_RESULT': 'result', 'IS_ATTENDED_BY': 'doctor'}

    cached_data = cache.get_class_cached_data('doctor')
    doctor_neo_id = NeoSchema.get_class_internal_id("doctor")
    doctor_schema_id = schema_info["doctor"]
    assert cached_data['neo_id'] == doctor_neo_id
    #assert cached_data['schema_id'] == doctor_schema_id
    assert cached_data['properties'] == ['name', 'specialty']
    assert cached_data['out_links'] == []
    assert cached_data['out_neighbors'] == {}

    cached_data = cache.get_class_cached_data('result')
    result_neo_id = NeoSchema.get_class_internal_id("result")
    result_schema_id = schema_info["result"]
    assert cached_data['neo_id'] == result_neo_id
    #assert cached_data['schema_id'] == result_schema_id
    assert cached_data['properties'] == ['biomarker', 'value']
    assert cached_data['out_links'] == []
    assert cached_data['out_neighbors'] == {}
