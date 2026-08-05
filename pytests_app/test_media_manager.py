import pytest
import os
from brainannex import GraphAccess, GraphSchema
from app_libraries.media_manager import MediaManager
from app_libraries.PLUGINS.plugin_manager import PluginManager
from app_libraries.PLUGINS.image import Image
from app_libraries.PLUGINS.document import Document
from app_libraries.PLUGINS.note import Note



# Provide a module initialization automatically run before each test
@pytest.fixture(scope="function", autouse=True) # autouse=True makes it unnecessary to pass initialize as argument to all tests
def initialize():
    PluginManager.REGISTERED_PLUGINS = {}       # Clear any registration from previous tests
    PluginManager.register(plugin_id="document", plugin_class=Document)
    PluginManager.register(plugin_id="image",    plugin_class=Image)
    PluginManager.register(plugin_id="note",     plugin_class=Note)

    MediaManager.set_media_folder("D:/media/my_media_folder/")
    MediaManager.set_default_folders(PluginManager.all_default_folders())


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    graph_db_handle = GraphAccess(debug=False)
    GraphSchema.set_database(graph_db_handle)
    yield graph_db_handle



def test_set_media_folder():
    MediaManager.set_media_folder("D:/whatever/")
    assert MediaManager.MEDIA_FOLDER == "D:/whatever/"

    MediaManager.set_media_folder("D:/I_forgot_the_final_slash")
    assert MediaManager.MEDIA_FOLDER == "D:/I_forgot_the_final_slash/"  # Automatically added

    with pytest.raises(Exception):
        MediaManager.set_media_folder(True)



def test_default_file_path():
    MediaManager.set_media_folder("D:/media/my_media_folder/")
    assert MediaManager.MEDIA_FOLDER == "D:/media/my_media_folder/"

    MediaManager.set_default_folders(PluginManager.all_default_folders())

    assert MediaManager.default_file_path(class_name="Document") == "D:/media/my_media_folder/documents/"

    assert MediaManager.default_file_path(class_name="Image", thumb=False) == "D:/media/my_media_folder/images/"
    assert MediaManager.default_file_path(class_name="Image", thumb=True) == f"D:/media/my_media_folder/images/{MediaManager.RESIZED_FOLDER}"

    assert MediaManager.default_file_path(class_name="Unknown") == "D:/media/my_media_folder/"



def test_lookup_media_file(db):
    db.empty_dbase()
    Image.add_to_schema()

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_entity_id="image-1")

    assert MediaManager.lookup_media_file(entity_id="image-1", class_name="Image") == ("D:/media/my_media_folder/images/", "snap1", "jpg")
    assert MediaManager.lookup_media_file(entity_id="image-1", class_name="Image", thumb=True) \
            == (f"D:/media/my_media_folder/images/{MediaManager.RESIZED_FOLDER}", "snap1", "jpg")

    with pytest.raises(Exception):
        assert MediaManager.lookup_media_file("unknown_uri", class_name="Image")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_entity_id="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.lookup_media_file(entity_id="image-1", class_name="Image") == ("D:/media/my_media_folder/images/Tahiti vacation/", "snap1", "jpg")
    assert MediaManager.lookup_media_file(entity_id="image-1", class_name="Image", thumb=True) \
            == (f"D:/media/my_media_folder/images/Tahiti vacation/{MediaManager.RESIZED_FOLDER}", "snap1", "jpg")



def test_get_media_item_file_by_entity(db):
    db.empty_dbase()
    Image.add_to_schema()

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image",
                                 properties={"basename": "snap1", "suffix": "jpg"},
                                 new_entity_id="image-1")

    assert MediaManager.get_media_item_file_by_entity(entity_id="image-1", class_name="Image") \
            == ("D:/media/my_media_folder/images/", "snap1", "jpg")
    # Note: "D:/media/my_media_folder/" was set by the pytest initialize fixture

    with pytest.raises(Exception):
        assert MediaManager.get_media_item_file_by_entity(class_name="Image", entity_id="unknown_entity_id")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_entity_id="dir-1")

    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.get_media_item_file_by_entity(class_name="Image", entity_id="image-1") \
            == ("D:/media/my_media_folder/images/Tahiti vacation/", "snap1", "jpg")



def test_get_media_item_file(db):
    db.empty_dbase()
    Image.add_to_schema()

    # Create an Image node, with the default folder for its type
    image_internal_id = GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                                     new_entity_id="image-1")

    assert MediaManager.get_media_item_file(internal_id=image_internal_id) \
            == ("D:/media/my_media_folder/images/", "snap1", "jpg")
    # Note: "D:/media/my_media_folder/" was set by this pytest module


    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_entity_id="dir-1")

    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.get_media_item_file(internal_id=image_internal_id) \
            == ("D:/media/my_media_folder/images/Tahiti vacation/", "snap1", "jpg")



