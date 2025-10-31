import pytest
import os
from brainannex import GraphAccess, GraphSchema
from app_libraries.media_manager import MediaManager
import app_libraries.PLUGINS.plugin_support as plugin_support
from app_libraries.PLUGINS.documents import Documents
from app_libraries.PLUGINS.images import Images
from app_libraries.PLUGINS.notes import Notes




# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    GraphSchema.set_database(neo_obj)

    MediaManager.set_media_folder("D:/media/my_media_folder/")
    MediaManager.set_default_folders(plugin_support.all_default_folders())

    yield neo_obj



def test_default_file_path():
    MediaManager.set_media_folder("D:/media/my_media_folder/")
    MediaManager.set_default_folders(plugin_support.all_default_folders())


    assert MediaManager.default_file_path(class_name="Document") == "D:/media/my_media_folder/documents/"

    assert MediaManager.default_file_path(class_name="Image", thumb=False) == "D:/media/my_media_folder/images/"
    assert MediaManager.default_file_path(class_name="Image", thumb=True) == "D:/media/my_media_folder/images/resized/"



def test_retrieve_full_path(db):
    db.empty_dbase()
    Images.initialize_schema()

    # Create an Image node, with the default folder for its type    TODO: turn all the various sample setup into a utility function
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_uri="image-1")

    assert MediaManager.retrieve_full_path(uri="image-1") == "D:/media/my_media_folder/images/"
    assert MediaManager.retrieve_full_path(uri="image-1", thumb=True) == "D:/media/my_media_folder/images/resized/"

    with pytest.raises(Exception):
        assert MediaManager.retrieve_full_path("unknown_uri")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_uri="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="uri")

    assert MediaManager.retrieve_full_path(uri="image-1") == "D:/media/my_media_folder/images/Tahiti vacation/"
    assert MediaManager.retrieve_full_path(uri="image-1", thumb=True) == "D:/media/my_media_folder/images/Tahiti vacation/resized/"



def test_lookup_media_file(db):
    db.empty_dbase()
    Images.initialize_schema()

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_uri="image-1")

    assert MediaManager.lookup_media_file(uri="image-1", class_name="Image") == ("D:/media/my_media_folder/images/", "snap1", "jpg")
    assert MediaManager.lookup_media_file(uri="image-1", class_name="Image", thumb=True) == ("D:/media/my_media_folder/images/resized/", "snap1", "jpg")

    with pytest.raises(Exception):
        assert MediaManager.lookup_media_file("unknown_uri", class_name="Image")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_uri="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="uri")

    assert MediaManager.lookup_media_file(uri="image-1", class_name="Image") == ("D:/media/my_media_folder/images/Tahiti vacation/", "snap1", "jpg")
    assert MediaManager.lookup_media_file(uri="image-1", class_name="Image", thumb=True) == ("D:/media/my_media_folder/images/Tahiti vacation/resized/", "snap1", "jpg")



def test_get_full_filename(db):
    db.empty_dbase()
    Images.initialize_schema()

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_uri="image-1")

    assert MediaManager.get_full_filename("image-1", class_name="Image") == "D:/media/my_media_folder/images/snap1.jpg"
    assert MediaManager.get_full_filename("image-1", class_name="Image", thumb=True) == "D:/media/my_media_folder/images/resized/snap1.jpg"

    with pytest.raises(Exception):
        assert MediaManager.get_full_filename("unknown_uri", class_name="Image")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_uri="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="uri")

    assert MediaManager.get_full_filename("image-1", class_name="Image") == "D:/media/my_media_folder/images/Tahiti vacation/snap1.jpg"
    assert MediaManager.get_full_filename("image-1", class_name="Image", thumb=True) == \
                                "D:/media/my_media_folder/images/Tahiti vacation/resized/snap1.jpg"



def test_move_file():
    src = "test_files/I_dont_exist.txt"
    dest = "test_files/sample_file_2.txt"

    with pytest.raises(Exception):
        MediaManager.move_file(src, dest)   # Non-existent source


    src = "test_files/sample_file_1.txt"

    with pytest.raises(Exception):
        MediaManager.move_file(src, src)    # Identical src and dest

    with pytest.raises(Exception):
        MediaManager.move_file(src, dest)   # Trying to over-write existing file


    dest = "test_files/sample_file_1_moved.txt"

    MediaManager.move_file(src, dest)
    assert os.path.exists(dest)

    # Move the file back to its original name
    src = dest
    dest_restore = "test_files/sample_file_1.txt"
    MediaManager.move_file(src, dest_restore)
    assert os.path.exists(dest_restore)
    assert not os.path.exists(src)


    src = "test_files/sample_file_1.txt"
    dest = "test_files/bad:name.txt"

    with pytest.raises(Exception):
        MediaManager.move_file(src, dest)   # Bad destination name



def test_get_mime_type():
    assert MediaManager.get_mime_type("jpg") == "image/jpeg"
    assert MediaManager.get_mime_type("PDF") == "application/pdf"
    assert MediaManager.get_mime_type("some_nonsense") == "application/save"    # default format for unknown file extensions
