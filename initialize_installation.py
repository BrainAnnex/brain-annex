# If the database is empty, attempt to read in the Schema file "init/MINIMAL_SCHEMA_TO_IMPORT.json"
# Then prompt to create a new admin user.  The `User` Schema gets created if needed.
# At a future date, this script will probably be generalized to a broader initialization process,
# and the import of the Schema file will be replaced by calls to initialization functions of all
# the applicable modules and plugin.

# It will connect to the Neo4j database from the credentials
# in config file(s) variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD

# IMPORTANT: this file is expected to be in the main folder (where the config files are stored)

# NOTE: if running inside PyCharm, go to Run > Edit Configurations...
#       then select "initialize_installation" under Python (left pane), and check box "Emulate terminal in output console"


import os
import getpass
from configparser import ConfigParser
from brainannex import GraphAccess, GraphSchema, UserManager


print("\n--- INITIALIZING (if needed) the BrainAnnex web app, and creating a new admin user...\n")
print("Reading the credentials STORED in the configuration file(s)\n")


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
          f"the Schema is assumed to be present, and will NOT be imported\n")
else:
    print("\nThe database is empty; now importing/creating the Schema...")

    schema_datafile = "init/MINIMAL_SCHEMA_TO_IMPORT.json"
    try:
        with open(schema_datafile, 'r') as fh:
            file_contents = fh.read()
            #print(f"Contents of schema file to import:\n{file_contents}")
    except Exception:
        raise Exception(f"File I/O failure to read schema datafile `{schema_datafile}`.  Make sure the file is present.")

    print(f"The schema datafile `{schema_datafile}` was found and successfully read")
    try:
        details = db.import_json_dump(file_contents)    # THE ACTUAL IMPORT TAKES PLACE HERE
    except Exception as ex:
       raise Exception("Import of JSON schema data file `{schema_datafile}` failed: {ex}")

    print(f"The schema data was successfully imported into the database")


# Attempt to create the Schema for the `User` class.  If it already exists, no action will be taken
try:
    print("Attempt to create the Schema for the `User` class (if needed).......")
    UserManager.create_schema()
except Exception as ex:
    print(f"INFO: `User` Schema NOT created. ", ex)


print("\nTime to create a new admin user...\n")

print("Enter the desired username: ")
username = input()

password = getpass.getpass(f"Enter the desired password for user `{username}` (at least 8 characters): ")

print(f"Enter the email address for user `{username}` :")
email = input()


print(f"Attempting to create a new admin user `{username}` ...")
#print(f"password:" , password)

try:
    user_id = UserManager.create_user(username=username, password=password, email=email, admin=True)
    print(f"New admin user successfully created with username: `{username}`, and assigned user_id: {user_id} ")
except Exception as ex:
    print(f"**** ERROR: Unable to create new user. ", ex)


print("\nEND of initialization script")
