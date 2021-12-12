from BrainAnnex.api.BA_api_request_handler import ImageProcessing, APIRequestHandler
from BrainAnnex.modules.categories.categories import Categories

MEDIA_FOLDER = "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"



def test_secure_filename_BA():
    assert APIRequestHandler.secure_filename_BA("My cool ++ movie.mov") == "My cool  movie.mov"
    assert APIRequestHandler.secure_filename_BA("../../../etc/passwd") == "etc_passwd"
    assert APIRequestHandler.secure_filename_BA('i contain \xfcml\xe4uts.txt') == 'i contain umlauts.txt'
    assert APIRequestHandler.secure_filename_BA("COM1.txt") == "_COM1.txt"
    assert APIRequestHandler.secure_filename_BA("    blank-padded string  ") == "blank-padded string"




#######################     SCHEMA- RELATED      #######################

def test_get_leaf_records():
    result = APIRequestHandler.get_leaf_records()
    print(result)




#########   Categories-related   #########


def test_reposition_content():
    Categories.reposition_content(60, item_id=576, move_after_n=4)



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
