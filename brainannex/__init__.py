__version__ = "5.0.0-beta.41"


from brainannex.neo_schema.neo_schema import NeoSchema
from brainannex.data_manager import DataManager
from brainannex.user_manager import UserManager
from brainannex.categories import Categories
from brainannex.collections import Collections


__all__ = [
    'NeoSchema',
    'DataManager',
    'UserManager',
    'Categories',
    'Collections',
    'version'
]


def version():
    return __version__
