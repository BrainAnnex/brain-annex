# Add to the database all the necessary Schema nodes and relationships

import os
from configparser import ConfigParser
from brainannex import GraphAccess, GraphSchema, Categories, UserManager, FullTextIndexing
import read_config

# TODO: automate the following imports based on the PLUGINS config setting
from app_libraries.PLUGINS.timer_widget import TimerWidget
from app_libraries.PLUGINS.site_link import SiteLink
from app_libraries.PLUGINS.header import Header
from app_libraries.PLUGINS.image import Image
from app_libraries.PLUGINS.document import Document
from app_libraries.PLUGINS.note import Note
from app_libraries.PLUGINS.recordset import Recordset
from app_libraries.PLUGINS.flash_card import FlashCard


print("\n--- INITIALIZING (as needed) the SCHEMA for the BrainAnnex web app - both for core modules "
      "and for plugins.  \n    A few nodes, as needed, will be added to the database, "
      "all with a `SCHEMA` or `Schema Autoincrement` label (except for the root `Category` node)...\n")


if os.environ.get("FLASK_APP"):     # Remote deployment
    print("This is a REMOTE deployment")
else:                               # Local deployment
    print("This is a LOCAL deployment")


print("\nReading the credentials STORED in the configuration file(s):\n")

config = ConfigParser()

d = read_config.load_config_data(config)    # A dictionary of config parameter names and value

i = d.get("DB_DEFAULT_INDEX")   # The presence of this value gets enforced during the read of the config data


NEO4J_HOST = d.get(f"DB_HOST_{i}")
NEO4J_USER = d.get(f"DB_USERNAME_{i}")
NEO4J_PASSWORD = d.get(f"DB_PASSWORD_{i}")


if not NEO4J_HOST \
    or not NEO4J_USER \
       or not NEO4J_PASSWORD:
    raise Exception(f"To run this script, ALL of the following variables must be set in the config file(s): "
                    f"DB_HOST_{i}, DB_USERNAME_{i}, DB_PASSWORD_{i} \n" 
                    f"No action taken")


# Attempt to connect to the Neo4j database from credentials in the config file(s)
print(f'\nAttempting to connect to HOST "{NEO4J_HOST}", USER "{NEO4J_USER}"...')
db = GraphAccess(host=NEO4J_HOST,
                 credentials=(NEO4J_USER, NEO4J_PASSWORD),
                 debug=False, autoconnect=True)

print("\nVersion of the Neo4j driver: ", db.driver_version())
print("Version of the Neo4j server: ", db.server_version())

db.test_dbase_connection()

print("\nThe stored credentials were successfully validated; now checking if SCHEMA data is already present in the database.")


GraphSchema.set_database(db)
UserManager.set_database(db)

number_nodes = db.count_nodes()

if number_nodes > 0:
    print(f"\nData already present in the database ({number_nodes} nodes found); "
          f"Schema will be added only as needed...")
else:
    print("\nThe database is empty; now creating the Schema...")



##########################################################################

def initialize_schema(db):
    """
    Create, as needed, the Schema for both the core modules
    and all the plugins.
    Also create root Category, if not already present.

    :param db:
    :return:
    """

    # Initialize core modules

    Categories.set_database(db)     # Also takes care of the class "Collections
    Categories.add_to_schema()      # Create, as needed, a new Schema Class node that represents "Categories"
    print("    Added (as needed) Schema for `Categories` core module")

    if Categories.get_root_entity_id() is None:
        # If no root Category was found
        try:
            Categories.create_categories_root()
            print("    Created a root Category")
        except Exception as ex:
            print(f"WARNING: Could not create root Category (perhaps it already exists?) ", ex)


    UserManager.set_database(db)
    UserManager.add_to_schema()
    print("    Added (as needed) Schema for `UserManager` core module")

    FullTextIndexing.set_database(db)
    FullTextIndexing.add_to_schema()
    print("    Added (as needed) Schema for `FullTextIndexing` core module")


    # Initialize plugins (TODO: automate, based on the PLUGINS config setting)
    try:
        TimerWidget.add_to_schema()
        print("    Added (as needed) Schema for `TimerWidget` plugin")
    except Exception as ex:
        print(f"WARNING: `TimerWidget` Schema could NOT be created. ", ex)

    try:
        Header.add_to_schema()
        print("    Added (as needed) Schema for `Header` plugin")
    except Exception as ex:
        print(f"WARNING: `Header` Schema could NOT be created. ", ex)

    try:
        SiteLink.add_to_schema()
        print("    Added (as needed) Schema for `SiteLink` plugin")
    except Exception as ex:
        print(f"WARNING: `SiteLink` Schema could NOT be created. ", ex)

    try:
        Image.add_to_schema()
        print("    Added (as needed) Schema for `Image` plugin")
    except Exception as ex:
        print(f"WARNING: `Image` Schema could NOT be created. ", ex)

    try:
        Document.add_to_schema()
        print("    Added (as needed) Schema for `Document` plugin")
    except Exception as ex:
        print(f"WARNING: `Document` Schema could NOT be created. ", ex)

    try:
        Note.add_to_schema()
        print("    Added (as needed) Schema for `Note` plugin")
    except Exception as ex:
        print(f"WARNING: `Note` Schema could NOT be created. ", ex)

    try:
        Recordset.add_to_schema()
        print("    Added (as needed) Schema for `Recordset` plugin")
    except Exception as ex:
        print(f"WARNING: `Recordset` Schema could NOT be created. ", ex)

    try:
        FlashCard.add_to_schema()
        print("    Added (as needed) Schema for `flash_card` plugin")
    except Exception as ex:
        print(f"WARNING: `flash_card` Schema could NOT be created. ", ex)



##########################################################################



print("\nSTART of database Schema initialization script...")

initialize_schema(db)

print("END of database Schema initialization script")

print("\n\nNote: to add USERS to log in into the web app, make sure to run:  python initialize_installation.py\n")