def test_get_absolute_file_path(db):
    db.empty_dbase()

    Image.add_to_schema()
    print(PluginManager.all_default_folders())

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image",
                                 properties={"basename": "snap1", "suffix": "jpg"},
                                 new_entity_id="image-1")

    assert MediaManager.get_absolute_file_path(entity_id="image-1", class_name="Image") \
                == "D:/media/my_media_folder/images/snap1.jpg"


    with pytest.raises(Exception):
        assert MediaManager.get_absolute_file_path(entity_id="unknown_uri", class_name="Image")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_entity_id="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.get_absolute_file_path(entity_id="image-1", class_name="Image") == "D:/media/my_media_folder/images/Tahiti vacation/snap1.jpg"



def test_get_full_filename(db):
    db.empty_dbase()

    Image.add_to_schema()
    print(PluginManager.all_default_folders())

    # Create an Image node, with the default folder for its type
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_entity_id="image-1")

    assert MediaManager.get_full_filename("image-1", class_name="Image") == "D:/media/my_media_folder/images/snap1.jpg"
    return
    assert MediaManager.get_full_filename("image-1", class_name="Image", thumb=True) \
                == f"D:/media/my_media_folder/images/{MediaManager.RESIZED_FOLDER}snap1.jpg"

    with pytest.raises(Exception):
        assert MediaManager.get_full_filename("unknown_uri", class_name="Image")

    # Create a new directory (just its metadata), and relocate our earlier image to be linked to it
    GraphSchema.create_data_node(class_name="Directory", properties={"name": "images/Tahiti vacation"},
                                 new_entity_id="dir-1")


    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.get_full_filename("image-1", class_name="Image") == "D:/media/my_media_folder/images/Tahiti vacation/snap1.jpg"
    assert MediaManager.get_full_filename("image-1", class_name="Image", thumb=True) == \
                                f"D:/media/my_media_folder/images/Tahiti vacation/{MediaManager.RESIZED_FOLDER}snap1.jpg"



def test_rename_media_file():
    with pytest.raises(Exception):
        MediaManager.rename_media_file(folder="test_files/", old_basename="I_dont_exist", old_suffix="txt",
                                       new_basename="sample_file_1_moved")

    # No action taken
    MediaManager.rename_media_file(folder="test_files/", old_basename="I_dont_exist", old_suffix="txt",
                                   new_basename="irrelevant", ignore_missing=True)

    with pytest.raises(Exception):
        MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt",
                                       new_basename="sample_file_2")        # Dest file already exists

    with pytest.raises(Exception):
        MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt",
                                   new_basename="un$uitable :file<>name")

    with pytest.raises(Exception):
        MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt",
                                   new_suffix="h@t")

    with pytest.raises(Exception):
        MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt",
                                   new_suffix="supercalifragili")   # Suffix is too long

    # No action involved : no new values provided
    MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt")

    # No action involved : everything stays the same
    MediaManager.rename_media_file(folder="test_files/",
                                   old_basename="sample_file_1", old_suffix="txt",
                                   new_basename="sample_file_1", new_suffix="txt")

    # Rename basename
    MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1", old_suffix="txt",
                                   new_basename="sample_file_1_moved")
    assert os.path.exists("test_files/sample_file_1_moved.txt")

    # Rename suffix (omitting final "/" in `folder`
    MediaManager.rename_media_file(folder="test_files", old_basename="sample_file_1_moved", old_suffix="txt",
                                   new_suffix="htm")
    assert os.path.exists("test_files/sample_file_1_moved.htm")

    # Rename both basename and suffix, back to original value
    MediaManager.rename_media_file(folder="test_files/", old_basename="sample_file_1_moved", old_suffix="htm",
                                   new_basename="sample_file_1", new_suffix="txt")
    assert os.path.exists("test_files/sample_file_1.txt")



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

    dest = "test_files/subfolder/sample_file_2.txt"     # The directory path "test_files/subfolder/" isn't already present

    with pytest.raises(Exception):
        MediaManager.move_file(src, dest)



