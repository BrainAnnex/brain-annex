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
import read_config
from configparser import ConfigParser
from brainannex import GraphAccess, GraphSchema, UserManager



print("\n--- INITIALIZATION of USER: adding `User` Schema nodes (if needed) to the database, "
      "and creating a new admin user to log into the BrainAnnex web app...\n")


if os.environ.get("FLASK_APP"):     # Remote deployment
    print("This is a REMOTE deployment")
else:                               # Local deployment
    print("This is a LOCAL deployment")


print("\nReading the credentials STORED in the configuration file(s)\n")

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


# Attempt to connect to the the database from credentials in the config file(s)
print(f'\nAttempting to connect to HOST "{NEO4J_HOST}", USER "{NEO4J_USER}"...')
db = GraphAccess(host=NEO4J_HOST,
                 credentials=(NEO4J_USER, NEO4J_PASSWORD),
                 debug=False, autoconnect=True)

print("\nVersion of the Neo4j driver: ", db.driver_version())
print("Version of the Neo4j server: ", db.server_version())

db.test_dbase_connection()

print("\nThe stored credentials were successfully validated; now checking if data is already present in the database")


GraphSchema.set_database(db)
UserManager.set_database(db)

# Attempt to create the Schema for the `User` class.  If it already exists, no action will be taken
try:
    print("Attempting to create the Schema for the `User` class (if needed).......")
    UserManager.add_to_schema()
except Exception as ex:
    print(f"WARNING: `User` Schema missing, and it failed to get created. ", ex)



print("\nTime to create a new admin user.")
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
