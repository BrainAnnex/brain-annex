# Test of the ability to connect to the Neo4j database from the credentials
# in config file(s) variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD

# IMPORTANT: this file is expected to be in a subfolder of the main folder (where the config files are stored);
#            if the location of this file gets changed, then the paths in the config.read() calls, below, may need changing


import os
from configparser import ConfigParser
from brainannex import GraphAccess

print("About to test the database connection, using the credentials STORED in the configuration file(s)...\n")



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
    found_files = config.read(['config.defaults.ini', 'config.ini'])     # For server
else:                               # Local deployment
    print("This is a LOCAL deployment")
    found_files = config.read(['config.defaults.ini', 'config.ini'])     # For local machine

#print("found_files: ", found_files)    # This will be a list of the names of the files that were found

if found_files == []:
    raise Exception("No configurations files found!  Make sure to have a 'config.ini' file in the same folder as main.py, "
                    "and to run this script from the tests_manual folder")

if found_files == ['config.defaults.ini']:
    raise Exception("Only found a DEFAULT version of the config file ('config.defaults.ini'); make sure to duplicate it, name it 'config.ini' and personalize it")

if found_files == ['config.ini']:
    print("A local, personalized, version of the config file found ('config.ini'); all configuration will be based on this file")
else:
    print("Two config files found: anything in 'config.ini' will over-ride any counterpart in 'config.defaults.ini'")


#print ("Sections found in config file(s): ", config.sections())

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
    print("To run this test, ALL of the following variables must be set in the config file(s): NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD.  "
          "Test skipped")

else:
    # Attempt to connect to the Neo4j database from credentials in the config file(s)
    obj = GraphAccess(host=NEO4J_HOST,
                      credentials=(NEO4J_USER, NEO4J_PASSWORD),
                      debug=False, autoconnect=True)

    print("Version of the Neo4j driver: ", obj.version())

    print("END of test")