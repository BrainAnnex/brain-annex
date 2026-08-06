import re
import keyword      # To lookup python keywords
from brainannex import GraphSchema


class PluginManager:
    """
    Framework-wide core service for interaction with the various web-app plugins

    This class is NOT to be instantiated.
    It maintains application-wide state in class variables
    and exposes its API through class methods.
    """

    REGISTERED_PLUGINS = {}     # EXAMPLE:  {"document": Document,
                                #            "image": Image,
                                #            "note": Note}


    @classmethod
    def register(cls, plugin_id :str, plugin_class) -> None:
        """
        Used to store the necessary information about a single web-app plugin:
        its name, and the python class that implements it

        :param plugin_id:       The standard, canonical name of a plugin
        :param plugin_class:    A python class that acts as the handler for that plugin.  EXAMPLE:
                                    <class 'app_libraries.PLUGINS.document.Document'>
        :return:                None
        """
        cls.REGISTERED_PLUGINS[plugin_id] = plugin_class



    @classmethod
    def get_plugin_python_class(cls, plugin_name :str):
        """
        Look up and return the python class (the actual class object, NOT its name)
        that was registered as the handler of the given plugin.
        If not found, and Exception is raised

        :param plugin_name: The standard, canonical name of a plugin
        :return:            The python class associated to the given plugin
        """
        assert plugin_name in cls.REGISTERED_PLUGINS, \
            f"get_plugin_python_class(): no plugin-handler class was registered for the plugin `{plugin_name}`"

        return cls.REGISTERED_PLUGINS[plugin_name]



    @staticmethod
    def is_valid_plugin_id(plugin_id: str) -> bool:
        """
        Check if the proposed plugin name is valid

        THE RULES:
            1) At least 2 characters overall
            2) Cannot be a python keyword (such as "for", "case", "class", etc)
            3) One or more words separated by single underscores
            4) Each word may contain digits but must start with a letter.  Only lowercase allowed.

        We recommend using SINGULAR names.  EXAMPLES of existing plugins:
            "document"
            "image"
            "timer_widget"

        :param plugin_id:   The proposed name of a plugin
        :return:            True if name is valid based on Brain Annex standards,
                                of False otherwise
        """
        if len(plugin_id) < 2:
            return False    # Too short, overall

        if keyword.iskeyword(plugin_id):
            return False    # Ran afoul of conflict with a python keyword

        pattern = r"^[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*$"   # Notice all letters are lowercase
        """
            ^                       — start of string
            [a-z]                   — required initial letter
            [a-z0-9]*               — additional letter or digits (zero or more chars)
            (?:_[a-z][a-z0-9]*)*    — zero or more occurrences of from "_[a-z][a-z0-9]*"
                                        (i.e. underscore-separated letter followed by letters and/or digits)
            $                       — end of string
        """

        PLUGIN_ID_PATTERN = re.compile(pattern)

        return bool(PLUGIN_ID_PATTERN.fullmatch(plugin_id))



    @staticmethod
    def plugin_id_to_class_name(plugin_id: str) -> str:
        """
        Implement the BrainAnnex framework convention
        about how to map plugin ID's (canonical names)
        to the names of their handler python class.

        If the plugin ID isn't a valid canonical name,
        an Exception will be raised.

        Our naming convention is to split underscore-separated parts, and capitalize/collate the parts

        EXAMPLES:   document       -> Document
                    timer_widget   -> TimerWidget

        :param plugin_id:   The standard, canonical name of a plugin
        :return:            The standardized name of its corresponding python handler class
        """
        assert PluginManager.is_valid_plugin_id(plugin_id), \
            f"plugin_id_to_class_name(): the plugin_id `{plugin_id}` " \
            f"is not a valid canonical name for a Brain Annex plugin"

        # Capitalize the first letter of each word,
        # after splitting over underscore word boundaries,
        # and then concatenate together all the resulting modified words
        return ''.join(
            part.capitalize()
                for part in plugin_id.split('_')
        )



    @classmethod
    def get_plugin_name_by_semantic_class(cls, semantic_class :str):
        """
        Look up and return the python class (the actual class object, NOT its name)
        that was registered as the handler of the given semantic class.
        If not found, and Exception is raised

        :param semantic_class:  The name of a semantic Class, as used in the database.  EXAMPLE: "Document"
        :return:                The python class associated to the given plugin
        """
        for plugin_name, plugin_class in cls.REGISTERED_PLUGINS.items():
            if plugin_class.SCHEMA_CLASS_NAME == semantic_class:
                return plugin_name

        raise Exception(f"PluginManager.get_plugin_name_by_semantic_class(): none of the registered plugins recognize "
                        f"a semantic Class named `{semantic_class}`")



    @classmethod
    def default_folder(cls, semantic_class :str) -> str:
        """
        Fetch the name for the default folder used for media content associated to the given semantic Class

        :param semantic_class:  The name of a Schema class.  EXAMPLE: "Document"
        :return:                A folder name, with no slashes.  EXAMPLE: "documents"
        """
        # Loop over all the registered plugin handlers
        for plugin_name, plugin_class in cls.REGISTERED_PLUGINS.items():
            if plugin_class.SCHEMA_CLASS_NAME == semantic_class:
                assert hasattr(plugin_class, "DEFAULT_FOLDER_NAME"), \
                    f"PluginManager.default_folder(): missing default folder value for " \
                    f"the plugin `{plugin_name}` (which handles the semantic Class `{semantic_class}`)"

                return plugin_class.DEFAULT_FOLDER_NAME


        raise Exception(f"PluginManager.default_folder(): none of the registered plugins recognize "
                        f"a semantic Class named `{semantic_class}`")



    @classmethod
    def all_default_folders(cls) -> dict:
        """
        Return a dict mapping a semantic Class name to its designated default folder
        (as provided by its handler plugin)

        :return:    EXAMPLE: {"Document": "documents", "Image": "images", "Note": "notes"}
        """
        d = {}

        # Loop over all the registered plugin handlers
        for plugin_name, plugin_class in cls.REGISTERED_PLUGINS.items():
            if hasattr(plugin_class, "DEFAULT_FOLDER_NAME"):
                d[plugin_class.SCHEMA_CLASS_NAME] = plugin_class.DEFAULT_FOLDER_NAME

        return d



    @classmethod
    def is_media_class(cls, class_name :str) -> bool:
        """
        Return True if the given Class is a "Media" Class.
        A check is made if the plugin handling that semantic Class contain a default media folder.
        Currently, no check is made whether, in the database, the given Class node is an INSTANCE_OF the "Media" Class

        :param class_name:  Name of a Schema class
        :return:            True if the given Class is a "Media" Class
        """
        # Loop over all the registered plugin handlers
        for plugin_name, plugin_class in cls.REGISTERED_PLUGINS.items():
            if plugin_class.SCHEMA_CLASS_NAME == class_name:
                return hasattr(plugin_class, "DEFAULT_FOLDER_NAME")

        # TODO: ought to also query the Schema, to discover if the given Class
        #       is an INSTANCE_OF the "Media" class

        return False    # Didn't find any plugin handling this class.  TODO: maybe raise Exception



    @classmethod
    def api_handler(cls, plugin_id :str, parameters):
        """
        EXPERIMENTAL: not in current use.

        Invoke the api_endpoint() method of the appropriate plugin-handler class

        :param plugin_id:  This is the value stored in the database,
                                in the "handler" property of the `Class` nodes
                                EXAMPLES: "document", "header"
        :param parameters: Data that was passed to the web API endpoint to be handled by a specific plugin;
                                for example a dict or list, etc.
        :return:           Pass thru the return value of the api_endpoint() method
        """
        plugin_class = cls.get_plugin_python_class(plugin_id)  # EXAMPLE: The "Document" class

        return plugin_class.api_endpoint(parameters)    # EXAMPLE: call to method Documents.api_endpoint(parameters)



    @classmethod
    def move_media_item_successful(cls, internal_id :int|str, src :str, dest :str) -> None:
        """
        Invoked after a Media file gets moved to another location.

        It will get dispatched to the appropriate plugin, to manage plugin-specific elements
        such as thumbnails or document covers (if applicable)
        """
        # Retrieve the name of the semantic Class of the given Media Item
        semantic_class, _ = GraphSchema.get_class_and_entity_id(internal_id)    # EXAMPLE: "Document"

        print(f"Inside PluginManager.move_media_item_successful(): "
              f"attempting dispatching to plugin that handles the semantic Class `{semantic_class}`")

        plugin_name = cls.get_plugin_name_by_semantic_class(semantic_class)

        print(f"Inside PluginManager.move_media_item_successful(): "
              f"located a handler plugin named `{plugin_name}`")


        python_class = cls.get_plugin_python_class(plugin_name)             # EXAMPLE: The "Document" class

        try:
            python_class.move_media_item_successful(internal_id=internal_id, src=src, dest=dest)
        except AttributeError as ex:
            print(f"INFO: {ex}")    # AttributeError means that the plugin isn't providing this method,
                                    #   which is allowed by our convention.
                                    # Any other error will be passed to the calling function
