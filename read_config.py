def load_config_data(config) -> dict:
    """
    Create and return a dictionary of all config data,
    upon reading in the config files.
    Attempt to import parameters from the default config file first, then from 'config.ini'
    (possibly overwriting some or all values from the default config file)

    :return:    A dictionary of all the config data.
                    EXAMPLE {"DB_COUNT": 2, "DB_DEFAULT_INDEX": 1, "DB_HOST_1": "bolt://localhost:7687", etc}
    """
    config_data = {}    # A dictionary of all the config data


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

    print("~~~~~~~~~~~  Start of config data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    ###  PART 1 : the database credentials  ###

    DB_COUNT = _extract_par("DB_COUNT", SETTINGS)
    try:
        config_data['DB_COUNT'] = int(DB_COUNT)
    except Exception:
        raise Exception(f"The passed configuration value for DB_COUNT ({DB_COUNT}) is not an integer as expected; "
                        f"this value is meant to be the number of databases whose credentials are provided in the config.ini file")

    DB_DEFAULT_INDEX = _extract_par("DB_DEFAULT_INDEX", SETTINGS)
    try:
        config_data['DB_DEFAULT_INDEX'] = int(DB_DEFAULT_INDEX)
    except Exception:
        raise Exception(f"The passed configuration value for DB_DEFAULT_INDEX ({DB_DEFAULT_INDEX}) is not an integer as expected; "
                        f"this value is meant to be the index of the database that is used at start time")


    for i in range(1, config_data["DB_COUNT"]+1):
        config_data[f"DB_HOST_{i}"] = _extract_par(f"DB_HOST_{i}", SETTINGS)
        config_data[f"DB_USERNAME_{i}"] = _extract_par(f"DB_USERNAME_{i}", SETTINGS)
        config_data[f"DB_PASSWORD_{i}"] = _extract_par(f"DB_PASSWORD_{i}", SETTINGS, display=False)
        config_data[f"DB_NICKNAME_{i}"] = _extract_par(f"DB_NICKNAME_{i}", SETTINGS)



    ###  PART 2 : deployment parameters  ###

    DEPLOYMENT = _extract_par("DEPLOYMENT", SETTINGS) # Should be either "FLASK" or "EXTERNAL"
                                                                #     use FLASK if starting the app with Flask
                                                                #     use EXTERNAL if starting the app with gunicorn (or other WSGI HTTP Server)

    assert DEPLOYMENT == "FLASK" or DEPLOYMENT == "EXTERNAL", \
        f"The passed configuration value for DEPLOYMENT (`{DEPLOYMENT}`) must be either 'FLASK' or 'EXTERNAL'"

    config_data['DEPLOYMENT'] = DEPLOYMENT

    # PORT_NUMBER is only used for FLASK runs
    if (DEPLOYMENT == "FLASK"):
        PORT_NUMBER = _extract_par("PORT_NUMBER", SETTINGS)      # The Flask default is 5000
        try:
            config_data['PORT_NUMBER'] = int(PORT_NUMBER)
        except Exception:
            raise Exception(f"The passed configuration value for PORT_NUMBER ({PORT_NUMBER}) is not an integer as expected")



    ###  PART 3 : folder locations  ###

    # TODO: add the final slash to all folders, if not already present
    config_data['MEDIA_FOLDER'] = _extract_par("MEDIA_FOLDER", SETTINGS)
    config_data['UPLOAD_FOLDER'] = _extract_par("UPLOAD_FOLDER", SETTINGS)    # A temporary folder for file uploads.  EXAMPLE: "/tmp/"
    config_data['LOG_FOLDER'] = _extract_par("LOG_FOLDER", SETTINGS)

    # Parameters for Continuous Data Ingestion
    config_data['INTAKE_FOLDER'] = _extract_par("INTAKE_FOLDER", SETTINGS)
    config_data['OUTTAKE_FOLDER'] = _extract_par("OUTTAKE_FOLDER", SETTINGS)



    ###  PART 4 : other parameters  ###

    # List of plugins to be used by the web app
    PLUGINS = _extract_par("PLUGINS", SETTINGS)

    try:
        # Split by commas and strip whitespace from each item
        config_data['PLUGINS'] = [item.strip() for item in PLUGINS.split(",")]
    except Exception:
        raise Exception(f"The passed configuration value for PLUGINS is not a series of comma-separated names as expected")


    index_pdf_files = _extract_par("INDEX_PDF_FILES", SETTINGS)

    if index_pdf_files.lower() == "true":
        config_data['INDEX_PDF_FILES'] = True
    elif index_pdf_files.lower() == "false":
        config_data['INDEX_PDF_FILES'] = False
    else:
        raise Exception(f"The only valid values for the "
                        f"configuration parameter `INDEX_PDF_FILES` are True or False ; the value you provided was: `{index_pdf_files}`")

    config_data['BRANDING'] = _extract_par("BRANDING", SETTINGS)

    print("~~~~~~~~~~~  End of config data ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    return config_data



def _extract_par(name :str, parser_dict, display=True) -> str:
    """
    Extract the parameter with the given name,
    from a "configparser" object containing the parameters and their values.
    If not found, an Exception is raised

    :param name:    Name of the config parameter of interest.  EXAMPLE: "PORT_NUMBER"
    :param parser_dict:Object of type "configparser.SectionProxy" ;
                        can be treated as a python dict
    :param display: Flag indicating whether to show the value of the parameter
                        in the printout; if False, "*********" will be shown instead of the value
    :return:        A string with the value of the requested parameter
                        (note: this will always be a string, even for parameter values such as 80 or True)
    """
    if name not in parser_dict:
        raise Exception(f"The `config.ini` configuration file needs a line providing a value for  {name} .  "
                        f"Example of configuration file: https://github.com/BrainAnnex/brain-annex/blob/main/config.defaults.ini")

    value = parser_dict[name]
    if display:
        print(f"{name}: {value}")
    else:
        print(f"{name}: *********")

    return value
