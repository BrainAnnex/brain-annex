# MAIN PROGRAM : it starts up a server for web User Interface and an API
# Run this file, and then set the browser to http://localhost:5000/some_url
# (the actual URL is specified in the various modules.)
# Note: this main program may also be started from the CLI with the "flask run" command

from flask import Flask

# All the sub-modules making up this web app

# The navigation is shared by Brain Annex and possible other independent sites embedded (co-hosted) with it
from navigation.navigation_routing import navigation_flask_blueprint

from BrainAnnex.pages.BA_pages_routing import PagesRouting
from BrainAnnex.api.BA_api_routing import BA_api_flask_blueprint

# These are an example of an independent site embedded (co-hosted) with Brain Annex.  Comment out if not needed!
from sample_embedded_site.sample_pages.sample_pages_routing import sample_pages_flask_blueprint
from sample_embedded_site.sample_api.sample_api_routing import sample_api_flask_blueprint

# The remaining imports, below, are for the database initialization
from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.pages.BA_pages_request_handler import PagesRequestHandler
from BrainAnnex.api.BA_api_request_handler import APIRequestHandler
from BrainAnnex.modules.categories.categories import Categories
from BrainAnnex.modules.categories.categories import Collections
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema



#########################################
#        MAIN PROGRAM EXECUTION         #
#########################################


# TODO: Maybe move all the initilization below into a separate module

# INITIALIZATION of various static classes that need the database object
# (to avoid multiple dbase connections)
APP_NEO4J_DBASE = neo_access.NeoAccess()

PagesRequestHandler.db = APP_NEO4J_DBASE
APIRequestHandler.db = APP_NEO4J_DBASE
Categories.db = APP_NEO4J_DBASE
Collections.db = APP_NEO4J_DBASE
NeoSchema.db = APP_NEO4J_DBASE



###  FLASK-RELATED INITIALIZATION  ###

# Instantiate the Flask object used to provide a UI and an API
app = Flask(__name__)   # The Flask object (exposed so that this main program may also be started from the CLI
                        #                   with the "flask run" command)



### DEFINE THE HIGH-LEVEL ROUTING
#   Register the various "blueprints" (i.e. the various top-level modules that specify how to dispatch the URL's),
#       and specify the URL prefixes to use for the various modules

# NOTE: 2 different approaches are currently in use -
#       with object instantiation (for BA_pages_flask_blueprint), and without (all other ones)
#       TODO: make all the same
app.register_blueprint(navigation_flask_blueprint, url_prefix = "/navigation")  # The navbar

#app.register_blueprint(BA_pages_flask_blueprint, url_prefix = "/BA/pages")      # The BrainAnnex-derived UI
obj = PagesRouting()
app.register_blueprint(obj.BA_pages_flask_blueprint, url_prefix = "/BA/pages")      # The BrainAnnex-derived UI

app.register_blueprint(BA_api_flask_blueprint, url_prefix = "/BA/api")          # The BrainAnnex-derived endpoint

app.register_blueprint(sample_pages_flask_blueprint, url_prefix = "/sample/pages") # Example of UI for an embedded independent site
app.register_blueprint(sample_api_flask_blueprint, url_prefix = "/sample/api")     # Example of endpoints for an embedded independent site


# DEFINE A TEMPORARY FOLDER FOR FILE UPLOADS
app.config['UPLOAD_FOLDER'] = "D:/tmp/"   # CHANGE AS NEEDED!

#app.config['UPLOAD_FOLDER'] = r'D:\tmp'
#APP_ROOT = os.path.dirname(os.path.abspath(__file__))
#UPLOAD_FOLDER = os.path.join(APP_ROOT, 'api/static/')




# Configure the Jinja template engine embedded in Flask
app.jinja_env.lstrip_blocks = True     # Strip tabs and spaces from the beginning of a line to the start of a block
app.jinja_env.trim_blocks = True       # The first newline after a template tag is removed


### Set the secret key to some random bytes. Used to sign the cookies cryptographically
app.secret_key = b"pqE3_t(4!x"



###  Fire up the web app.   IMPORTANT : COMMENT OUT ALL THE LINES BELOW DURING DEPLOYMENT, to start the webapp from the CLI
debug_mode=True
print(" * SET BROWSER TO http://localhost:5000/BA/pages/admin")
app.run(debug=debug_mode)       # CORE of UI : transfer control to the "Flask object"
                                # This  will start a local WSGI server.  Threaded mode is enabled by default
                                # To specify a different port, one could specify, for example: port=8080