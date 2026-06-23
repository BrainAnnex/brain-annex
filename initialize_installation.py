# If the database is empty, attempt to read in the Schema file "init/MINIMAL_SCHEMA_TO_IMPORT.json"
# Then prompt to create a new admin user.  The `User` Schema gets created if needed.

# At a future date, this script will be generalized to a broader initialization process,
# and the import of the Schema file will be replaced by calls to initialization functions of all
# the applicable modules and desired plugins (this process will also set indexes/constraints)

# It will connect to the Neo4j database from the credentials
# in config file(s) variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD

# IMPORTANT: this file is expected to be in the main folder (where the config files are stored)

# NOTE: if running inside PyCharm, go to Run > Edit Configurations...
#       then select "initialize_installation" under Python (left pane), and check box "Emulate terminal in output console"


import os
import getpass
#import app_build
from configparser import ConfigParser
from brainannex import GraphAccess, GraphSchema, UserManager


print("\n--- Adding `User` Schema nodes (if needed) to the database, "
      "and creating a new admin user to log into the BrainAnnex web app...\n")
print("Reading the credentials STORED in the configuration file(s):\n")


###  IMPORT AND VALIDATE THE CONFIGURABLE PARAMETERS  ###

def _extract_par(name, d, display=True) -> str:
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


DB_COUNT = _extract_par("DB_COUNT", SETTINGS)
try:
    DB_COUNT = int(DB_COUNT)
except Exception:
    raise Exception(f"The passed configuration value for DB_COUNT ({DB_COUNT}) is not an integer as expected; "
                    f"this value is meant to be the number of databases whose credentials are provided in the config.ini file")

DB_DEFAULT = _extract_par("DB_DEFAULT", SETTINGS)
try:
    DB_DEFAULT = int(DB_DEFAULT)
except Exception:
    raise Exception(f"The passed configuration value for DB_DEFAULT ({DB_DEFAULT}) is not an integer as expected; "
                    f"this value is meant to be the index of the database that is used at start time")


i = DB_DEFAULT

NEO4J_HOST = _extract_par(f"DB_HOST_{i}", SETTINGS)
NEO4J_USER = _extract_par(f"DB_USERNAME_{i}", SETTINGS)
NEO4J_PASSWORD = _extract_par(f"DB_PASSWORD_{i}", SETTINGS, display=False)


MEDIA_FOLDER = _extract_par("MEDIA_FOLDER", SETTINGS)
UPLOAD_FOLDER = _extract_par("UPLOAD_FOLDER", SETTINGS)
PORT_NUMBER = _extract_par("PORT_NUMBER", SETTINGS)       # The Flask default is 5000

try:
    PORT_NUMBER = int(PORT_NUMBER)
except Exception:
    raise Exception(f"The passed value for PORT_NUMBER ({PORT_NUMBER}) is not an integer as expected")


# END OF CONFIGURATION IMPORT


if not NEO4J_HOST \
    or not NEO4J_USER \
       or not NEO4J_PASSWORD:
    raise Exception(f"To run this script, ALL of the following variables must be set in the config file(s): "
                    f"DB_HOST_{i}, DB_USERNAME_{i}, DB_PASSWORD_{i}")


# Attempt to connect to the Neo4j database from credentials in the config file(s)
print()
db = GraphAccess(host=NEO4J_HOST,
                 credentials=(NEO4J_USER, NEO4J_PASSWORD),
                 debug=False, autoconnect=True)

print("Version of the Neo4j driver: ", db.version())

print("\nThe stored credentials were successfully validated; now checking if data is already present in the database")

GraphSchema.set_database(db)
UserManager.set_database(db)



# Attempt to create the Schema for the `User` class.  If it already exists, no action will be taken
try:
    print("Attempt to create the Schema for the `User` class (if needed).......")
    UserManager.add_to_schema()
except Exception as ex:
    print(f"WARNING: `User` Schema missing, and it failed to get created. ", ex)



print("\nTime to create a new admin user...\n")

print("Enter the desired username: ")
username = input()

password = getpass.getpass(f"Enter the desired password for user `{username}` (at least 8 characters): ")

print(f"[OPTIONAL] Enter the email address for user `{username}` :")
email = input()


print(f"Attempting to create a new admin user `{username}` ...")
#print(f"password:" , password)

try:
    user_id = UserManager.create_user(username=username, password=password, email=email, admin=True)
    print(f"New admin user successfully created with username: `{username}`, and assigned user_id: {user_id} ")
except Exception as ex:
    print(f"**** ERROR: Unable to create new user. ", ex)


print("\nEND of installation initialization script\n")
