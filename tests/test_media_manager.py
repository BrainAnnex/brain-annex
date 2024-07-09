from brainannex.media_manager import MediaManager



def test_get_mime_type():
    assert MediaManager.get_mime_type("jpg") == "image/jpeg"
    assert MediaManager.get_mime_type("PDF") == "application/pdf"
    assert MediaManager.get_mime_type("some_nonsense") == "application/save"    # default format for unknown file extensions
