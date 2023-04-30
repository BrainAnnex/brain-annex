# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema, SchemaCache, SchemaCacheExperimental
from BrainAnnex.modules.categories.categories import Categories


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    Categories.db = neo_obj
    yield neo_obj



# ************  CREATE SAMPLE CATEGORIES for the testing  **************

def create_root_category():
    # Create the ROOT category, and its Schema

    node_internal_id, _ = NeoSchema.create_class_with_properties(class_name="Categories",
                                                                 property_list=["name", "remarks"])

    NeoSchema.add_data_point(class_internal_id = node_internal_id, properties = {"name": "HOME", "remarks": "top level"},
                             new_item_id =1 )



def create_sample_category_2():
    # Class "quotes" with relationship named "in_category" to Class "categories";
    # each Class has some properties
    _, sch_1 = NeoSchema.create_class_with_properties(class_name="quotes",
                                                      property_list=["quote", "attribution", "verified"])

    _, sch_2 = NeoSchema.create_class_with_properties(class_name="categories",
                                                      property_list=["name", "remarks"])

    NeoSchema.create_class_relationship(from_id=sch_1, to_id=sch_2, rel_name="in_category")

    return {"quotes": sch_1, "categories": "sch_2"}





def test_get_all_categories(db):
    db.empty_dbase()

    create_root_category()

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    assert result == [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'}]

    result = Categories.get_all_categories(exclude_root=False, include_remarks=False)
    assert result == [{'item_id': 1, 'name': 'HOME'}]

    result = Categories.get_all_categories(exclude_root=True, include_remarks=True)
    assert result == []

    # Add a new Category
    language_item_id = Categories.add_subcategory({"category_id": 1, "subcategory_name": "Languages",
                                "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'item_id': language_item_id, 'name': 'Languages', 'remarks': 'Common node for all languages'}]
    compare_recordsets(result, expected)

    # Add 2 new Categories
    french_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "French"})
    italian_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "Italian"})
    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)

    print(result)
