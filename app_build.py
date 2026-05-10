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



def create_app(db=None, test=False, config_override=None):
    """
    Create and return the Flask object,
    upon reading in the config files

    :param db:
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
    if db is None:
        APP_NEO4J_DBASE = GraphAccess(host=app.config['NEO4J_HOST'],
                                      credentials=(app.config['NEO4J_USER'], app.config['NEO4J_PASSWORD']))
    else:
        APP_NEO4J_DBASE = db

    app.config['DATABASE'] = APP_NEO4J_DBASE


    #initialize_services(app)
    InitializeBrainAnnex.set_dbase(APP_NEO4J_DBASE)
    InitializeBrainAnnex.set_folders(app.config['MEDIA_FOLDER'], app.config['LOG_FOLDER'])

    #site_pages = get_site_pages()     # Data for the site navigation



    ### DEFINE THE HIGH-LEVEL ROUTING
    #   Register the various "blueprints" (i.e. the various top-level modules that specify how to dispatch the URL's),
    #   and specify the URL prefixes to use for the various modules
    #   Note that all the classes used here are STATIC classes, that don't get initialized.
    #   ==> TODO: maybe merge with the initializations being done by the methods in InitializeBrainAnnex

    #register_routes(app)

    # The site's home (i.e. top-level) pages, incl. login
    HomeRouting.setup(app)

    # The navbar
    Navigation.setup(app)

    # The BrainAnnex-provided web app (UI for admin and Multimedia Content Management)
    PagesRouting.setup(app)

    # The BrainAnnex-provided web API endpoints
    ApiRouting.setup(app)

    # Examples of generic pages and web API
    SamplePagesRouting.setup(app)           # Example of UI for an embedded independent site
    SampleApiRouting.setup(app)             # Example of endpoints for an embedded independent site



    # Configure the Jinja template engine embedded in Flask
    app.jinja_env.lstrip_blocks = True     # Strip tabs and spaces from the beginning of a line to the start of a block
    app.jinja_env.trim_blocks = True       # The first newline after a template tag is removed


    ### Set the secret key to some random bytes. Used to sign the cookies cryptographically
    app.secret_key = b"pqE3_t(4!x"

    return app



def load_config(app) -> None:
    """
    Attempt to import parameters from the default config file first ('config.defaults.ini'),
    then from the user-customized file 'config.ini',
    possibly overwriting some or all values from the default config file
    with those from 'config.ini', which takes priority.

    The loaded values are stored in the passed `app` object

    :return:    None
    """
    config = ConfigParser()

    # Check whether the default and and custom config files are present
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
        print("Two config files found: settings in 'config.ini' will take priority, and over-ride any counterpart in 'config.defaults.ini'")


    #print("Sections found in config file(s): ", config.sections())    # EXAMPLE: ['SETTINGS']

    if "SETTINGS" not in config:
        raise Exception("Incorrectly set up configuration file - the following line should be present at the top: [SETTINGS]")


    # Extract all the values that were set in the configuration file(s)
    # NOTE: if both files were present, values in the latter ('config.ini')
    #       will override any same-named value in the former ('config.defaults.ini')

    SETTINGS = config['SETTINGS']
    #print(SETTINGS)                 # EXAMPLE:  <Section: SETTINGS>

    app.config['NEO4J_HOST'] = _extract_par("NEO4J_HOST", SETTINGS)
    app.config['NEO4J_USER'] = _extract_par("NEO4J_USER", SETTINGS)
    app.config['NEO4J_PASSWORD'] = _extract_par("NEO4J_PASSWORD", SETTINGS, display=False)


    DEPLOYMENT = _extract_par("DEPLOYMENT", SETTINGS)        # Should be either "FLASK" or "EXTERNAL"
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



    # TODO: add the final slash to all folders, if not already present
    app.config['MEDIA_FOLDER'] = _extract_par("MEDIA_FOLDER", SETTINGS)
    app.config['UPLOAD_FOLDER'] = _extract_par("UPLOAD_FOLDER", SETTINGS)    # A temporary folder for file uploads.  EXAMPLE: "/tmp/"
    app.config['LOG_FOLDER'] = _extract_par("LOG_FOLDER", SETTINGS)

    # Parameters for Continuous Data Ingestion
    app.config['INTAKE_FOLDER'] = _extract_par("INTAKE_FOLDER", SETTINGS)
    app.config['OUTTAKE_FOLDER'] = _extract_par("OUTTAKE_FOLDER", SETTINGS)


    # List of plugins to be used by the web app
    app.config['PLUGINS'] = _extract_par("PLUGINS", SETTINGS)


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
                        in the printout
    :return:        A string with the value of the requested parameter
                        (note: this will always be a string, even for parameter values such as 80 or True)
    """
    if name not in d:
        raise Exception(f"The configuration file needs a line with a value for {name}")

    value = d[name]
    if display:
        print(f"{name}: {value}")
    else:
        print(f"{name}: *********")

    return value
