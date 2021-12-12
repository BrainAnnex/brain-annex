# MAIN PROGRAM : it starts up a server for web User Interface and an API
# Run this file, and then set the browser to http://localhost:5000/some_url
# (the actual URL is specified in the various modules.)
# Note: this main program may also be started from the CLI with the "flask run" command

from flask import Flask

# All the sub-modules making up this web app

# The navigation is shared by Brain Annex and possible other independent sites embedded (co-hosted) with it
from navigation.navigation_routing import navigation_flask_blueprint

from BrainAnnex.pages.BA_pages_routing import BA_pages_flask_blueprint
from BrainAnnex.api.BA_api_routing import BA_api_flask_blueprint

# These are an example of an independent site embedded (co-hosted) with Brain Annex.  Comment out if not needed!
from sample_embedded_site.sample_pages.sample_pages_routing import sample_pages_flask_blueprint
from sample_embedded_site.sample_api.sample_api_routing import sample_api_flask_blueprint



#########################################
###      MAIN PROGRAM EXECUTION       ###
#########################################


###  FLASK-RELATED INITIALIZATION  ###

# Instantiate the Flask object used to provide a UI and an API
app = Flask(__name__)   # The Flask object (exposed so that this main program may also be started from the CLI
                        #                   with the "flask run" command)


### DEFINE THE HIGH-LEVEL ROUTING
#   Register the various "blueprints" (i.e. the various top-level modules that specify how to dispatch the URL's),
#       and specify the URL prefixes to use for the various modules
app.register_blueprint(navigation_flask_blueprint, url_prefix = "/navigation")  # The navbar

app.register_blueprint(BA_pages_flask_blueprint, url_prefix = "/BA/pages")      # The BrainAnnex-derived UI
app.register_blueprint(BA_api_flask_blueprint, url_prefix = "/BA/api")          # The BrainAnnex-derived endpoint

app.register_blueprint(sample_pages_flask_blueprint, url_prefix = "/sample/pages") # Example of UI for an embedded independent site
app.register_blueprint(sample_api_flask_blueprint, url_prefix = "/sample/api")     # Example of endpoints for an embedded independent site


# DEFINE A TEMPORARY FOLDER FOR FILE UPLOADS
UPLOAD_FOLDER = "D:/tmp/"   # CHANGE AS NEEDED!
#print("UPLOAD_FOLDER: ", UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
print(" * SET BROWSER TO http://localhost:5000/some_url")
app.run(debug=debug_mode)       # CORE of UI : transfer control to the "Flask object"
                                        # This  will start a local WSGI server.  Threaded mode is enabled by default
                                        # To specify a different port, one could specify, for example: port=8080