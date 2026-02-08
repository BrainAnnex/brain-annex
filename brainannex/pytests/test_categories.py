# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from brainannex import GraphAccess, GraphSchema, Collections, Categories
from utilities.comparisons import compare_unordered_lists, compare_recordsets



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    GraphSchema.set_database(neo_obj)
    Categories.db = neo_obj
    Collections.set_database(neo_obj)
    yield neo_obj



# ************  CREATE CATEGORY CLASS AND ROOT CATEGORY for the testing  **************

def initialize_categories(db):
    # Clear the dbase, create the Category Schema, and creates a ROOT Category node;
    # return the pair (internal database ID, URI) of that newly-created root node

    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    Categories.add_to_schema()

    return Categories.create_categories_root()  # Returns a pair (int|str, str)
                                                # The root node contains the properties:
                                                # {"name": "HOME", "remarks": "top level", "uri": "1", "root": True}





# ************  THE ACTUAL TESTS  ************

def test_add_to_schema(db):
    pass


def test_get_category_info(db):
    _, root_uri = initialize_categories(db)

    result = Categories.get_category_info(root_uri)

    assert result == {'root': True, 'name': 'HOME', 'uri': '1', 'remarks': 'top level'}
    #TODO: more tests



def test_is_root_category(db):
    _, root_uri = initialize_categories(db)

    assert Categories.is_root_category(root_uri)
    #TODO: more tests



def test_get_root_uri(db):
    _, root_uri = initialize_categories(db)

    assert Categories.get_root_uri() == root_uri
    #TODO: more tests



def test_get_all_categories(db):

    _, root_uri = initialize_categories(db)

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    assert result == [{'uri': root_uri, 'name': 'HOME', 'remarks': 'top level'}]

    result = Categories.get_all_categories(exclude_root=False, include_remarks=False)
    assert result == [{'uri': root_uri, 'name': 'HOME'}]

    result = Categories.get_all_categories(exclude_root=True, include_remarks=True)
    assert result == []

    # Add a new Category ("Languages")
    language_uri = Categories.add_subcategory(data_dict={"category_uri": root_uri,
                                                         "subcategory_name": "Languages",
                                                          "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'uri': root_uri, 'name': 'HOME', 'remarks': 'top level'},
                {'uri': language_uri, 'name': 'Languages', 'remarks': 'Common node for all languages'}]
    compare_recordsets(result, expected)

    # Add 2 new Categories ("French" and "Italian")
    french_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "French"})
    italian_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "Italian"})
    result = Categories.get_all_categories(exclude_root=False, include_remarks=True)
    expected = [{'uri': root_uri, 'name': 'HOME', 'remarks': 'top level'},
                {'uri': language_uri, 'name': 'Languages', 'remarks': 'Common node for all languages'},
                {'uri': french_uri, 'name': 'French'}, {'uri': italian_uri, 'name': 'Italian'}]
    compare_recordsets(result, expected)



def test_count_subcategories(db):
    root_internal_id, root_uri = initialize_categories(db)
    result = Categories.get_parent_categories(root_uri)
    assert result == []     # The root node has no children yet

    # Add a sub-category ("Languages") to the root
    language_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Languages",
                                               "subcategory_remarks": "Common node for all languages"})

    assert Categories.count_subcategories(root_uri) == 1
    assert Categories.count_subcategories(language_uri) == 0    # The "Languages" node has no children

    # Add a 2nd sub-category ("Courses") to the root
    courses_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Courses"})

    assert Categories.count_subcategories(root_uri) == 2
    assert Categories.count_subcategories(language_uri) == 0
    assert Categories.count_subcategories(courses_uri) == 0

    # Add a sub-category ("French") to "Languages"
    french_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "French"})
    assert Categories.count_subcategories(root_uri) == 2
    assert Categories.count_subcategories(language_uri) == 1    # Now has a child
    assert Categories.count_subcategories(courses_uri) == 0
    assert Categories.count_subcategories(french_uri) == 0

    # Make the "French" also a child of "Courses"
    Categories.add_subcategory_relationship(subcategory_uri=french_uri, category_uri=courses_uri)
    assert Categories.count_subcategories(root_uri) == 2
    assert Categories.count_subcategories(language_uri) == 1
    assert Categories.count_subcategories(courses_uri) == 1        # Now has a child
    assert Categories.count_subcategories(french_uri) == 0



