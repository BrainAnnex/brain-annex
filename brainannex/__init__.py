__version__ = "5.0.0rc7_INTERIM_1"        # IN_PROGRESS towards rc7


# IMPORTANT: ONLY 1 of the following small group of InterGraph imports
#            should be uncommented,
#            depending on the graph database being used

#from brainannex.intergraph_neo4j_4.intergraph_neo4j_4 import InterGraph      # (Un)comment AS NEEDED!
from brainannex.intergraph_neo4j_5.intergraph_neo4j_5 import InterGraph     # (Un)comment AS NEEDED!

from brainannex.graphaccess import GraphAccess
from brainannex.cypher_utils import (CypherBuilder, CypherUtils)
from brainannex.graphschema import (GraphSchema, SchemaCache)
from brainannex.collections import Collections
from brainannex.categories import Categories
from brainannex.full_text_indexing import FullTextIndexing
from brainannex.user_manager import UserManager
from brainannex.py_graph_visual import PyGraphVisual


__all__ = [
    'InterGraph',
    'GraphAccess',
    'CypherBuilder',
    'CypherUtils',
    'GraphSchema',
    'SchemaCache',
    'Collections',
    'Categories',
    'FullTextIndexing',
    'UserManager',
    'PyGraphVisual',
    'version'
]


def version():
    return __version__
