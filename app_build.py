from flask import Flask
from configparser import ConfigParser
from read_config import load_config_data


### Import sub-modules making up this web app:

# The site's home/login/top-level pages
# (possibly under the control of a co-hosted independent site)
from flask_modules.home.home_routing import HomeRouting

# The navigation is shared by Brain Annex and possibly other independent sites
# embedded (co-hosted) with it
from flask_modules.navigation.navigation_routing import Navigation

from flask_modules.pages.BA_pages_routing import PagesRouting
from flask_modules.api.BA_api_routing import ApiRouting

# These are an example of an independent site embedded (co-hosted) with Brain Annex.
# Comment out if not needed!
from flask_modules.sample_embedded_site.sample_pages.sample_pages_routing import SamplePagesRouting
from flask_modules.sample_embedded_site.sample_api.sample_api_routing import SampleApiRouting

# The remaining imports, below, are for the database initialization
from brainannex import GraphAccess
from app_libraries.initialize import InitializeBrainAnnex



def create_app(db=None, test=False, config_override=None) -> Flask:
    """
    Create and return the Flask object,
    upon reading in the config files (unless over-ridden)

    :param db:              [OPTIONAL] A "GraphAccess" database object (currently only used for pytests)
    :param test:            [OPTIONAL] If True, instead of reading the config files, use the values hardwired in this function
                                (default=False)
    :param config_override: [OPTIONAL] A dictionary for passing specific values for the config variables)
                                EXAMPLE: {'MEDIA_FOLDER': 'my_test/'}

    :return:                The instantiated Flask object
    """

    app = Flask(__name__)   # The Flask object


    #Save in the "app" object various global and module-specific data, to propagate to those modules
    if test:
        # For testing, set the configuration parameters manually below
        app.config['DB_COUNT'] = 1
        app.config['DB_DEFAULT_INDEX'] = 1

        app.config['DB_HOST_1'] = ""
        app.config['DB_USERNAME_1'] = ""
        app.config['DB_PASSWORD_1'] = ""
        app.config['DB_NICKNAME_1'] = ""

        app.config['DEPLOYMENT'] = "FLASK"
        app.config['PORT_NUMBER'] = 5000

        app.config['UPLOAD_FOLDER'] = ""
        app.config['MEDIA_FOLDER'] = ""
        app.config['LOG_FOLDER'] = ""
        app.config['INTAKE_FOLDER'] = ""
        app.config['OUTTAKE_FOLDER'] = ""

        app.config['PLUGINS'] = ""

        app.config['INDEX_PDF_FILES'] = True
        app.config['BRANDING'] = "Brain Annex"

    else:
        config = ConfigParser()
        d = load_config_data(config)    # IMPORT AND VALIDATE THE CONFIGURABLE PARAMETERS
        for k, v in d.items():
            app.config[k] = v           # Store all the values in app.config


    # If applicable, over-ride any configuration value that we have so far
    if config_override:
        app.config.update(config_override)

    #print(app.config)

    #initialize_graph_db(app)

    ### INITIALIZATION of various static classes that need the database object
    #   (to avoid multiple dbase connections)
    if db is not None:
        APP_GRAPH_DBASE = db    # Use the passed value
    else:
        db_index = app.config['DB_DEFAULT_INDEX']
        print("Attempting to connect to database ", app.config[f"DB_HOST_{db_index}"])

        APP_GRAPH_DBASE = GraphAccess(host=app.config[f"DB_HOST_{db_index}"],
                                      credentials=(app.config[f"DB_USERNAME_{db_index}"], app.config[f"DB_PASSWORD_{db_index}"]))

    app.config['DATABASE'] = APP_GRAPH_DBASE

    InitializeBrainAnnex.set_dbase(APP_GRAPH_DBASE)
    InitializeBrainAnnex.set_folders(app.config['MEDIA_FOLDER'], app.config['LOG_FOLDER'])

    #site_pages = get_site_pages()     # Data for the site navigation


    initialize_services(app)


    # Configure the Jinja template engine embedded in Flask
    app.jinja_env.lstrip_blocks = True     # Strip tabs and spaces from the beginning of a line to the start of a block
    app.jinja_env.trim_blocks = True       # The first newline after a template tag is removed


    ### Set the secret key to some random bytes. Used to sign the cookies cryptographically
    app.secret_key = b"pqE3_t(4!x"

    return app



def initialize_services(app :Flask) -> None:
    """
    Define the high-level routing.
    Register the various "blueprints" (i.e. the various top-level modules that specify how to dispatch the URL's),
    and specify the URL prefixes to use for the various modules

    :param app: An object of type "Flask"
    :return:    None
    """
    ###
    #   Note that all the classes used here are STATIC classes, that don't get initialized.
    #   ==> TODO: maybe merge with the initializations being done by the methods in InitializeBrainAnnex

    #register_routes(app)

    # The site's home (i.e. top-level) pages, incl. login
    HomeRouting.setup(app)

    # The navbar
    Navigation.setup(app)

    # The web app (UI for admin and Multimedia Content Management)
    PagesRouting.setup(app)

    # The web API endpoints
    ApiRouting.setup(app)

    # Examples of generic pages and web API
    SamplePagesRouting.setup(app)           # Example of UI for an embedded independent site
    SampleApiRouting.setup(app)             # Example of endpoints for an embedded independent site
