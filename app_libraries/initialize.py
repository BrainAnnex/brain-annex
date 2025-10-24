from brainannex import Categories, Collections, NeoSchema, UserManager, FullTextIndexing

from app_libraries.data_manager import DataManager
from app_libraries.media_manager import MediaManager
from app_libraries.node_explorer import NodeExplorer
import app_libraries.PLUGINS.plugin_support as plugin_support

from flask_modules.home.login_manager import FlaskUserManagement



class InitializeBrainAnnex:
    """
    INITIALIZATION of various static classes
    """

    @classmethod
    def set_dbase(cls, db_handle) -> None:
        """
        Initialize various static classes that need the "GraphAccess" database object
        (to avoid multiple dbase connections)

        :param db_handle:   Object of class "GraphAccess"
        :return:            None
        """
        DataManager.db = db_handle
        Categories.db = db_handle
        Collections.db = db_handle
        NeoSchema.db = db_handle
        FlaskUserManagement.db = db_handle
        NodeExplorer.db = db_handle
        FullTextIndexing.db = db_handle
        UserManager.db = db_handle



    @classmethod
    def set_folders(cls, media_folder :str, log_folder :str) -> None:
        """
        Initialize various static classes that need folder locations from the
        configuration file
        (another approach, currently partially used, would be to pass them thru Flask's app.config)

        :param media_folder:
        :param log_folder:
        :return:            None
        """
        DataManager.LOG_FOLDER = log_folder

        MediaManager.set_media_folder(media_folder)

        MediaManager.set_default_folders(plugin_support.all_default_folders())
