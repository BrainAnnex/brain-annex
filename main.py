"""
MAIN PROGRAM : it starts up a server for web User Interface and an API
    Run this file, and then set the browser to http://localhost:5000/some_url
    (the actual port number is configurable; the URL's are specified in the various modules)

IMPORTANT: first change the config.ini file as needed

Note: this main program may also be started from the CLI with the "flask run" command
"""

import os
from flask import Flask
from configparser import ConfigParser


### Import sub-modules making up this web app:

# The site's home/login/top-level pages
# (possibly under the control of a co-hosted independent site)
from home.home_routing import Home

# The navigation is shared by Brain Annex and possibly other independent sites
# embedded (co-hosted) with it
from navigation.navigation_routing import Navigation
from navigation.navigation import get_site_pages

from BrainAnnex.pages.BA_pages_routing import PagesRouting
from BrainAnnex.api.BA_api_routing import ApiRouting

# These are an example of an independent site embedded (co-hosted) with Brain Annex.
# Comment out if not needed!
from sample_embedded_site.sample_pages.sample_pages_routing import SamplePagesRouting
from sample_embedded_site.sample_api.sample_api_routing import SampleApiRouting

# The remaining imports, below, are for the database initialization
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.initialize import InitializeBrainAnnex



#################################################################################
#                                                                               #
#               IMPORT AND VALIDATE THE CONFIGURABLE PARAMETERS                 #
#                                                                               #
#################################################################################

def extract_par(name, d, display=True) -> str:
    if name not in d:
        raise Exception(f"The configuration file needs a line with a value for {name}")
    value = d[name]
    if display:
        print(f"{name}: {value}")
    else:
        print(f"{name}: *********")

    return value
#########################################

config = ConfigParser()

# Attempt to import parameters from the default config file first, then from 'config.ini'
# (possibly overwriting some or all values from the default config file)
found_files = config.read(['config.defaults.ini', 'config.ini'])
#print("found_files: ", found_files)    # This will be a list of the names of the files that were found

if found_files == []:
    raise Exception("No configurations files found!  Make sure to have a 'config.ini' file in the same folder as main.py")

if found_files == ['config.defaults.ini']:
    raise Exception("Only found a DEFAULT version of the config file ('config.defaults.ini'); make sure to duplicate it, name it 'config.ini' and personalize it")

if found_files == ['config.ini']:
    print("A local, personalized, version of the config file found ('config.ini'); all configuration will be based on this file")
else:
    print("Two config files found: settings in 'config.ini' will over-ride any counterpart in 'config.defaults.ini'")


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




#########################################
#        MAIN PROGRAM EXECUTION         #
#########################################

### INITIALIZATION of various static classes that need the database object
#   (to avoid multiple dbase connections)
APP_NEO4J_DBASE = neo_access.NeoAccess(host=NEO4J_HOST, credentials=(NEO4J_USER, NEO4J_PASSWORD))

InitializeBrainAnnex.set_dbase(APP_NEO4J_DBASE)
InitializeBrainAnnex.set_media_folder(MEDIA_FOLDER)

site_pages = get_site_pages()     # Data for the site navigation



###  FLASK-RELATED INITIALIZATION  ###

# Instantiate the Flask object used to provide a UI and an API
app = Flask(__name__)   # The Flask object (exposed so that this main program may also be started from the CLI
                        #                   with the "flask run" command)



### DEFINE THE HIGH-LEVEL ROUTING
#   Register the various "blueprints" (i.e. the various top-level modules that specify how to dispatch the URL's),
#   and specify the URL prefixes to use for the various modules
#   TODO: maybe all the various setup() methods could take an optional 2nd arg, a dict,
#         to pass module-specific data

# The site's home/top-level pages, incl. login
Home.setup(app)

# The navbar
Navigation.setup(app)

# The BrainAnnex-provided UI
PagesRouting.site_pages = site_pages
PagesRouting.setup(app)

# The BrainAnnex-provided endpoints
ApiRouting.MEDIA_FOLDER = MEDIA_FOLDER
ApiRouting.UPLOAD_FOLDER = UPLOAD_FOLDER
ApiRouting.setup(app)

# Examples of generic pages and API
SamplePagesRouting.setup(app)           # Example of UI for an embedded independent site
SampleApiRouting.setup(app)             # Example of endpoints for an embedded independent site



# DEFINE A TEMPORARY FOLDER FOR FILE UPLOADS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#app.config['UPLOAD_FOLDER'] = r'D:\tmp'
#APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#UPLOAD_FOLDER = os.path.join(APP_ROOT, 'api/static/')



# Configure the Jinja template engine embedded in Flask
app.jinja_env.lstrip_blocks = True     # Strip tabs and spaces from the beginning of a line to the start of a block
app.jinja_env.trim_blocks = True       # The first newline after a template tag is removed


### Set the secret key to some random bytes. Used to sign the cookies cryptographically
app.secret_key = b"pqE3_t(4!x"



###  Fire up the web app

if os.environ.get("FLASK_APP"):
    # Remote deployment.  The web app is started from the CLI,
    # with the command "flask run [OPTIONS]" , after setting:  export FLASK_APP=main.py
    print(f" * Remote deployment: SET BROWSER TO http://YOUR_IP_OR_DOMAIN:PORT_NUMBER_USED_IN_STARTING_UP")
else:
    # Local deployment.  The web app is started by running this main.py
    debug_mode = True
    print(f" * Local deployment: SET BROWSER TO http://localhost:{PORT_NUMBER}/BA/pages/admin")
    app.run(debug=debug_mode, port=PORT_NUMBER)     # CORE of UI : transfer control to the "Flask object"
    # This  will start a local WSGI server.  Threaded mode is enabled by default
