from flask import Flask
from configparser import ConfigParser


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
    upon reading in the config files

    :param db:              Database object (currently only used for pytests)
    :param test:
    :param config_override: NOT CURRENTLY USED
    :return:                The instantiated Flask object
    """

    app = Flask(__name__)   # The Flask object




    #################################################################################
    #                                                                               #
    #               IMPORT AND VALIDATE THE CONFIGURABLE PARAMETERS                 #
    #                                                                               #
    #################################################################################

    #Save in the "app" object various global and module-specific data, to propagate to those modules
    if test:
        # For testing, set the configuration parameters manually below
        app.config['NEO4J_HOST'] = ""
        app.config['NEO4J_USER'] = ""
        app.config['NEO4J_PASSWORD'] = ""

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
        load_config(app)


    #if config_override:
        #app.config.update(config_override)


    #initialize_graph_db(app)

    ### INITIALIZATION of various static classes that need the database object
    #   (to avoid multiple dbase connections)
    if db is not None:
        APP_GRAPH_DBASE = db
    else:
        '''
        APP_GRAPH_DBASE = GraphAccess(host=app.config['NEO4J_HOST'],
                                      credentials=(app.config['NEO4J_USER'], app.config['NEO4J_PASSWORD']))
        '''

        db_index = app.config['DB_DEFAULT']
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



def load_config(app :Flask) -> None:
    """
    Attempt to import all the expected  parameters from the default config file first ('config.defaults.ini'),
    then from the user-customized file 'config.ini';
    in case of value conflict, 'config.ini', which takes priority.

    The loaded values are stored in the passed `app` object

    :param app: An object of type "Flask"
    :return:    None
    """
    #TODO: write a sub-routine that doesn't require the Flask app,
    #      and stores all the results in a dict  (for the benefit of initialize_installation.py, etc)
    config = ConfigParser()

    # Check whether the default and the custom config files are present
    found_files = config.read(['config.defaults.ini', 'config.ini'])
    #print("found_files: ", found_files)    # This will be a list of the names of the config files that were found

    if found_files == []:
        raise Exception("No configurations files found!  Make sure to have a 'config.ini' file in the same folder as main.py")

    if found_files == ['config.defaults.ini']:
        raise Exception("Only found a DEFAULT version of the config file ('config.defaults.ini'); "
                        "make sure to duplicate it, name the duplicate 'config.ini', and optionally customize it")

    if found_files == ['config.ini']:
        print("A local, customized, version of the config file found ('config.ini'); all configuration will be based on this file")
    else:
        print("Two config files found: settings in 'config.ini' (your customized file) will take priority, and over-ride any counterpart in 'config.defaults.ini'")


    #print("Sections found in config file(s): ", config.sections())    # EXAMPLE: ['SETTINGS']

    if "SETTINGS" not in config:
        raise Exception("Incorrectly set up configuration file - the following line should be present at the top: [SETTINGS]")


    # Extract all the values that were set in the configuration file(s)
    # NOTE: if both files were present, values in the latter ('config.ini')
    #       will override any same-named value in the former ('config.defaults.ini')

    SETTINGS = config['SETTINGS']
    #print(SETTINGS)                 # EXAMPLE:  <Section: SETTINGS>


    ###  PART 1 : the database credentials  ###

    DB_COUNT = _extract_par("DB_COUNT", SETTINGS)
    try:
        app.config['DB_COUNT'] = int(DB_COUNT)
    except Exception:
        raise Exception(f"The passed configuration value for DB_COUNT ({DB_COUNT}) is not an integer as expected; "
                        f"this value is meant to be the number of databases whose credentials are provided in the config.ini file")

    DB_DEFAULT = _extract_par("DB_DEFAULT", SETTINGS)
    try:
        app.config['DB_DEFAULT'] = int(DB_DEFAULT)
    except Exception:
        raise Exception(f"The passed configuration value for DB_DEFAULT ({DB_DEFAULT}) is not an integer as expected; "
                        f"this value is meant to be the index of the database that is used at start time")


    for i in range(1, app.config["DB_COUNT"]+1):
        app.config[f"DB_HOST_{i}"] = _extract_par(f"DB_HOST_{i}", SETTINGS)
        app.config[f"DB_USERNAME_{i}"] = _extract_par(f"DB_USERNAME_{i}", SETTINGS)
        app.config[f"DB_PASSWORD_{i}"] = _extract_par(f"DB_PASSWORD_{i}", SETTINGS, display=False)
        app.config[f"DB_NICKNAME_{i}"] = _extract_par(f"DB_NICKNAME_{i}", SETTINGS)




    ###  PART 2 : deployment parameters  ###

    DEPLOYMENT = _extract_par("DEPLOYMENT", SETTINGS)       # Should be either "FLASK" or "EXTERNAL"
                                                            #     use FLASK if starting the app with Flask
                                                            #     use EXTERNAL if starting the app with gunicorn (or other WSGI HTTP Server)

    assert DEPLOYMENT == "FLASK" or DEPLOYMENT == "EXTERNAL", \
        f"The passed configuration value for DEPLOYMENT (`{DEPLOYMENT}`) must be either 'FLASK' or 'EXTERNAL'"

    app.config['DEPLOYMENT'] = DEPLOYMENT

    # PORT_NUMBER is only used for FLASK runs
    if (DEPLOYMENT == "FLASK"):
        PORT_NUMBER = _extract_par("PORT_NUMBER", SETTINGS)      # The Flask default is 5000
        try:
            app.config['PORT_NUMBER'] = int(PORT_NUMBER)
        except Exception:
            raise Exception(f"The passed configuration value for PORT_NUMBER ({PORT_NUMBER}) is not an integer as expected")



    ###  PART 3 : folder locations  ###

    # TODO: add the final slash to all folders, if not already present
    app.config['MEDIA_FOLDER'] = _extract_par("MEDIA_FOLDER", SETTINGS)
    app.config['UPLOAD_FOLDER'] = _extract_par("UPLOAD_FOLDER", SETTINGS)    # A temporary folder for file uploads.  EXAMPLE: "/tmp/"
    app.config['LOG_FOLDER'] = _extract_par("LOG_FOLDER", SETTINGS)

    # Parameters for Continuous Data Ingestion
    app.config['INTAKE_FOLDER'] = _extract_par("INTAKE_FOLDER", SETTINGS)
    app.config['OUTTAKE_FOLDER'] = _extract_par("OUTTAKE_FOLDER", SETTINGS)



    ###  PART 4 : other parameters  ###

    # List of plugins to be used by the web app
    PLUGINS = _extract_par("PLUGINS", SETTINGS)

    try:
        # Split by commas and strip whitespace from each item
        app.config['PLUGINS'] = [item.strip() for item in PLUGINS.split(",")]
    except Exception:
        raise Exception(f"The passed configuration value for PLUGINS is not a series of comma-separated names as expected")


    index_pdf_files = _extract_par("INDEX_PDF_FILES", SETTINGS)

    if index_pdf_files.lower() == "true":
        app.config['INDEX_PDF_FILES'] = True
    elif index_pdf_files.lower() == "false":
        app.config['INDEX_PDF_FILES'] = False
    else:
        raise Exception(f"The only valid values for the "
                        f"configuration parameter `INDEX_PDF_FILES` are True or False ; the value you provided was: `{index_pdf_files}`")

    app.config['BRANDING'] = _extract_par("BRANDING", SETTINGS)



def _extract_par(name :str, d, display=True) -> str:
    """
    Extract the parameter with the given name,
    from a "configparser" object containing the parameters and their values.
    If not found, an Exception is raised

    :param name:    Name of the config parameter of interest.  EXAMPLE: "PORT_NUMBER"
    :param d:       Object of type "configparser.SectionProxy" ;
                        can be treated as a python dict
    :param display: Flag indicating whether to show the value of the parameter
                        in the printout; if False, "*********" will be shown instead of the value
    :return:        A string with the value of the requested parameter
                        (note: this will always be a string, even for parameter values such as 80 or True)
    """
    if name not in d:
        raise Exception(f"The `config.ini` configuration file needs a line providing a value for {name}. "
                        f"Example of configuration file: https://github.com/BrainAnnex/brain-annex/blob/main/config.defaults.ini")

    value = d[name]
    if display:
        print(f"{name}: {value}")
    else:
        print(f"{name}: *********")

    return value



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
