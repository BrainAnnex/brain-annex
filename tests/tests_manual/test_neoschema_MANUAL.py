import pytest
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.utilities.comparisons import compare_recordsets
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=True)
    NeoSchema.db = neo_obj
    #yield neo_obj



def test_get_class_relationships(db):
    result = NeoSchema.get_class_relationships(47)
    print(result)
    assert result == (['INSTANCE_OF', 'BA_located_in', 'BA_cuisine_type'], ['BA_served_at'])

    result = NeoSchema.get_class_relationships(47, omit_instance=True)
    print(result)
    assert result == (['BA_located_in', 'BA_cuisine_type'], ['BA_served_at'])


def test_data_points_of_class(db):
    all_category_ids = NeoSchema.data_points_of_class("Categories")
    print(all_category_ids)
    assert len(all_category_ids) == 27