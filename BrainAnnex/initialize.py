from BrainAnnex.pages.BA_pages_request_handler import PagesRequestHandler
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.categories.categories import Collections
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from BrainAnnex.modules.media_manager.media_manager import MediaManager
from home.user_manager import UserManagerNeo4j



class InitializeBrainAnnex:
    """
    INITIALIZATION of various static classes
    """

    @classmethod
    def set_dbase(cls, db_handle):
        """
        Initialize various static classes that need the database object
        (to avoid multiple dbase connections)
        :param db_handle:
        :return:
        """
        PagesRequestHandler.db = db_handle
        APIRequestHandler.db = db_handle
        Categories.db = db_handle
        Collections.db = db_handle
        NeoSchema.db = db_handle
        UserManagerNeo4j.db = db_handle



    @classmethod
    def set_folders(cls, media_folder, log_folder):
        """
        Initialize various static classes that need folder locations from the
        configuration file
        (another approach, currently partially used, would be to pass them thru Flask's app.config)

        :param media_folder:
        :return:
        """
        APIRequestHandler.MEDIA_FOLDER = media_folder
        APIRequestHandler.LOG_FOLDER = log_folder

        MediaManager.MEDIA_FOLDER = media_folder
