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
