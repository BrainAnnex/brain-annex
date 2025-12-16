
import os
from configparser import ConfigParser
from brainannex import GraphAccess, GraphSchema, Categories, UserManager, FullTextIndexing

from app_libraries.PLUGINS.timer import Timer
from app_libraries.PLUGINS.site_link import SiteLink
from app_libraries.PLUGINS.headers import Headers
from app_libraries.PLUGINS.images import Images
from app_libraries.PLUGINS.documents import Documents
from app_libraries.PLUGINS.notes import Notes
from app_libraries.PLUGINS.recordsets import Recordsets


print("\n--- INITIALIZING (as needed) the Schema for the BrainAnnex web app - both for core modules "
      "and for plugins.  A few nodes, as needed, will be added to the database, "
      "all with a `SCHEMA` or `Schema Autoincrement` label (except for the root `Category` node)...\n")

print("Reading the credentials STORED in the configuration file(s):\n")



###  IMPORT AND VALIDATE THE CONFIGURABLE PARAMETERS  ###

def extract_par(name, d, display=True) -> str:
    if name not in d:
        raise Exception(f"The configuration file needs a line with a value for {name}")
    value = d[name]
    if display:
        print(f"{name}: {value}")
    else:
        print(f"{name}: *********")

    return value
##############################################


config = ConfigParser()

# Attempt to import parameters from the default config file first, then from 'config.ini'
# (possibly overwriting some or all values from the default config file)

if os.environ.get("FLASK_APP"):     # Remote deployment
    print("This is a REMOTE deployment")
else:                               # Local deployment
    print("This is a LOCAL deployment")


found_files = config.read(['config.defaults.ini', 'config.ini'])
print(f"The following configuration files were found: {found_files}\n")    # This will be a list of the names of the files that were found

if found_files == []:
    raise Exception("No configurations files found!  Make sure to have a 'config.ini' file in the same folder as main.py")

if found_files == ['config.defaults.ini']:
    raise Exception("Only found a DEFAULT version of the config file ('config.defaults.ini'); make sure to duplicate it, name it 'config.ini' and personalize it")

if found_files == ['config.ini']:
    print("A local, personalized, version of the config file found ('config.ini'); all configuration will be based on this file")
else:
    print("Two config files found: anything in 'config.ini' will take priority, and over-ride any counterpart in 'config.defaults.ini'")


#print ("Sections found in config file(s): ", config.sections())

# Extract the various configurable settings from the config files

if "SETTINGS" not in config:
    raise Exception("Incorrectly set up configuration file - the following line should be present at the top: [SETTINGS]")

SETTINGS = config['SETTINGS']

NEO4J_HOST = extract_par("NEO4J_HOST", SETTINGS)
NEO4J_USER = extract_par("NEO4J_USER", SETTINGS)
NEO4J_PASSWORD = extract_par("NEO4J_PASSWORD", SETTINGS, display=False)
MEDIA_FOLDER = extract_par("MEDIA_FOLDER", SETTINGS)
UPLOAD_FOLDER = extract_par("UPLOAD_FOLDER", SETTINGS)
PORT_NUMBER = extract_par("PORT_NUMBER", SETTINGS)       # The Flask default is 5000

try:
    PORT_NUMBER = int(PORT_NUMBER)
except Exception:
    raise Exception(f"The passed value for PORT_NUMBER ({PORT_NUMBER}) is not an integer as expected")


# END OF CONFIGURATION IMPORT


if not NEO4J_HOST \
    or not NEO4J_USER \
       or not NEO4J_PASSWORD:
    raise Exception("To run this script, ALL of the following variables must be set in the config file(s): NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD")


# Attempt to connect to the Neo4j database from credentials in the config file(s)
print()
db = GraphAccess(host=NEO4J_HOST,
                 credentials=(NEO4J_USER, NEO4J_PASSWORD),
                 debug=False, autoconnect=True)

print("Version of the Neo4j driver: ", db.version())

print("\nThe stored credentials were successfully validated; now checking if data is already present in the database")

GraphSchema.set_database(db)
UserManager.set_database(db)

number_nodes = db.count_nodes()

if number_nodes > 0:
    print(f"\nData already present in the database ({number_nodes} nodes found); "
          f"Schema will be added as needed...\n")
else:
    print("\nThe database is empty; now importing/creating the Schema...")


##########################################################################

def initialize_schema(db):
    """
    Create, as needed, the Schema for both the core modules
    and all the plugins.
    Also create root Category.

    :param db:
    :return:
    """

    # Initialize core modules

    Categories.set_database(db)     # Also takes care of the class "Collections
    Categories.add_to_schema()      # Create, as needed, a new Schema Class node that represents "Categories"
    print("    Added Schema for `Categories` core module")

    try:
        Categories.create_categories_root()
        print("    Created a root Category")
    except Exception as ex:
        print(f"WARNING: Could not create root Category (perhaps it already exists?) ", ex)


    UserManager.set_database(db)
    UserManager.add_to_schema()
    print("    Added Schema for `UserManager` core module")

    FullTextIndexing.set_database(db)
    FullTextIndexing.add_to_schema()
    print("    Added Schema for `FullTextIndexing` core module")


    # Initialize plugins (TODO: perhaps allow to pick-and-choose what plugins to use)
    try:
        Timer.add_to_schema()
        print("    Added Schema for `TimerWidget` plugin")
    except Exception as ex:
        print(f"WARNING: `TimerWidget` Schema could NOT be created. ", ex)

    try:
        Headers.add_to_schema()
        print("    Added Schema for `Header` plugin")
    except Exception as ex:
        print(f"WARNING: `Header` Schema could NOT be created. ", ex)

    try:
        SiteLink.add_to_schema()
        print("    Added Schema for `SiteLinks` plugin")
    except Exception as ex:
        print(f"WARNING: `SiteLinks` Schema could NOT be created. ", ex)

    try:
        Images.add_to_schema()
        print("    Added Schema for `Images` plugin")
    except Exception as ex:
        print(f"WARNING: `Images` Schema could NOT be created. ", ex)

    try:
        Documents.add_to_schema()
        print("    Added Schema for `Documents` plugin")
    except Exception as ex:
        print(f"WARNING: `Documents` Schema could NOT be created. ", ex)

    try:
        Notes.add_to_schema()
        print("    Added Schema for `Notes` plugin")
    except Exception as ex:
        print(f"WARNING: `Notes` Schema could NOT be created. ", ex)

    try:
        Recordsets.add_to_schema()
        print("    Added Schema for `Recordsets` plugin")
    except Exception as ex:
        print(f"WARNING: `Recordsets` Schema could NOT be created. ", ex)


##########################################################################


initialize_schema(db)



print("\nEND of database Schema initialization script")

print("\n\nNote: to add users to log in into the web app, make sure to run:  python initialize_installation.py\n")
