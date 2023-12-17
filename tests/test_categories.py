# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
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
    # Clear the dbase, create the Category Schema, and creates a ROOT Category node;
    # return the internal database ID of the new Categories node

    db.empty_dbase()

    node_internal_id, _ = NeoSchema.create_class_with_properties(name="Categories",
                                                                 property_list=["name", "remarks"])

    return Categories.create_categories_root()





# ************  THE ACTUAL TESTS  ************

def test_get_all_categories(db):

    initialize_categories(db)

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    assert result == [{'uri': '1', 'name': 'HOME', 'remarks': 'top level'}]

    result = Categories.get_all_categories(exclude_root=False, include_remarks=False)
    assert result == [{'uri': '1', 'name': 'HOME'}]

    result = Categories.get_all_categories(exclude_root=True, include_remarks=True)
    assert result == []

    # Add a new Category ("Languages")
    language_uri = Categories.add_subcategory({"category_id": "1", "subcategory_name": "Languages",
                                "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'uri': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'uri': language_uri, 'name': 'Languages', 'remarks': 'Common node for all languages'}]
    compare_recordsets(result, expected)

    # Add 2 new Categories ("French" and "Italian")
    french_uri = Categories.add_subcategory({"category_id": language_uri, "subcategory_name": "French"})
    italian_uri = Categories.add_subcategory({"category_id": language_uri, "subcategory_name": "Italian"})
    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'uri': 1, 'name': 'HOME', 'remarks': 'top level'},
                {'uri': language_uri, 'name': 'Languages', 'remarks': 'Common node for all languages'},
                {'uri': french_uri, 'name': 'French'}, {'uri': italian_uri, 'name': 'Italian'}]
    compare_recordsets(result, expected)



def test_get_sibling_categories(db):

    root_internal_id = initialize_categories(db)
    result = Categories.get_sibling_categories(root_internal_id)
    assert result == []     # The root node has no siblings

    # Add a new Category ("Languages")
    language_uri = Categories.add_subcategory({"category_id": "1", "subcategory_name": "Languages",
                                                   "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_sibling_categories(root_internal_id)
    assert result == []     # The "Languages" node has no siblings

    # Add 2 new Categories ("French" and "Italian"), both subcategories of "Languages"
    french_uri = Categories.add_subcategory({"category_id": language_uri, "subcategory_name": "French"})
    italian_uri = Categories.add_subcategory({"category_id": language_uri, "subcategory_name": "Italian"})

    french_internal_id = NeoSchema.get_data_node_internal_id(uri = french_uri)
    italian_internal_id = NeoSchema.get_data_node_internal_id(uri = italian_uri)

    result = Categories.get_sibling_categories(french_internal_id)
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "Italian"   # The sibling of "French" is "Italian"
    assert entry["uri"] == italian_uri
    assert entry["internal_id"] == italian_internal_id
    #assert compare_unordered_lists(entry["neo4j_labels"], ['Categories', 'BA'])

    result = Categories.get_sibling_categories(italian_internal_id)
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "French"   # The sibling of "Italian" is "French"

    expected = {"name": "French", "uri": french_uri, "internal_id": french_internal_id, "neo4j_labels": ['BA', 'Categories']}

    # We'll check the node labels separately, because their order may be reshuffled
    assert compare_unordered_lists(entry["neo4j_labels"], expected["neo4j_labels"])

    del entry["neo4j_labels"]
    del expected["neo4j_labels"]
    assert entry == expected

    # Add a new Categories ("German") as a subcategories of "Languages"
    Categories.add_subcategory({"category_id": language_uri, "subcategory_name": "German"})

    result = Categories.get_sibling_categories(french_internal_id)
    assert len(result) == 2     # Now, "French" has 2 siblings
    sibling_names = [d["name"] for d in result]
    assert compare_unordered_lists(sibling_names, ["Italian", "German"])
