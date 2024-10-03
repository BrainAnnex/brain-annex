__version__ = "5.0.0-beta.48.1"


from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.data_manager import DataManager
from brainannex.user_manager import UserManager
from brainannex.categories import Categories
from brainannex.collections import Collections
from brainannex.full_text_indexing import FullTextIndexing
import brainannex.PLUGINS.plugin_support as plugin_support


__all__ = [
    'NeoSchema',
    'DataManager',
    'UserManager',
    'Categories',
    'Collections',
    'FullTextIndexing',
    'plugin_support',
    'version'
]


def version():
    return __version__
