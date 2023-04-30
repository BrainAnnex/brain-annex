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

def initialize_categories(db):
    # Clear the dbase, create the Category Schema, and creats a ROOT category node

    db.empty_dbase()

    node_internal_id, _ = NeoSchema.create_class_with_properties(class_name="Categories",
                                                                 property_list=["name", "remarks"])

    Categories.create_categories_root()





# ************  THE ACTUAL TESTS  ************

def test_get_all_categories(db):

    initialize_categories(db)

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    assert result == [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'}]

    result = Categories.get_all_categories(exclude_root=False, include_remarks=False)
    assert result == [{'item_id': 1, 'name': 'HOME'}]

    result = Categories.get_all_categories(exclude_root=True, include_remarks=True)
    assert result == []

    # Add a new Category ("Languages")
    language_item_id = Categories.add_subcategory({"category_id": 1, "subcategory_name": "Languages",
                                "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'item_id': language_item_id, 'name': 'Languages', 'remarks': 'Common node for all languages'}]
    compare_recordsets(result, expected)

    # Add 2 new Categories ("French" and "Italian")
    french_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "French"})
    italian_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "Italian"})
    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'item_id': language_item_id, 'name': 'Languages', 'remarks': 'Common node for all languages'},
                {'item_id': french_item_id, 'name': 'French'}, {'item_id': italian_item_id, 'name': 'Italian'}]
    compare_recordsets(result, expected)



def test_get_sibling_categories(db):

    initialize_categories(db)

    # Add a new Category ("Languages")
    language_item_id = Categories.add_subcategory({"category_id": 1, "subcategory_name": "Languages",
                                                   "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'item_id': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'item_id': language_item_id, 'name': 'Languages', 'remarks': 'Common node for all languages'}]
    compare_recordsets(result, expected)

    # Add 2 new Categories ("French" and "Italian")
    french_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "French"})
    italian_item_id = Categories.add_subcategory({"category_id": language_item_id, "subcategory_name": "Italian"})

    french_internal_id = NeoSchema.get_data_point_internal_id(item_id = french_item_id)
    italian_internal_id = NeoSchema.get_data_point_internal_id(item_id = italian_item_id)

    result = Categories.get_sibling_categories(french_internal_id)

    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "Italian"
    assert entry["item_id"] == italian_item_id
    assert entry["internal_id"] == italian_internal_id
    assert compare_unordered_lists(entry["neo4j_labels"], ['Categories', 'BA'])