def test_count_parent_categories(db):
    root_internal_id, root_uri = initialize_categories(db)
    result = Categories.get_parent_categories(root_uri)
    assert result == []     # The root node has no parents

    # Add a sub-category ("Languages") to the root
    language_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Languages",
                                               "subcategory_remarks": "Common node for all languages"})

    assert Categories.count_parent_categories(language_uri) == 1    # The "Languages" node has 1 parent (the root)

    # Add a 2nd sub-category ("Courses") to the root
    courses_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Courses"})

    assert Categories.count_parent_categories(courses_uri) == 1     # The "Courses" node has 1 parent (the root)

    # Add a sub-category ("French") to "Languages"
    french_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "French"})
    assert Categories.count_parent_categories(french_uri) == 1      # The "French" node has 1 parent ("Languages")

    # Make the "French" also a child of "Courses"
    Categories.add_subcategory_relationship(subcategory_uri=french_uri, category_uri=courses_uri)
    # The "French" node will now have 2 parents ("Languages" and "Courses)
    assert Categories.count_parent_categories(french_uri) == 2


def test_get_subcategories(db):
    pass



def test_get_parent_categories(db):
    root_internal_id, root_uri = initialize_categories(db)
    result = Categories.get_parent_categories(root_uri)
    assert result == []     # The root node has no parents

    # Add a sub-category ("Languages") to the root
    language_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Languages",
                                               "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_parent_categories(language_uri)
    assert result == [{"name": "HOME", "remarks": "top level", "uri": root_uri, "root": True}]
    # The "Languages" node has 1 parent (the root)

    # Add a 2nd sub-category ("Courses") to the root
    courses_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Courses"})

    result = Categories.get_parent_categories(courses_uri)
    assert result == [{"name": "HOME", "remarks": "top level", "uri": root_uri, "root": True}]
    # The "Courses" node has 1 parent (the root)

    # Add a sub-category ("French") to "Languages"
    french_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "French"})
    result = Categories.get_parent_categories(french_uri)
    assert result == [{"name": "Languages", "remarks": "Common node for all languages", "uri": language_uri}]
    # The "French" node has 1 parent ("Languages")

    # Make the "French" also a child of "Courses"
    Categories.add_subcategory_relationship(subcategory_uri=french_uri, category_uri=courses_uri)
    # The "French" node will now have 2 parents ("Languages" and "Courses)
    result = Categories.get_parent_categories(french_uri)
    expected = [{"name": "Languages", "remarks": "Common node for all languages", "uri": language_uri},
                {"name": "Courses", "uri": courses_uri}]
    assert compare_recordsets(result, expected)



def test_get_ancestor_categories(db):
    _, root_uri = initialize_categories(db)

    result = Categories.get_ancestor_categories(category_uri=root_uri)
    assert result == []     # The root node has no ancestors

    A_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "A"})
    result = Categories.get_ancestor_categories(category_uri=A_uri)
    assert result == [root_uri]     # The root node is the only ancestor of Category "A"

    B_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "B"})
    result = Categories.get_ancestor_categories(category_uri=B_uri)
    assert result == [root_uri]     # The root node is the only ancestor of Category "B"

    C_uri = Categories.add_subcategory({"category_uri": A_uri, "subcategory_name": "C"})
    result = Categories.get_ancestor_categories(category_uri=C_uri)
    assert compare_unordered_lists(result, [A_uri, root_uri])

    # Make "A" a subcategory of "B"
    Categories.add_subcategory_relationship(category_uri=B_uri, subcategory_uri=A_uri)

    result = Categories.get_ancestor_categories(category_uri=A_uri)
    assert compare_unordered_lists(result, [B_uri, root_uri])

    result = Categories.get_ancestor_categories(category_uri=C_uri)
    assert compare_unordered_lists(result, [A_uri, B_uri, root_uri])



