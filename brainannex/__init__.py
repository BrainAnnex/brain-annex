__version__ = "5.0.0rc3"    # IN-PROGRESS


# IMPORTANT: ONY 1 of the following small group of InterGraph imports
#            should be uncommented,
#            depending on the graph database being used

#from brainannex.intergraph_neo4j_4.intergraph_neo4j_4 import InterGraph      # (Un)comment AS NEEDED!
from brainannex.intergraph_neo4j_5.intergraph_neo4j_5 import InterGraph     # (Un)comment AS NEEDED!

from brainannex.neoaccess import NeoAccess
from brainannex.cypher_utils import (NodeSpecs, CypherUtils, CypherMatch)
from brainannex.neoschema import (NeoSchema, SchemaCache)
from brainannex.collections import Collections
from brainannex.categories import Categories
from brainannex.full_text_indexing import FullTextIndexing
from brainannex.user_manager import UserManager
from brainannex.py_graph_visual import PyGraphVisual


__all__ = [
    'InterGraph',
    'NeoAccess',
    'NodeSpecs',
    'CypherUtils',
    'CypherMatch',
    'NeoSchema',
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
