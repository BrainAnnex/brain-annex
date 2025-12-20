from .documents import Documents
from .images import Images
from .notes import Notes


def default_folder(class_name :str) -> str:
    """
    Fetch the name for the default folder used for media content associated to the given class

    :param class_name:  The name of a Schema class
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



def api_handler(plugin_handler :str, parameters):
    """
    EXPERIMENTAL: not in current use.

    Invoke the api_endpoint() method of the appropriate plugin-handler class

    UNTESTED alternate approach: use a registry of all the plugins.  EXAMPLE
        CLASS_REGISTRY: dict[str, type] = {
            "documents": Documents,
            "headers": Headers,
            "images": Images,
            "notes": Notes,
            "recordsets" : Recordsets,
            "site_link": SiteLink,
            "timer": Timer
        }

    :param plugin_handler:  This is the value stored in the database,
                                in the "handler" property of the `Class` nodes
                                EXAMPLES: "documents", "headers"
    :param parameters:      Data that was passed to the web API endpoint to be handled by a specific plugin;
                                for example a dict or list, etc.
    :return:                Pass thru the return value of the api_endpoint() method
    """
    class_name = plugin_handler.capitalize()    # EXAMPLE: "Documents"  (this is our naming convention)
    # TODO: the naming convention is to split underscore-separated parts, and capitalize/collate the parts

    '''
    UNTESTED alt approach to avoid having to import all the various plugin files into this script:
    
        import importlib
    
        module_filename = plugin_handler + ".py"
        
        module = importlib.import_module(module_filename)
        cls = getattr(module, class_name)
        cls.api_endpoint(parameters)
    '''

    cls = globals().get(class_name)             # EXAMPLE: The "Documents" class
    assert cls is not None, \
        f"plugin_support.api_handler(): no plugin-handler class named `{class_name}` exists"

    return cls.api_endpoint(parameters)         # EXAMPLE: call to method Documents..api_endpoint(parameters)
