# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.collections.collections import Collections


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    Collections.set_database(neo_obj)

    yield neo_obj



# ************  CREATE A SAMPLE COLLECTION for the testing  **************

def initialize_collections(db):
    # Clear the dbase, create a sample Collection named "Album" (a Class with a "name" and "uri" properties

    db.empty_dbase()

    Collections.create_collections_class()

    NeoSchema.create_class_with_properties(name="Album",
                                           property_list=["name", "uri"])

    NeoSchema.create_class_relationship(from_class="Album", to_class="Collections",
                                        rel_name="INSTANCE_OF", use_link_node=False)





# ************  THE ACTUAL TESTS  ************

def test_is_collection(db):
    initialize_collections(db)

    new_uri = NeoSchema.reserve_next_uri(prefix="album-")   # Use default namespace

    NeoSchema.create_data_node(class_node="Album", properties ={"name": "Jamaica vacation"}, new_uri=new_uri)

    assert Collections.is_collection(collection_uri=new_uri)

    assert not Collections.is_collection(collection_uri="some random string that is not a URI")


    # Create something that is NOT a collection
    NeoSchema.create_class_with_properties(name="Car",
                                           property_list=["color", "uri"])
    car_uri = NeoSchema.reserve_next_uri(namespace="cars", prefix="c-")
    NeoSchema.create_data_node(class_node="Car", properties ={"color": "white"}, new_uri=car_uri)
    assert not Collections.is_collection(collection_uri=car_uri)