def test_get_sibling_categories(db):
    root_internal_id, root_uri = initialize_categories(db)
    result = Categories.get_sibling_categories(root_internal_id)
    assert result == []     # The root node has no siblings

    # Add a new Category ("Languages")
    language_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Languages",
                                               "subcategory_remarks": "Common node for all languages"})

    result = Categories.get_sibling_categories(root_internal_id)
    assert result == []     # The "Languages" node has no siblings

    # Add 2 new Categories ("French" and "Italian"), both subcategories of "Languages"
    french_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "French"})
    italian_uri = Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "Italian"})

    french_internal_id = GraphSchema.get_data_node_internal_id(uri = french_uri)
    italian_internal_id = GraphSchema.get_data_node_internal_id(uri = italian_uri)

    result = Categories.get_sibling_categories(french_internal_id)
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "Italian"   # The sibling of "French" is "Italian"
    assert entry["uri"] == italian_uri
    assert entry["_internal_id"] == italian_internal_id
    #assert compare_unordered_lists(entry["_node_labels"], ['Category', 'BA'])

    result = Categories.get_sibling_categories(italian_internal_id)
    assert len(result) == 1
    entry = result[0]
    assert entry["name"] == "French"   # The sibling of "Italian" is "French"

    expected = {"name": "French", "uri": french_uri, "_internal_id": french_internal_id, "_node_labels": ['BA', 'Category']}

    # We'll check the node labels separately, because their order may be reshuffled
    assert compare_unordered_lists(entry["_node_labels"], expected["_node_labels"])

    del entry["_node_labels"]
    del expected["_node_labels"]
    assert entry == expected

    # Add a new Categories ("German") as a subcategories of "Languages"
    Categories.add_subcategory({"category_uri": language_uri, "subcategory_name": "German"})

    result = Categories.get_sibling_categories(french_internal_id)
    assert len(result) == 2     # Now, "French" has 2 siblings
    sibling_names = [d["name"] for d in result]
    assert compare_unordered_lists(sibling_names, ["Italian", "German"])



def test_create_parent_map(db):
    pass


def test_create_categories_root(db):
    pass


def test_create_add_subcategory(db):
    pass

def test_delete_category(db):
    pass



def test_add_subcategory_relationship(db):
    _, root_uri = initialize_categories(db)

    A_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "A"})
    B_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "B"})

    with pytest.raises(Exception):
        # Root cannot be made a subcategory of something else
        Categories.add_subcategory_relationship(category_uri=A_uri, subcategory_uri=root_uri)

    with pytest.raises(Exception):
        # Link already exists
        Categories.add_subcategory_relationship(category_uri=root_uri, subcategory_uri=A_uri)

    with pytest.raises(Exception):
        # Sub-category of itself!
        Categories.add_subcategory_relationship(category_uri=A_uri, subcategory_uri=A_uri)


    # Make 'A' a subcategory of 'B'
    Categories.add_subcategory_relationship(category_uri=B_uri, subcategory_uri=A_uri)

    # Verify that 'A' is indeed a subcategory of 'B'
    result = Categories.get_subcategories(category_uri=B_uri)
    assert result == [{'_CLASS': 'Category', 'uri': A_uri, 'name': 'A'}]

    with pytest.raises(Exception):
        # This would create a cycle
        Categories.add_subcategory_relationship(category_uri=A_uri, subcategory_uri=B_uri)



def test_get_see_also(db):
    root_internal_id, root_uri = initialize_categories(db)

    A_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "A"})
    B_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "B"})

    Categories.create_see_also(from_category=A_uri, to_category=B_uri)

    result = Categories.get_see_also(from_category=A_uri)
    assert result == [{'name': 'B', 'remarks': None, 'uri': B_uri}]



def test_create_see_also(db):
    root_internal_id, root_uri = initialize_categories(db)

    A_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "A"})

    B_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "B"})

    Categories.create_see_also(from_category=A_uri, to_category=B_uri)

    assert db.links_exist(match_from = db.match(key_name="uri", key_value=A_uri),
                          match_to = db.match(key_name="uri", key_value=B_uri),
                          rel_name="BA_see_also")

    with pytest.raises(Exception):
        Categories.create_see_also(from_category="I don't exist", to_category=B_uri)



