import pytest
from neoaccess import NeoAccess
from brainannex.neoschema.neo_schema import NeoSchema
from brainannex.data_manager import DataManager
from brainannex.categories import Categories
from brainannex.media_manager import ImageProcessing


MEDIA_FOLDER = "D:/Docs/media/"



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=True)
    DataManager.db = neo_obj
    NeoSchema.set_database(neo_obj)
    yield neo_obj



#######################     SCHEMA- RELATED      #######################

def test_get_leaf_records(db):
    result = DataManager.get_leaf_records()
    print("Leaf records: ", result)




#########   Categories-related   #########


def test_reposition_content():
    Categories.reposition_content(60, uri=576, move_after_n=4)



def test_relocate_positions():
    n_shifted = Categories.relocate_positions(60, n_to_skip=29, pos_shift=-295)
    assert n_shifted == 2




#########   ImageProcessing class  #########

def test_make_thumbnail():
    ImageProcessing.save_thumbnail(src_folder=MEDIA_FOLDER,
                                   filename="test.PNG",
                                   save_to_folder=MEDIA_FOLDER+"resized/",
                                   src_width=1141, src_height=643)



def test_scale_down_image():
    ImageProcessing.scale_down_horiz(src_folder=MEDIA_FOLDER,
                                     filename="test.PNG",
                                     save_to_folder=MEDIA_FOLDER+"resized/",
                                     src_width=1141, src_height=643,
                                     target_width=100)



def test_describe_image():
    src = MEDIA_FOLDER + "test.PNG"
    print()
    ImageProcessing.describe_image(src)
