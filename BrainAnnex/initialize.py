from BrainAnnex.pages.BA_pages_request_handler import PagesRequestHandler
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.categories.categories import Collections
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from home.user_manager import UserManagerNeo4j



class InitializeBrainAnnex:
    """
    INITIALIZATION of various static classes that need the database object
    (to avoid multiple dbase connections)
    """
    @classmethod
    def set_dbase(cls, db_handle):
        PagesRequestHandler.db = db_handle
        APIRequestHandler.db = db_handle
        Categories.db = db_handle
        Collections.db = db_handle
        NeoSchema.db = db_handle
        UserManagerNeo4j.db = db_handle



    @classmethod
    def set_media_folder(cls, media_folder):
        APIRequestHandler.MEDIA_FOLDER = media_folder
