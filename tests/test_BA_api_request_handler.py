import pytest
from neoaccess import NeoAccess
from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.data_manager import DataManager
from brainannex.upload_helper import UploadHelper


#MEDIA_FOLDER = "D:/Docs/media/"



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=True)
    DataManager.db = neo_obj
    NeoSchema.set_database(neo_obj)
    yield neo_obj



def test_secure_filename_BA():
    assert UploadHelper.secure_filename_BA("My cool ++ movie.mov") == "My cool  movie.mov"
    assert UploadHelper.secure_filename_BA("../../../etc/passwd") == "etc_passwd"
    assert UploadHelper.secure_filename_BA('i contain \xfcml\xe4uts.txt') == 'i contain umlauts.txt'
    assert UploadHelper.secure_filename_BA("COM1.txt") == "_COM1.txt"
    assert UploadHelper.secure_filename_BA("    blank-padded string  ") == "blank-padded string"




#######################     SCHEMA- RELATED      #######################

def test_get_leaf_records(db):
    pass        # TODO




#########   Categories-related   #########

# TODO




#########   ImageProcessing class  #########

# TODO
