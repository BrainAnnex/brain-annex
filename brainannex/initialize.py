from brainannex.data_manager import DataManager
from brainannex.categories import Categories
from brainannex.collections import Collections
from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.media_manager import MediaManager
from brainannex.node_explorer import NodeExplorer
from brainannex.full_text_indexing import FullTextIndexing
from brainannex.user_manager import UserManager
from flask_modules.home.login_manager import FlaskUserManagement



class InitializeBrainAnnex:
    """
    INITIALIZATION of various static classes
    """

    @classmethod
    def set_dbase(cls, db_handle) -> None:
        """
        Initialize various static classes that need the "NeoAccess" database object
        (to avoid multiple dbase connections)

        :param db_handle:   Object of class "NeoAccess"
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
    def set_folders(cls, media_folder, log_folder) -> None:
        """
        Initialize various static classes that need folder locations from the
        configuration file
        (another approach, currently partially used, would be to pass them thru Flask's app.config)

        :param media_folder:
        :param log_folder:
        :return:            None
        """
        DataManager.LOG_FOLDER = log_folder

        MediaManager.MEDIA_FOLDER = media_folder
