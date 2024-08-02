import pytest
from brainannex.utilities.comparisons import compare_recordsets
from brainannex.data_manager import DataManager
from neoaccess import NeoAccess
from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.categories import Categories
from brainannex.collections import Collections


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    #NeoSchema.set_database(neo_obj)
    #Categories.db = neo_obj
    #Collections.set_database(neo_obj)
    DataManager.set_database(neo_obj)
    yield neo_obj



# ************  CREATE CATEGORY CLASS AND ROOT CATEGORY for the testing  **************

def initialize_categories(db):
    # Clear the dbase, create the Schema needed for Categories , and create a ROOT Category node;
    # return the pair (internal database ID, URI) of the new Categories ROOT node

    db.empty_dbase()

    Categories.initialize_categories()

    return Categories.create_categories_root()  # Returns a pair (int, str)





# ********************  THE ACTUAL TESTS  ********************

def test_update_content_item_NEW(db):

    _, root_uri = initialize_categories(db)

    # Create a Content Item, and attach it to the Root Category
    NeoSchema.create_class_with_properties(name="Photo", strict=True,
                                           properties=["caption", "remarks", "uri"])
    Categories.add_content_at_end(category_uri=root_uri, item_class_name="Photo",
                                  item_properties={"caption": "beach at sunrise"}, new_uri="photo_1")

    # Alter the Content Item
    DataManager.update_content_item_NEW(uri="photo_1", class_name="Photo",
                                        update_data={"caption": "beach at sunrise"})    # No actual change
    result = NeoSchema.get_data_node(uri="photo_1")
    assert result.get("caption") == "beach at sunrise"     # Notice the leading/trailing blanks are gone
    assert result.get("remarks") is None

    # Alter the Content Item
    DataManager.update_content_item_NEW(uri="photo_1", class_name="Photo",
                                        update_data={"caption": "    beach under full moon  "})
    result = NeoSchema.get_data_node(uri="photo_1")
    assert result.get("caption") == "beach under full moon"     # Notice the leading/trailing blanks are gone
    assert result.get("remarks") is None

    # Alter again the Content Item
    DataManager.update_content_item_NEW(uri="photo_1", class_name="Photo",
                                        update_data={"caption": "      "})
    result = NeoSchema.get_data_node(uri="photo_1")
    assert result.get("caption") is None        # That field is now gone altogether
    assert result.get("remarks") is None

    # Alter yet again the Content Item
    DataManager.update_content_item_NEW(uri="photo_1", class_name="Photo",
                                        update_data={"remarks": "3 is a charm!  ", "caption": "  beach in the late afternoon"})
    result = NeoSchema.get_data_node(uri="photo_1")
    assert result.get("caption") == "beach in the late afternoon"
    assert result.get("remarks") == "3 is a charm!"

    with pytest.raises(Exception):
        DataManager.update_content_item_NEW(uri="photo_1", class_name="I_DONT_EXIST",
                                            update_data={"remarks": "this will blow up!"})



def test_switch_category(db):

    _, root_uri = initialize_categories(db)

    greece_uri = Categories.add_subcategory({"category_uri": root_uri, "subcategory_name": "Greece",
                                             "subcategory_remarks": "Summer trip to Greece"})

    # Create 2 Content Items, and initially attach them to the Root Category
    NeoSchema.create_class_with_properties(name="Photo",
                                           properties=["name", "uri"])

    all_photo_uris = []
    for i in range(4):
        photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS", prefix="photo-")
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

    db.create_node(labels="Test Label", properties={'age': 22, 'gender': 'F'})

    # No filtration
    assert DataManager.get_nodes_by_filter({}) == [{'gender': 'F', 'age': 22}]
    # Filtration by labels
    assert DataManager.get_nodes_by_filter({"labels": "Test Label"}) == [{'gender': 'F', 'age': 22}]
    assert DataManager.get_nodes_by_filter({"labels": "WRONG_Label"}) == []

    # TODO: add more tests
    #print(DataManager.get_nodes_by_filter({}))



def test__process_order_by():
    s = "John DESC, Alice, Bob desc, Carol"
    result = DataManager._process_order_by(s)
    assert result == "toLower(n.John) DESC, toLower(n.Alice), toLower(n.Bob) DESC, toLower(n.Carol)"