def test_remove_see_also(db):
    root_internal_id, root_uri = initialize_categories(db)

    A_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "A"})

    B_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "B"})

    Categories.create_see_also(from_category=A_uri, to_category=B_uri)

    Categories.remove_see_also(from_category=A_uri, to_category=B_uri)

    assert not db.links_exist(match_from = db.match(key_name="uri", key_value=A_uri),
                              match_to = db.match(key_name="uri", key_value=B_uri),
                              rel_name="BA_see_also")

    with pytest.raises(Exception):
        # Attempting to remove a non-existent link
        Categories.remove_see_also(from_category=A_uri, to_category=B_uri)



def test_import_ontology(db):
    pass





##############  CATEGORY PAGES  ##############


def test_viewer_handler(db):
    pass


def test_remove_relationship_before(db):
    pass

def test_create_bread_crumbs(db):
    pass

def test__recursive(db):
    pass


def test_pin_category(db):
    pass

def test_is_pinned(db):
    pass

def test_get_categories_linked_to_content_item(db):
    pass

def test_get_content_items_by_category(db):
    pass

def test_add_content_at_beginning(db):
    pass


def test_link_content_at_end(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    GraphSchema.create_class_with_properties(name="Image",
                                             properties=["caption", "basename", "suffix", "uri"])
    GraphSchema.create_class_relationship(from_class="Image", to_class="Category",
                                          rel_name="BA_in_category")

    # Create a new Data Node
    GraphSchema.create_data_node(class_name="Image", properties={"caption": "my_pic"},
                                 new_uri="i-100")

    Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100")

    # Verify that all nodes and links are in place
    q = f'''
        MATCH p=
        (:Image {{caption:"my_pic", uri:"i-100", `_CLASS`:"Image"}})
        -[:BA_in_category]->
        (:Category {{uri: "{root_uri}", `_CLASS`:"Category"}})
        RETURN COUNT(p) AS path_count
        '''
    result = db.query(q, single_cell="path_count")
    assert result == 1

    with pytest.raises(Exception):
        # Link already exists
        Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100")

    # TODO: additional testing



def test_add_content_at_end(db):
    pass



def test_add_content_after_element(db):
    _, root_uri = initialize_categories(db)

    # Introduce a new test Class, "Image"
    GraphSchema.create_class_with_properties(name="Image",
                                             properties=["caption", "basename", "suffix", "uri"])
    GraphSchema.create_class_relationship(from_class="Image", to_class="Category",
                                          rel_name="BA_in_category")

    # Create a new Data Node (of class "Image"), positioned at the end (bottom) of the Root Category Page
    Categories.add_content_at_end(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "USA"},
                                  new_uri="i-USA")

    q = f'''
        MATCH (c:Category {{uri: "{root_uri}"}})<-[r:BA_in_category]-(ci)
        RETURN r.pos AS pos, ci.uri AS uri
        ORDER BY pos
        '''
    result = db.query(q, single_column="uri")
    assert result == ["i-USA"]

    # Create a new Data Node (of class "Image"), positioned after the previously-added "USA" Image on the Root Category Page
    # Note: this corresponds to an "add at the end"
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "Brazil"},
                                  insert_after_uri="i-USA", insert_after_class="Image",
                                  new_uri="i-Brazil")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Brazil"]

    # Create a new Data Node (of class "Image"), positioned after the initially-added "USA" Image on the Root Category Page
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "Mexico"},
                                  insert_after_uri="i-USA", insert_after_class="Image",
                                  new_uri="i-Mexico")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Mexico", "i-Brazil"]


    # Introduce another new test Class, "Header"
    GraphSchema.create_class_with_properties(name="Header",
                                             properties=["text", "uri"])
    GraphSchema.create_class_relationship(from_class="Header", to_class="Category",
                                          rel_name="BA_in_category")

    # Create a new Data Node (of class "Header"), positioned after the "Mexico" Image on the Root Category Page
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Header", item_properties={"text": "South America"},
                                  insert_after_uri="i-Mexico", insert_after_class="Image",
                                  new_uri="i-Header-1")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Mexico", "i-Header-1", "i-Brazil"]


    # Create a new Data Node (of class "Image"), positioned after the Header item on the Root Category Page
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "Guyana"},
                                  insert_after_uri="i-Header-1", insert_after_class="Header",
                                  new_uri="i-Guyana")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Mexico", "i-Header-1", "i-Guyana", "i-Brazil"]


    # Create a new Data Node (of class "Image"), positioned after the Header item on the Root Category Page
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "Venezuela"},
                                  insert_after_uri="i-Header-1", insert_after_class="Header",
                                  new_uri="i-Venezuela")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Mexico", "i-Header-1", "i-Venezuela", "i-Guyana", "i-Brazil"]


    # Create a new Data Node (of class "Image"), positioned after the Header item on the Root Category Page
    # Note: this will force a re-numbering of the pos values
    Categories.add_content_after_element(category_uri=root_uri,
                                  item_class_name="Image", item_properties={"caption": "Colombia"},
                                  insert_after_uri="i-Header-1", insert_after_class="Header",
                                  new_uri="i-Colombia")

    result = db.query(q, single_column="uri")
    assert result == ["i-USA", "i-Mexico", "i-Header-1","i-Colombia", "i-Venezuela", "i-Guyana", "i-Brazil"]



