from brainannex.PLUGINS.documents import Documents
from brainannex.PLUGINS.images import Images
from brainannex.PLUGINS.notes import Notes


def default_folder(class_name :str) -> str:
    """
    Fetch the name for the default folder used for media content associated to the given class

    :param class_name:
    :return:            A folder name, with no slashes.  EXAMPLE: "documents"
    """
    if class_name == "Document":
        return Documents.default_folder()

    if class_name == "Image":
        return Images.default_folder()

    if class_name == "Note":
        return Notes.default_folder()

    raise Exception(f"plugin_support.default_folder(): unknown or missing value for "
                    f"`class_name` ({class_name})")



def all_default_folders() -> dict:
    """
    Return a dict mapping a Class name to its designated default folder

    :return:    EXAMPLE: {"Document": "documents", "Image": "images", "Note": "notes"}
    """
    d = {}

    d["Document"] = Documents.default_folder()
    d["Image"] = Images.default_folder()
    d["Note"] = Notes.default_folder()

    return d



def is_media_class(class_name :str) -> bool:
    """
    Return True if the given Class is an INSTANCE_OF the "Media" Class

    :param class_name:  Name of a Schema class
    :return:            True if the given Class is an INSTANCE_OF the "Media" Class
    """
    # TODO: for now hardwired; ought to instead query the Schema, to discover if the given Class
    #       is an INSTANCE_OF the "Media" class
    return class_name in ["Document", "Image", "Note"]