def test_assert_valid_file_path():
    #MediaManager.assert_valid_file_path("/my_file.img")

    MediaManager.assert_valid_file_path("good name")
    MediaManager.assert_valid_file_path("good name! (Indeed, just so 123).txt")

    with pytest.raises(Exception):
        MediaManager.assert_valid_file_path("bad:name")

    with pytest.raises(Exception):
        MediaManager.assert_valid_file_path("a/bad?name")

    MediaManager.assert_valid_file_path("a//file")      # It's fine; the extra slash will be ignored by the OS

    MediaManager.assert_valid_file_path(r"a\good name! (Indeed, just so 123).txt")
    MediaManager.assert_valid_file_path("a/good name! (Indeed, just so 123).txt")

    MediaManager.assert_valid_file_path(r"a\folder1\folder2\my_file.img")
    MediaManager.assert_valid_file_path("a/folder1/folder2/my_file.img")

    MediaManager.assert_valid_file_path("/my_file.img")
    MediaManager.assert_valid_file_path("\my_file.img")
    MediaManager.assert_valid_file_path("D:\my_file.img")

    MediaManager.assert_valid_file_path("./my_file.img")
    MediaManager.assert_valid_file_path(".\my_file.img")

    MediaManager.assert_valid_file_path("../../my folder_x3/my_file.img")
    MediaManager.assert_valid_file_path(r"..\..\my folder_x3\my_file.img")

    if os.name == "nt":     # If on Windows7+ or Windows Server variants
        with pytest.raises(Exception):
            MediaManager.assert_valid_file_path("PRN")

        with pytest.raises(Exception):
            MediaManager.assert_valid_file_path("COM3")

        with pytest.raises(Exception):
            MediaManager.assert_valid_file_path("COM3.png")

        with pytest.raises(Exception):
            MediaManager.assert_valid_file_path("aUx.hide")



def test_check_valid_file_name():
    assert MediaManager.check_valid_file_name("perfectly_good_name_123") == ""
    assert MediaManager.check_valid_file_name("bad*") == "*"


def test_check_valid_file_extension():
    assert MediaManager.check_valid_file_extension("jgp") == ""
    assert MediaManager.check_valid_file_extension("bad:indeed") == ":"



def test_get_mime_type():
    assert MediaManager.get_mime_type("jpg") == "image/jpeg"
    assert MediaManager.get_mime_type("PDF") == "application/pdf"
    assert MediaManager.get_mime_type("some_nonsense") == "application/save"    # default format for unknown file extensions



def test_retrieve_full_path(db):
    db.empty_dbase()

    MediaManager.add_to_schema()
    Image.add_to_schema()

    # Create an Image node, with the default folder for its type    TODO: maybe turn all the various sample setup into a utility function
    GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"},
                                 new_entity_id="image-1")

    assert MediaManager.retrieve_full_path(uri="image-1") == "D:/media/my_media_folder/images/"
    assert MediaManager.retrieve_full_path(uri="image-1", thumb=True) == f"D:/media/my_media_folder/images/{MediaManager.RESIZED_FOLDER}"

    with pytest.raises(Exception):
        assert MediaManager.retrieve_full_path("unknown_uri")

    # Create a new directory (just its metadata), and link our earlier image to it
    MediaManager.create_media_directory(name="images/Tahiti vacation", entity_id="dir-1")

    GraphSchema.add_data_relationship(from_id="image-1", to_id="dir-1", rel_name="BA_stored_in", id_type="entity_id")

    assert MediaManager.retrieve_full_path(uri="image-1") == "D:/media/my_media_folder/images/Tahiti vacation/"
    assert MediaManager.retrieve_full_path(uri="image-1", thumb=True) == f"D:/media/my_media_folder/images/Tahiti vacation/{MediaManager.RESIZED_FOLDER}"



def test_get_directories(db):
    db.empty_dbase()

    MediaManager.add_to_schema()

    assert MediaManager.get_media_directories() == []

    MediaManager.create_media_directory("images/Tahiti vacation")
    assert MediaManager.get_media_directories() == ["images/Tahiti vacation"]

    MediaManager.create_media_directory("images/South Pole expedition")
    assert MediaManager.get_media_directories() == ["images/South Pole expedition", "images/Tahiti vacation"]



def test_media_directory_stored_in(db):
    db.empty_dbase()

    MediaManager.add_to_schema()
    Image.add_to_schema()

    dir_1 = MediaManager.create_media_directory("images/Tahiti vacation")

    # Create an Image, and link it to the "Tahiti" directory
    image_1_id = GraphSchema.create_data_node(class_name="Image", properties={"basename": "snap1", "suffix": "jpg"})

    GraphSchema.add_data_relationship(from_id=image_1_id, to_id=dir_1, rel_name="BA_stored_in")

    assert MediaManager.media_directory_stored_in(image_1_id) == "images/Tahiti vacation"


    dir_2 = MediaManager.create_media_directory("images/South Pole expedition")

    # Create an Image, and link it to the "South Pole" directory
    image_2_id = GraphSchema.create_data_node(class_name="Image", properties={"basename": "penguin", "suffix": "png"})

    GraphSchema.add_data_relationship(from_id=image_2_id, to_id=dir_2, rel_name="BA_stored_in")

    assert MediaManager.media_directory_stored_in(image_1_id) == "images/Tahiti vacation"
    assert MediaManager.media_directory_stored_in(image_2_id) == "images/South Pole expedition"



