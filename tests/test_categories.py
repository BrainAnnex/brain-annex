# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from neoaccess import NeoAccess
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.collections.collections import Collections


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    Categories.db = neo_obj
    Collections.set_database(neo_obj)
    yield neo_obj



# ************  CREATE SAMPLE CATEGORIES for the testing  **************

def initialize_categories(db):
    # Clear the dbase, create the Category Schema, and creates a ROOT Category node;
    # return the internal database ID and URI of the new Categories node

    db.empty_dbase()

    NeoSchema.create_class_with_properties(name="Categories",
                                           property_list=["name", "remarks", "uri"])

    return Categories.create_categories_root()  # Returns a pair (int, str)





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

    root_internal_id, _ = initialize_categories(db)
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



def test_get_items_schema_data(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {}    # There are no Contents Items yet attached to the Category

    NeoSchema.create_class_with_properties(name="Notes", property_list=["title", "basename", "suffix"])
    NeoSchema.create_class_with_properties(name="Images", property_list=["caption", "basename", "suffix", "uri"])

    # Add some Content Items to the above Category
    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Notes",
                                 item_properties={"title": "My 1st note"})

    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Notes': ['title', 'basename', 'suffix']}

    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Images",
                                  item_properties={"caption": "vacation pic", "basename": "pic1", "suffix": "jpg"})
    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Notes': ['title', 'basename', 'suffix'], 'Images': ['caption', 'basename', 'suffix', 'uri']}

    # Make the "uri" property of the Class "Images" to be a "system" property
    NeoSchema.set_property_attribute(class_name="Images", prop_name="uri",
                                     attribute_name="system", attribute_value=True)
    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Notes': ['title', 'basename', 'suffix'], 'Images': ['caption', 'basename', 'suffix']}   # 'uri' is no longer included



def test_link_content_at_end(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    NeoSchema.create_class_with_properties(name="Images",
                                           property_list=["caption", "basename", "suffix", "uri"])
    NeoSchema.create_class_relationship(from_class="Images", to_class="Categories",
                                        rel_name="BA_in_category")

    # Create a new Data Node
    NeoSchema.create_data_node(class_node="Images", properties={"caption": "my_pic"},
                               assign_uri=False, new_uri="i-100")

    Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100", label=None)

    # Verify that all nodes and links are in place
    q = f'''
        MATCH p=(:CLASS {{name:"Images"}})
        <-[:SCHEMA]-
        (:Images {{caption:"my_pic", uri:"i-100"}})
        -[:BA_in_category]->
        (:Categories {{uri: "{root_uri}"}})
        -[:SCHEMA]->
        (:CLASS {{name:"Categories"}}) 
        RETURN COUNT(p) AS path_count
        '''
    result = db.query(q, single_cell="path_count")
    assert result == 1

    with pytest.raises(Exception):
        # Link already exists
        Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100", label=None)

    # TODO: additional testing



def test_detach_from_category(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    NeoSchema.create_class_with_properties(name="Images", property_list=["caption", "basename", "suffix", "uri"])
    NeoSchema.create_class_relationship(from_class="Images", to_class="Categories",
                                        rel_name="BA_in_category")

    # Create a new Data Node
    NeoSchema.create_data_node(class_node="Images", properties={"caption": "my_pic"},
                               assign_uri=False, new_uri="i-100")

    Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100", label=None)

    with pytest.raises(Exception):
        # It would leave the Content Item "stranded"
        Categories.detach_from_category(category_uri=root_uri, item_uri="i-100")


    # Create a 2nd Category, and link up the Content Item to it
    new_cat_uri = Categories.add_subcategory({"category_id":root_uri,  "subcategory_name": "math"})
    Categories.link_content_at_end(category_uri=new_cat_uri, item_uri="i-100", label=None)

    # Now, the detachment of the Content Item from the initial (root) Category is possible
    Categories.detach_from_category(category_uri=root_uri, item_uri="i-100")

    # Verify that nodes and links are in place
    q = f'''
        MATCH p=(:CLASS {{name:"Images"}})
        <-[:SCHEMA]-
        (:Images {{caption:"my_pic", uri:"i-100"}})
        -[:BA_in_category]->
        (:Categories {{uri: "{new_cat_uri}"}})
        -[:SCHEMA]->
        (:CLASS {{name:"Categories"}}) 
        RETURN COUNT(p) AS path_count
        '''
    result = db.query(q, single_cell="path_count")
    assert result == 1
