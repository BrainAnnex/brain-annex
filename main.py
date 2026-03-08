"""
MAIN PROGRAM : it starts up a server for web User Interface and an API
    Run this file, and then set the browser to http://localhost:5000/some_url
    (the actual port number is configurable; the URL's are specified in the various modules)

IMPORTANT: first change the config.ini file as needed

Note: this main program may also be started from the CLI with the "flask run" command
"""

from app_build import create_app



# The object for the Flask app (exposed, at the top level of this module,
#                   so that this main program may also be started from the CLI
#                   with the "flask run" command)
app = create_app()


###  Fire up the web app

#if os.environ.get("FLASK_APP"):
if app.config['DEPLOYMENT'] == "EXTERNAL":      # starting the app with gunicorn (or other WSGI HTTP Server)
    # The web app is started with commands such as:
    #           "gunicorn [OPTIONS] main:app"
    print(f" * EXTERNAL deployment: SET BROWSER TO http://YOUR_IP_OR_DOMAIN or https://YOUR_IP_OR_DOMAIN")
else:       # "FLASK" : starting the app with Flask
    # The web app is started by running this main.py
    #   - either by running main.py (for example from an IDE such as PyCharm)
    #   - or by starting flask from the CLI, with the command:
    #           "flask run [OPTIONS]" , after setting:  export FLASK_APP=main.py
    debug_mode = True       # At least for now, local deployment always enables Flask's debug mode
    PORT_NUMBER = app.config['PORT_NUMBER']
    print(f" * FLASK deployment: SET BROWSER TO http://localhost:{PORT_NUMBER}/BA/pages/admin")

    if __name__ == '__main__':  # Skip the next command if application is run from the Flask command line executable
        app.run(debug=debug_mode, port=PORT_NUMBER) # CORE of UI : transfer control to the "Flask object"
                                                    # This  will start a local WSGI server.  Threaded mode is enabled by default
