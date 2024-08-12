import pytest
import os
from brainannex.media_manager import MediaManager



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
