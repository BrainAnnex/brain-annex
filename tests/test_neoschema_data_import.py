# Testing of Schema-based Data Import
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



def test_create_data_nodes_from_python_data_1(db):
    db.empty_dbase()

    # 1-layer dictionary, with a key in the Schema and one not

    data = {"legit": 123, "unexpected": 456}
    NeoSchema.new_class_with_properties(class_name="my_class_1",
                                        property_list=["legit", "other"])

    node_id_list = NeoSchema.create_data_nodes_from_python_data(data, class_name="my_class_1")
    assert len(node_id_list) == 1
    root_id = node_id_list[0]
    result = db.fetch_nodes(match=root_id, single_row=True)
    assert result == {"legit": 123}     # Only the key in the Schema gets imported
    assert db.get_node_labels(root_id) == ["my_class_1"]