def test_create_media_directory(db):
    db.empty_dbase()

    MediaManager.add_to_schema()
    MediaManager.set_media_folder("test_files/")


    MediaManager.create_media_directory(name="my documents/chapter 1")

    assert MediaManager.get_media_directories() == ["my documents/chapter 1"]

    assert MediaManager.folder_exists("test_files/my documents")
    assert MediaManager.folder_exists("test_files/my documents/chapter 1")
    assert not MediaManager.folder_exists("test_files/my documents/chapter 2")

    with pytest.raises(Exception):
        MediaManager.create_media_directory(name="my documents/chapter 1")  # Already exists


    MediaManager.create_media_directory(name="my screenshots")

    assert MediaManager.get_media_directories() == ["my documents/chapter 1", "my screenshots"]

    assert MediaManager.folder_exists("test_files/my documents")
    assert MediaManager.folder_exists("test_files/my documents/chapter 1")
    assert MediaManager.folder_exists("test_files/my screenshots")


    # Clean up the temp folders
    MediaManager.delete_folder("test_files/my documents/chapter 1")
    MediaManager.delete_folder("test_files/my documents")
    MediaManager.delete_folder("test_files/my screenshots")



def test_move_media_item(db):
    db.empty_dbase()

    # Set up
    MediaManager.add_to_schema()
    Document.add_to_schema()

    MediaManager.set_media_folder("test_files/")
    MediaManager.set_default_folders({})


    # Create a Document node, initially with no linked directories (i.e. stored in standard locations)
    # The actual file already exists in the "test_files/" folder
    doc_1_id = GraphSchema.create_data_node(class_name="Document",
                                            properties={"basename": "sample_file_1", "suffix": "txt"})

    assert MediaManager.get_media_item_file(internal_id=doc_1_id) \
            == ("test_files/", "sample_file_1", "txt")

    assert MediaManager.file_exists("test_files/sample_file_1.txt")


    with pytest.raises(Exception):
        # Directory doesn't exist yet
        MediaManager.move_media_item(internal_id=doc_1_id, media_directory="my documents/chapter 1")

    # Create a new media directory
    MediaManager.create_media_directory("my documents/chapter 1")

    MediaManager.move_media_item(internal_id=doc_1_id, media_directory="my documents/chapter 1")

    # Verify the new location of the media file, both in the file system and on the database
    assert MediaManager.file_exists("test_files/my documents/chapter 1/sample_file_1.txt")
    assert MediaManager.get_media_item_file(internal_id=doc_1_id) \
                == ("test_files/my documents/chapter 1/", "sample_file_1", "txt")
    assert MediaManager.media_directory_stored_in(doc_1_id) == "my documents/chapter 1"


    # Create a new media directory
    MediaManager.create_media_directory("ebooks")


    # MOVE THE MEDIA ITEMS
    MediaManager.move_media_item(internal_id=doc_1_id, media_directory="ebooks")


    # Verify the new location of the media file, both in the file system and on the database
    assert MediaManager.file_exists("test_files/ebooks/sample_file_1.txt")
    assert MediaManager.get_media_item_file(internal_id=doc_1_id) \
                == ("test_files/ebooks/", "sample_file_1", "txt")
    assert MediaManager.media_directory_stored_in(doc_1_id) == "ebooks"


    with pytest.raises(Exception):
        # Attempting to repeat the last move
        MediaManager.move_media_item(internal_id=doc_1_id, media_directory="ebooks")


    # Clean up
    MediaManager.move_file(src="test_files/ebooks/sample_file_1.txt", dest="test_files/sample_file_1.txt")
    MediaManager.delete_folder("test_files/my documents/chapter 1")
    MediaManager.delete_folder("test_files/my documents")
    MediaManager.delete_folder("test_files/ebooks")



def test_split_absolute_file_path():
    assert MediaManager.split_absolute_file_path(r"C:\folder_1\folder_2\my_file.txt") == \
        (r"C:\folder_1\folder_2", "my_file", "txt")
