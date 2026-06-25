# Test of the ability to connect to the Graph database from the credentials
# in config file(s) variables

# IMPORTANT: this file is expected to be in the main folder (where the config files are stored)

import os
import read_config
from configparser import ConfigParser
from brainannex import GraphAccess


print("About to test the database connection, using the credentials STORED in the configuration file(s)...\n")

if os.environ.get("FLASK_APP"):     # Remote deployment
    print("This is a REMOTE deployment")
else:                               # Local deployment
    print("This is a LOCAL deployment")

print()


config = ConfigParser()

d = read_config.load_config_data(config)    # A dictionary of config parameter names and value

i = d.get("DB_DEFAULT_INDEX")   # The presence of this value gets enforced during the read of the config data


NEO4J_HOST = d.get(f"DB_HOST_{i}")
NEO4J_USER = d.get(f"DB_USERNAME_{i}")
NEO4J_PASSWORD = d.get(f"DB_PASSWORD_{i}")


if not NEO4J_HOST \
    or not NEO4J_USER \
       or not NEO4J_PASSWORD:
    print(f"To run a database-connectivity test, ALL of the following variables must be set in the config file(s): "
          f"DB_HOST_{i}, DB_USERNAME_{i}, DB_PASSWORD_{i} \n" 
          f"Test skipped")

else:
    # Attempt to connect to the graph database from credentials in the config file(s)
    print(f'\nAttempting to connect to HOST "{NEO4J_HOST}", USER "{NEO4J_USER}"...')
    db = GraphAccess(host=NEO4J_HOST,
                     credentials=(NEO4J_USER, NEO4J_PASSWORD),
                     debug=False, autoconnect=True)

    print("\nVersion of the Neo4j driver: ", db.driver_version())
    print("Version of the Neo4j server: ", db.server_version())

    db.test_dbase_connection()

    print("END of test")
