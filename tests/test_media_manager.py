import pytest
from BrainAnnex.modules.utilities.comparisons import compare_unordered_lists, compare_recordsets
from BrainAnnex.modules.media_manager.media_manager import MediaManager



def test_get_mime_type():
    assert MediaManager.get_mime_type("jpg") == "image/jpeg"
    assert MediaManager.get_mime_type("PDF") == "application/pdf"
    assert MediaManager.get_mime_type("some_nonsense") == "application/save"    # default format for unknown file extensions
