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



#############   CLASS-related   #############

def test_create_class(db):
    db.empty_dbase()

    french_class_id = NeoSchema.create_class("French Vocabulary")
    result = db.get_nodes()
    assert result == [{'name': 'French Vocabulary', 'schema_id': french_class_id, 'type': 'L'}]

    class_A_id = NeoSchema.create_class("A", schema_type="S")
    result = db.get_nodes()
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



#############   PROPERTIES-RELATED   #############


#############   SCHEMA-CODE  RELATED   ###########

#############   DATA POINTS   ###########

#############   EXPORT SCHEMA   ###########


###############   INTERNAL  METHODS   ###############

def test_valid_schema_id(db):
    db.empty_dbase()    # Completely clear the database
    result = NeoSchema.create_class("Records")
    assert NeoSchema.valid_schema_id(result)
