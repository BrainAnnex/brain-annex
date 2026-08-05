import pytest
from app_libraries.PLUGINS.plugin_manager import PluginManager
from app_libraries.PLUGINS.document import Document
from app_libraries.PLUGINS.image import Image
from app_libraries.PLUGINS.note import Note
from app_libraries.PLUGINS.header import Header



# Provide a module initialization before each test
@pytest.fixture(scope="function")
def initialize():
    PluginManager.REGISTERED_PLUGINS = {}       # Clear any registration from previous tests



def test_register():
    pass    # TODO



def test_is_valid_plugin_id():
    assert PluginManager.is_valid_plugin_id("document")
    assert PluginManager.is_valid_plugin_id("timer_widget")
    assert PluginManager.is_valid_plugin_id("site_link2")

    assert not PluginManager.is_valid_plugin_id("x")        # Too short
    assert not PluginManager.is_valid_plugin_id("x-y")      # Forbidden special characters
    assert not PluginManager.is_valid_plugin_id("BadUppercaseName")    # Forbidden uppercase characters
    assert PluginManager.is_valid_plugin_id("h_game")
    assert PluginManager.is_valid_plugin_id("x_y")
    assert not PluginManager.is_valid_plugin_id("_abc")     # Underscores need to be sandwiched between words
    assert not PluginManager.is_valid_plugin_id("x_")       # Underscores need to be sandwiched between words
    assert not PluginManager.is_valid_plugin_id("x__y")     # Underscores need to be sandwiched between words

    assert PluginManager.is_valid_plugin_id("x2")
    assert not PluginManager.is_valid_plugin_id("9x")       # Words cannot start with digits
    assert not PluginManager.is_valid_plugin_id("x_2")      # Words cannot start with digits
    assert PluginManager.is_valid_plugin_id("x_v2")

    assert not PluginManager.is_valid_plugin_id("for")      # Cannot be a python keyword
    assert not PluginManager.is_valid_plugin_id("class")    # Cannot be a python keyword
    assert not PluginManager.is_valid_plugin_id("if")       # Cannot be a python keyword



def test_plugin_id_to_class_name():
    assert PluginManager.plugin_id_to_class_name("document") == "Document"
    assert PluginManager.plugin_id_to_class_name("timer_widget") == "TimerWidget"
    assert PluginManager.plugin_id_to_class_name("doc2") == "Doc2"

    with pytest.raises(Exception):
        PluginManager.plugin_id_to_class_name("doc_2")

    with pytest.raises(Exception):
        PluginManager.plugin_id_to_class_name("BadUppercaseName")



def test_default_folder(initialize):
    with pytest.raises(Exception):
        PluginManager.default_folder(semantic_class="Document")     # No plugins yet registered

    PluginManager.register(plugin_id="document", plugin_class=Document)
    assert PluginManager.default_folder(semantic_class="Document") == "documents"

    with pytest.raises(Exception):
        PluginManager.default_folder(semantic_class="Image")    # No plugin handling the "Image" class yet registered

    PluginManager.register(plugin_id="image", plugin_class=Image)
    assert PluginManager.default_folder(semantic_class="Image") == "images"

    PluginManager.register(plugin_id="note", plugin_class=Note)
    assert PluginManager.default_folder(semantic_class="Note") == "notes"

    PluginManager.register(plugin_id="header", plugin_class=Header)
    with pytest.raises(Exception):
        PluginManager.default_folder(semantic_class="Header")   # Plugin for "Header" isn't for media



def test_all_default_folders(initialize):
    assert PluginManager.all_default_folders() == {}    # No plugins yet registered

    PluginManager.register(plugin_id="document", plugin_class=Document)
    assert PluginManager.all_default_folders() == {"Document": "documents"}

    PluginManager.register(plugin_id="image", plugin_class=Image)
    assert PluginManager.all_default_folders() == {"Document": "documents", "Image": "images"}

    PluginManager.register(plugin_id="note", plugin_class=Note)
    assert PluginManager.all_default_folders() == { "Document": "documents",
                                                    "Image": "images",
                                                    "Note": "notes"}

    PluginManager.register(plugin_id="header", plugin_class=Header)
    assert PluginManager.all_default_folders() == { "Document": "documents",
                                                    "Image": "images",
                                                    "Note": "notes"}    # No change, because header plugin has no default folders


def test_is_media_class(initialize):
    assert not PluginManager.is_media_class("Document")
    PluginManager.register(plugin_id="document", plugin_class=Document)
    assert PluginManager.is_media_class("Document")

    assert not PluginManager.is_media_class("Image")
    PluginManager.register(plugin_id="image", plugin_class=Image)
    assert PluginManager.is_media_class("Image")

    assert not PluginManager.is_media_class("Note")
    PluginManager.register(plugin_id="note", plugin_class=Note)
    assert PluginManager.is_media_class("Note")

    assert not PluginManager.is_media_class("Header")
    PluginManager.register(plugin_id="header", plugin_class=Header)
    assert not PluginManager.is_media_class("Header")



def test_api_endpoint(initialize):
    with pytest.raises(Exception):
        PluginManager.api_handler(plugin_id="document", parameters=[1, 2, 3])   # Not yet registered

    PluginManager.register(plugin_id="document", plugin_class=Document)

    result = PluginManager.api_handler(plugin_id="document", parameters=[1, 2, 3])
    assert result
