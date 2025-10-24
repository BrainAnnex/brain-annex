import pytest
from brainannex import GraphAccess, NeoSchema, Collections, Categories
from utilities.comparisons import compare_recordsets
from app_libraries.data_manager import DataManager



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    #NeoSchema.set_database(neo_obj)
    #Categories.db = neo_obj
    #Collections.set_database(neo_obj)
    DataManager.set_database(neo_obj)
    yield neo_obj



# ************  CREATE CATEGORY CLASS AND ROOT CATEGORY for the testing  **************

def initialize_categories(db):
    # Clear the dbase, create the Schema needed for Categories, and create a ROOT Category node;
    # return the pair (internal database ID, URI) of the new Categories ROOT node

    db.empty_dbase()

    Categories.initialize_categories()

    return Categories.create_categories_root()  # Returns a pair (int, str)





# ********************  THE ACTUAL TESTS  ********************

def test_get_records_by_link(db):
    db.empty_dbase(drop_indexes=True, drop_constraints=True)

    book_1 = db.create_node("book", {'title': 'The Double Helix', "uri": "biochem-1"})
    book_2 = db.create_node("book", {'title': 'Intro to Hilbert Spaces'})

    # Create new node, linked to the previous two
    person_id = db.create_node_with_relationships(labels="person",
                                      properties={"name": "Julian", "city": "Berkeley"},
                                      connections=[
                                          {"labels": "book",
                                           "key": "title", "value": "The Double Helix",
                                           "rel_name": "OWNS", "rel_dir": "OUT"},

                                          {"labels": "book",
                                           "key": "title", "value": "Intro to Hilbert Spaces",
                                           "rel_name": "OWNS", "rel_dir": "OUT"}
                                      ]
                                      )

    request_data = {"uri": "biochem-1", "rel_name": "OWNS", "dir": "IN"}
    result = DataManager.get_records_by_link(request_data)
    expected = [{"name": "Julian", "city": "Berkeley", 'node_labels': ['person']}]
    assert result == expected

    request_data = {"internal_id": book_2, "rel_name": "OWNS", "dir": "IN"}
    result = DataManager.get_records_by_link(request_data)
    expected = [{"internal_id": person_id, "name": "Julian", "city": "Berkeley", 'node_labels': ['person']}]
    assert result == expected

    request_data = {"internal_id": person_id, "rel_name": "OWNS", "dir": "OUT"}
    result = DataManager.get_records_by_link(request_data)
    expected = [{'title': 'The Double Helix', 'uri': 'biochem-1', 'internal_id': book_1, 'node_labels': ['book']} ,
                {'title': 'Intro to Hilbert Spaces', 'internal_id': book_2, 'node_labels': ['book']}]
    assert compare_recordsets(result, expected)



def test_update_content_item(db):

    _, root_uri = initialize_categories(db)

    # Create a Content Item, and attach it to the Root Category
    NeoSchema.create_class_with_properties(name="Photo", strict=True,
                                           properties=["caption", "remarks", "uri"])
    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Photo",
                                  item_properties={"caption": "beach at sunrise"}, new_uri="photo_1")

    # Alter the Content Item
    DataManager.update_content_item(uri="photo_1", class_name="Photo",
                                    update_data={"caption": "beach at sunrise"})    # No actual change
    result = NeoSchema.search_data_node(uri="photo_1")
    assert result.get("caption") == "beach at sunrise"     # Notice the leading/trailing blanks are gone
    assert result.get("remarks") is None

    # Alter the Content Item
    DataManager.update_content_item(uri="photo_1", class_name="Photo",
                                    update_data={"caption": "    beach under full moon  "})
    result = NeoSchema.search_data_node(uri="photo_1")
    assert result.get("caption") == "beach under full moon"     # Notice the leading/trailing blanks are gone
    assert result.get("remarks") is None

    # Alter again the Content Item
    DataManager.update_content_item(uri="photo_1", class_name="Photo",
                                    update_data={"caption": "      "})
    result = NeoSchema.search_data_node(uri="photo_1")
    assert result.get("caption") is None        # That field is now gone altogether
    assert result.get("remarks") is None

    # Alter yet again the Content Item
    DataManager.update_content_item(uri="photo_1", class_name="Photo",
                                    update_data={"remarks": "3 is a charm!  ", "caption": "  beach in the late afternoon"})
    result = NeoSchema.search_data_node(uri="photo_1")
    assert result.get("caption") == "beach in the late afternoon"
    assert result.get("remarks") == "3 is a charm!"

    with pytest.raises(Exception):
        DataManager.update_content_item(uri="photo_1", class_name="I_DONT_EXIST",
                                        update_data={"remarks": "this will blow up!"})