def test_detach_from_category(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    GraphSchema.create_class_with_properties(name="Image", properties=["caption", "basename", "suffix", "uri"])
    GraphSchema.create_class_relationship(from_class="Image", to_class="Category",
                                          rel_name="BA_in_category")

    # Create a new Data Node
    GraphSchema.create_data_node(class_name="Image", properties={"caption": "my_pic"},
                                 new_uri="i-100")

    Categories.link_content_at_end(category_uri=root_uri, item_uri="i-100")

    with pytest.raises(Exception):
        # It would leave the Content Item "stranded"
        Categories.detach_from_category(category_uri=root_uri, item_uri="i-100")


    # Create a 2nd Category, and link up the Content Item to it
    new_cat_uri = Categories.add_subcategory({"category_uri":root_uri,  "subcategory_name": "math"})
    Categories.link_content_at_end(category_uri=new_cat_uri, item_uri="i-100")

    # Now, the detachment of the Content Item from the initial (root) Category is possible
    Categories.detach_from_category(category_uri=root_uri, item_uri="i-100")

    # Verify that nodes and links are in place
    q = f'''
        MATCH p=
        (:Image {{caption:"my_pic", uri:"i-100", `_CLASS`:"Image"}})
        -[:BA_in_category]->
        (:Category {{uri: "{new_cat_uri}", `_CLASS`:"Category"}})
        RETURN COUNT(p) AS path_count
        '''
    result = db.query(q, single_cell="path_count")
    assert result == 1



def test_relocate_across_categories(db):
    pass



##############  SCHEMA-RELATED  ##############


def test_get_items_schema_data(db):
    _, root_uri = initialize_categories(db)
    #print("root URI is: ", root_uri)

    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {}    # There are no Contents Items yet attached to the Category

    GraphSchema.create_class_with_properties(name="Note", properties=["title", "basename", "suffix"])
    GraphSchema.create_class_with_properties(name="Image", properties=["caption", "basename", "suffix", "uri"])

    # Add some Content Items to the above Category
    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Note",
                                 item_properties={"title": "My 1st note"})

    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Note': ['title', 'basename', 'suffix']}

    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Image",
                                  item_properties={"caption": "vacation pic", "basename": "pic1", "suffix": "jpg"})
    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Note': ['title', 'basename', 'suffix'], 'Image': ['caption', 'basename', 'suffix', 'uri']}

    # Make the "uri" property of the Class "Image" to be a "system" property
    GraphSchema.set_property_attribute(class_name="Image", prop_name="uri",
                                       attribute_name="system", attribute_value=True)
    res = Categories.get_items_schema_data(category_uri=root_uri)
    assert res == {'Note': ['title', 'basename', 'suffix'], 'Image': ['caption', 'basename', 'suffix']}   # 'uri' is no longer included



##############  POSITION WITHIN CATEGORIES  ##############


def test_check_for_duplicates(db):
    pass

def test_check_all_categories_for_duplicates(db):
    pass

def test_reassign_positional_values(db):
    pass

def test_reposition_content(db):
    pass

def test_relocate_positions(db):
    pass

def test_swap_content_items(db):
    pass