def test_switch_category(db):

    _, root_uri = initialize_categories(db)

    greece_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Greece",
                                             "subcategory_remarks": "Summer trip to Greece"})

    # Create 2 Content Items, and initially attach them to the Root Category
    NeoSchema.create_class_with_properties(name="Photo",
                                           properties=["name", "uri"])

    NeoSchema.create_namespace(name="PHOTOS", prefix="photo-")
    all_photo_uris = []
    for i in range(4):
        photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
        all_photo_uris.append(photo_uri)
        Categories.add_content_at_end(category_uri=root_uri, item_class_name="Photo",
                                      item_properties={"caption": "photo_"+str(i+1)}, new_uri=photo_uri)


    # Relocate the first 2 photos to the "Greece" Category
    DataManager.switch_category({"items": ['photo-1', 'photo-2'], "from": root_uri, "to": greece_uri})

    # Verify that those 2 photos are now linked to the "Greece" Category, at the expected positions
    result = Categories.get_content_items_by_category(uri=greece_uri)
    expected = [{'caption': 'photo_1', 'uri': 'photo-1', 'pos': 0, 'class_name': 'Photo'},
                {'caption': 'photo_2', 'uri': 'photo-2', 'pos': Collections.DELTA_POS, 'class_name': 'Photo'}]

    assert compare_recordsets(result, expected)


    # Separately, add a new photo to the "Greece" Category
    photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    Categories.add_content_at_end(category_uri=greece_uri, item_class_name="Photo",
                                  item_properties={"caption": "photo_extra"}, new_uri=photo_uri)


    # Now relocate the remaining 2 photos from the Root Category to the "Greece" Category
    DataManager.switch_category({"items": ['photo-3', 'photo-4'], "from": root_uri, "to": greece_uri})

    # Verify that those 2 photos are now linked to the "Greece" Category, at the expected positions
    result = Categories.get_content_items_by_category(uri=greece_uri)
    # Concatenate two dicts
    expected += [{'caption': 'photo_extra', 'uri': 'photo-5', 'pos': 2 * Collections.DELTA_POS, 'class_name': 'Photo'},
                 {'caption': 'photo_3', 'uri': 'photo-3',     'pos': 3 * Collections.DELTA_POS, 'class_name': 'Photo'},
                 {'caption': 'photo_4', 'uri': 'photo-4',     'pos': 4 * Collections.DELTA_POS, 'class_name': 'Photo'}]
    assert compare_recordsets(result, expected)



def test_get_nodes_by_filter(db):
    db.empty_dbase()

    assert DataManager.get_nodes_by_filter({}) == []    # The database is empty

    internal_id = db.create_node(labels="Test Label", properties={'age': 22, 'gender': 'F'})

    # No filtration
    assert DataManager.get_nodes_by_filter({}) == [{'gender': 'F', 'age': 22, 'internal_id': internal_id, 'node_labels': ["Test Label"]}]
    # Filtration by labels
    assert DataManager.get_nodes_by_filter({"label": "Test Label"}) == \
                                [{'gender': 'F', 'age': 22, 'internal_id': internal_id, 'node_labels': ["Test Label"]}]
    assert DataManager.get_nodes_by_filter({"label": "WRONG_Label"}) == []
    assert DataManager.get_nodes_by_filter({"key_name": "age", "key_value": 22}) == \
                                [{'gender': 'F', 'age': 22, 'internal_id': internal_id, 'node_labels': ["Test Label"]}]
    assert DataManager.get_nodes_by_filter({"key_name": "age", "key_value": 99}) == []
    assert DataManager.get_nodes_by_filter({"label": "WRONG_Label", "key_name": "age", "key_value": 22}) == []

    with pytest.raises(Exception):
        DataManager.get_nodes_by_filter(filter_dict=123)        # Not a dict

    with pytest.raises(Exception):
        DataManager.get_nodes_by_filter({"mystery_key": 123})   # Bad key

    # TODO: add more tests
    #print(DataManager.get_nodes_by_filter({}))
